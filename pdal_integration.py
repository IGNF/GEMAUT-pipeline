#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module pour l'intégration avec PDAL
Gère le calcul automatique du masque sol/sursol avec PDAL
Génère directement un masque binaire (0=sol, 1=sursol)
"""

import os
import time
import shutil
import numpy as np
import rasterio
from loguru import logger
from typing import Dict
import json
import subprocess

from ground_extraction_interface import GroundExtractionInterface


class PDALIntegration(GroundExtractionInterface):
    """Classe pour l'intégration avec PDAL"""
    
    def __init__(self):
        """Initialise l'intégration PDAL"""
        self.temp_files = []
    
    def compute_mask(self, mns_file: str, output_mask_file: str, 
                    work_dir: str, cpu_count: int,
                    params: Dict) -> None:
        """
        Calcule automatiquement le masque sol/sursol avec PDAL
        
        Args:
            mns_file: Chemin vers le fichier MNS
            output_mask_file: Chemin de sortie pour le masque
            work_dir: Répertoire de travail
            cpu_count: Nombre de CPUs à utiliser
            params: Paramètres PDAL (radius, tile, no_data_max, pente)
        """
        try:
            # Essayer d'abord la vraie pipeline PDAL
            if self._check_pdal_available():
                logger.info("PDAL détecté - utilisation de la vraie pipeline PDAL")
                self.compute_mask_with_pdal_pipeline(mns_file, output_mask_file, work_dir, params)
            else:
                logger.warning("PDAL non disponible - création d'un masque par défaut")
                self._create_default_mask(mns_file, output_mask_file)
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du masque PDAL: {e}")
            raise
    
    def _check_pdal_available(self) -> bool:
        """Vérifie si PDAL est disponible dans le système"""
        try:
            result = subprocess.run(['pdal', '--version'], 
                                  capture_output=True, text=True, check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def compute_mask_with_pdal_pipeline(self, mns_file: str, output_mask_file: str, work_dir: str, params: Dict) -> None:
        """
        Calcule le masque sol/sursol avec la vraie pipeline PDAL
        
        Args:
            mns_file: Fichier MNS d'entrée
            output_mask_file: Fichier de sortie du masque binaire
            params: Paramètres de configuration
        """
        logger.info("🚀 Démarrage de l'extraction avec la vraie pipeline PDAL")
        start_time = time.time()
        
        # Créer le répertoire de travail
        tmp_dir = os.path.join(work_dir, "tmp_pdal_pipeline")
        os.makedirs(tmp_dir, exist_ok=True)
        
        # Initialiser output_json pour éviter l'erreur dans finally
        output_json = os.path.join(work_dir, "pdal_pipeline_used.json")
        
        try:
            # Créer la pipeline PDAL adaptée
            pipeline = self._create_adapted_pipeline(mns_file, output_mask_file, params)
            
            # Écrire la pipeline dans un fichier JSON
            pipeline_file = os.path.join(tmp_dir, "pipeline.json")
            with open(pipeline_file, 'w') as f:
                json.dump(pipeline, f, indent=2)
            
            # Conserver le JSON de la pipeline pour inspection
            output_json = os.path.join(work_dir, "pdal_pipeline_used.json")
            shutil.copy2(pipeline_file, output_json)
            logger.info(f"📄 Pipeline JSON sauvegardé: {output_json}")
            
            # Exécuter la pipeline PDAL
            logger.info("⚡ Exécution de la pipeline PDAL...")
            cmd = ['pdal', 'pipeline', pipeline_file]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.stdout:
                logger.debug(f"Sortie PDAL: {result.stdout}")
            
            # Vérifier que le fichier de sortie existe
            if not os.path.exists(output_mask_file):
                raise FileNotFoundError(f"Fichier de sortie PDAL non trouvé: {output_mask_file}")
            
            # Créer un fichier temporaire pour le masque PDAL brut
            pdal_raw_mask = os.path.join(tmp_dir, "pdal_raw_mask.tif")
            shutil.move(output_mask_file, pdal_raw_mask)
            
            # Appliquer le resampling pour correspondre aux dimensions du MNS d'entrée
            logger.info("🔄 Application du resampling pour correspondre aux dimensions du MNS...")
            self.resample_mask_to_mns_dimensions(pdal_raw_mask, mns_file, output_mask_file)
            
            # Calculer la taille du fichier final
            file_size = os.path.getsize(output_mask_file) / (1024 * 1024)  # MB
            
            elapsed_time = time.time() - start_time
            logger.info(f"✅ PDAL: Extraction et resampling réussis en {elapsed_time:.2f}s")
            logger.info(f"📁 Fichier final créé: {output_mask_file} ({file_size:.2f} MB)")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erreur lors de l'exécution PDAL: {e}")
            if e.stderr:
                logger.error(f"Erreur stderr: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"❌ Erreur inattendue avec PDAL: {e}")
            raise
        finally:
            # Nettoyer les fichiers temporaires sauf le JSON
            for temp_file in os.listdir(tmp_dir):
                if temp_file != "pipeline.json":  # Garder le JSON
                    temp_path = os.path.join(tmp_dir, temp_file)
                    if os.path.isfile(temp_path):
                        os.remove(temp_path)
                        logger.debug(f"Fichier temporaire supprimé: {temp_path}")
            
            # Ajouter le JSON à la liste des fichiers à conserver
            self.temp_files.append(output_json)
    
    def _create_adapted_pipeline(self, mns_file: str, output_mask_file: str, params: Dict) -> Dict:
        """
        Crée une pipeline PDAL adaptée pour générer un masque binaire sol/sursol (0/1)
        Utilise le filtre CSF (Cloth Simulation Filter) pour l'extraction du sol
        puis convertit les valeurs en masque binaire propre
        
        Args:
            mns_file: Fichier MNS d'entrée
            output_mask_file: Fichier de sortie du masque binaire
            params: Paramètres de configuration
            
        Returns:
            Pipeline PDAL au format JSON
        """
        # Convertir en chemin absolu pour éviter les problèmes de répertoire de travail
        output_mask_file = os.path.abspath(output_mask_file)
        mns_file = os.path.abspath(mns_file)
        
        pipeline = {
            "pipeline": [
                # Lecture du fichier MNS
                {
                    "type": "readers.gdal",
                    "filename": mns_file,
                    "header": "Z"
                },
                # Création de l'attribut "Classification"
                {
                    "type": "filters.ferry",
                    "dimensions": "=>Classification"
                },
                # Filtrage du bruit / outlier / NODATA
                {
                    "type": "filters.elm"
                },
                # Filtrage des valeurs NODATA
                {
                    "type": "filters.range",
                    "limits": "Classification![7:7]"
                },
                # Filtrage des valeurs Z extrêmes
                {
                    "type": "filters.range",
                    "limits": f"Z[-{abs(params.get('no_data_max', -32768))}:]"
                },
                # Initialisation de la classification
                {
                    "type": "filters.assign",
                    "assignment": "Classification[:]=0"
                },
                # Application du filtre CSF pour l'extraction du sol
                {
                    "type": "filters.csf",
                    "resolution": 2.0,
                    "threshold": 0.8,
                    "hdiff": 0.2,
                    "step": 0.8,
                    "rigidness": 5,
                    "iterations": 500,
                    "smooth": True
                },
                # Conversion des points au sol (2) en 0
                {
                    "type": "filters.assign",
                    "assignment": "Classification[2:2]=0"
                },
                # Conversion des points sursol (1) en 1
                {
                    "type": "filters.assign",
                    "assignment": "Classification[1:1]=1"
                },
                # Export du masque binaire
                {
                    "type": "writers.gdal",
                    "filename": output_mask_file,
                    "resolution": "1",
                    "dimension": "Classification",
                    "output_type": "min",
                    "data_type": "uint8"
                }
            ]
        }
        return pipeline
    
    def _create_default_mask(self, mns_file: str, output_mask: str) -> None:
        """
        Crée un masque par défaut si PDAL échoue
        
        Args:
            mns_file: Fichier MNS de référence
            output_mask: Fichier de sortie du masque
        """
        logger.info("🔄 Création d'un masque par défaut...")
        
        with rasterio.open(mns_file) as src:
            data = src.read(1)
            # Masque binaire : 0 = sol (données valides), 1 = sursol (NoData)
            mask = (data == src.nodata) | (data == -9999)
            
            with rasterio.open(
                output_mask, 'w',
                driver='GTiff',
                height=src.height,
                width=src.width,
                count=1,
                dtype=np.uint8,
                crs=src.crs,
                transform=src.transform
            ) as dst:
                dst.write(mask.astype(np.uint8), 1)
                dst.nodata = 255
        
        logger.info("✅ Masque par défaut créé")
    
    def cleanup(self):
        """Nettoie les fichiers temporaires"""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.debug(f"Fichier temporaire supprimé: {temp_file}")
                except Exception as e:
                    logger.warning(f"Impossible de supprimer {temp_file}: {e}")
        self.temp_files.clear()
    
    def validate_installation(self) -> bool:
        """Vérifie si PDAL est correctement installé"""
        try:
            result = subprocess.run(['pdal', '--version'],
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                logger.info("PDAL détecté et fonctionnel")
                return True
            else:
                logger.warning("PDAL non disponible")
                return False
        except FileNotFoundError:
            logger.warning("PDAL non installé")
            return False
    
    def get_version(self) -> str:
        """Obtient la version de PDAL installée"""
        try:
            result = subprocess.run(['pdal', '--version'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except Exception:
            return "PDAL non disponible"
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Vérifie les dépendances PDAL nécessaires"""
        dependencies = {
            'pdal': False,
            'gdal': False,
            'rasterio': False
        }
        
        # Vérifier PDAL
        try:
            result = subprocess.run(['pdal', '--version'], 
                                  capture_output=True, text=True, check=False)
            dependencies['pdal'] = result.returncode == 0
        except FileNotFoundError:
            pass
        
        # Vérifier GDAL
        try:
            result = subprocess.run(['gdalinfo', '--version'], 
                                  capture_output=True, text=True, check=False)
            dependencies['gdal'] = result.returncode == 0
        except FileNotFoundError:
            pass
        
        # Vérifier rasterio
        try:
            import rasterio
            dependencies['rasterio'] = True
        except ImportError:
            pass
        
        return dependencies
    
    def log_environment(self) -> None:
        """Enregistre les informations sur l'environnement PDAL"""
        logger.info("=== Informations environnement PDAL ===")
        
        # Version PDAL
        pdal_version = self.get_version()
        logger.info(f"PDAL version: {pdal_version}")
        
        # Dépendances
        dependencies = self.check_dependencies()
        logger.info("Dépendances PDAL:")
        for dep, available in dependencies.items():
            status = "✓" if available else "✗"
            logger.info(f"  {status} {dep}")
        
        logger.info("=======================================")
    
    def get_required_params(self) -> list:
        """Retourne la liste des paramètres requis pour PDAL"""
        return ['radius', 'tile', 'no_data_max', 'pente'] 

    def resample_mask_to_mns_dimensions(self, pdal_mask_file: str, mns_file: str, output_file: str) -> None:
        """
        Sur-échantillonne le masque PDAL pour qu'il corresponde aux dimensions du MNS d'entrée
        
        Args:
            pdal_mask_file: Chemin vers le masque PDAL (résolution 1m)
            mns_file: Chemin vers le MNS d'entrée (référence pour les dimensions)
            output_file: Chemin de sortie pour le masque resamplé
        """
        logger.info("🔄 Sur-échantillonnage du masque PDAL aux dimensions du MNS...")
        
        try:
            # Lire le MNS d'entrée pour récupérer les métadonnées
            with rasterio.open(mns_file) as mns_src:
                mns_width = mns_src.width
                mns_height = mns_src.height
                mns_crs = mns_src.crs
                mns_transform = mns_src.transform
                mns_resolution_x = mns_src.res[0]
                mns_resolution_y = mns_src.res[1]
                
                logger.info(f"📐 MNS d'entrée: {mns_width}x{mns_height} pixels")
                logger.info(f"📍 Résolution MNS: {mns_resolution_x:.3f}m x {mns_resolution_y:.3f}m")
            
            # Lire le masque PDAL
            with rasterio.open(pdal_mask_file) as mask_src:
                mask_width = mask_src.width
                mask_height = mask_src.height
                mask_data = mask_src.read(1)  # Lire la bande Classification
                mask_crs = mask_src.crs
                mask_transform = mask_src.transform
                
                logger.info(f"📐 Masque PDAL: {mask_width}x{mask_height} pixels")
                logger.info(f"📍 Résolution masque: {mask_src.res[0]:.3f}m x {mask_src.res[1]:.3f}m")
            
            # Vérifier que les CRS sont compatibles
            if mns_crs != mask_crs:
                logger.warning(f"⚠️ CRS différents: MNS={mns_crs}, Masque={mask_crs}")
                logger.info("🔄 Reprojection du masque vers le CRS du MNS...")
                
                # Reprojeter le masque vers le CRS du MNS
                from rasterio.warp import reproject, Resampling
                
                # Créer un tableau temporaire pour la reprojection
                reprojected_mask = np.empty((mns_height, mns_width), dtype=np.uint8)
                
                reproject(
                    source=mask_data,
                    destination=reprojected_mask,
                    src_transform=mask_transform,
                    src_crs=mask_crs,
                    dst_transform=mns_transform,
                    dst_crs=mns_crs,
                    resampling=Resampling.nearest,  # Nearest neighbor pour préserver les valeurs binaires
                    dst_width=mns_width,
                    dst_height=mns_height
                )
                
                mask_data = reprojected_mask
                logger.info("✅ Reprojection terminée")
            
            # Si les dimensions sont déjà identiques, pas besoin de resampling
            if mns_width == mask_width and mns_height == mask_height:
                logger.info("✅ Les dimensions sont déjà identiques, pas de resampling nécessaire")
                mask_data_resampled = mask_data
            else:
                logger.info("🔄 Resampling du masque aux dimensions du MNS...")
                
                # Utiliser scipy pour le resampling avec interpolation nearest neighbor
                from scipy.ndimage import zoom
                
                # Calculer les facteurs de zoom
                zoom_x = mns_width / mask_width
                zoom_y = mns_height / mask_height
                
                logger.info(f"🔍 Facteurs de zoom: X={zoom_x:.3f}, Y={zoom_y:.3f}")
                
                # Resampling avec interpolation nearest neighbor pour préserver les valeurs binaires
                mask_data_resampled = zoom(mask_data, (zoom_y, zoom_x), order=0, mode='nearest')
                
                # Vérifier que les dimensions correspondent
                if mask_data_resampled.shape != (mns_height, mns_width):
                    logger.warning(f"⚠️ Dimensions après resampling: {mask_data_resampled.shape}")
                    # Ajuster si nécessaire
                    if mask_data_resampled.shape[0] > mns_height:
                        mask_data_resampled = mask_data_resampled[:mns_height, :]
                    if mask_data_resampled.shape[1] > mns_width:
                        mask_data_resampled = mask_data_resampled[:, :mns_width]
                    if mask_data_resampled.shape[0] < mns_height:
                        # Padding avec des zéros (sol)
                        padding_y = mns_height - mask_data_resampled.shape[0]
                        mask_data_resampled = np.pad(mask_data_resampled, ((0, padding_y), (0, 0)), mode='constant', constant_values=0)
                    if mask_data_resampled.shape[1] < mns_width:
                        # Padding avec des zéros (sol)
                        padding_x = mns_width - mask_data_resampled.shape[1]
                        mask_data_resampled = np.pad(mask_data_resampled, ((0, 0), (0, padding_x)), mode='constant', constant_values=0)
                
                logger.info(f"✅ Resampling terminé: {mask_data_resampled.shape}")
            
            # Écrire le masque resamplé
            with rasterio.open(
                output_file, 'w',
                driver='GTiff',
                height=mns_height,
                width=mns_width,
                count=1,
                dtype=np.uint8,
                crs=mns_crs,
                transform=mns_transform,
                nodata=255
            ) as dst:
                dst.write(mask_data_resampled.astype(np.uint8), 1)
            
            # Vérifier le résultat
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
            logger.info(f"✅ Masque resamplé créé: {output_file} ({file_size:.2f} MB)")
            logger.info(f"📐 Dimensions finales: {mns_width}x{mns_height} pixels")
            
            # Statistiques du masque
            unique_values, counts = np.unique(mask_data_resampled, return_counts=True)
            total_pixels = mns_width * mns_height
            logger.info("📊 Statistiques du masque resamplé:")
            for val, count in zip(unique_values, counts):
                percentage = (count / total_pixels) * 100
                label = "Sol" if val == 0 else "Sursol" if val == 1 else f"Valeur {val}"
                logger.info(f"  {label}: {count:,} pixels ({percentage:.1f}%)")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du resampling du masque: {e}")
            raise
