#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module pour le calcul automatique de masques sol/sursol
Supporte SAGA et PDAL comme méthodes d'extraction
"""

import os
import sys
import time
import subprocess
import json
import tempfile
from loguru import logger
from typing import Dict, Optional, Tuple

# Import des modules d'intégration existants
try:
    from saga_integration import SAGAIntegration
    SAGA_AVAILABLE = True
except ImportError:
    SAGA_AVAILABLE = False
    logger.warning("Module SAGA non disponible")

# Vérifier si PDAL est disponible dans le système
try:
    result = subprocess.run(['pdal', '--version'], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        PDAL_AVAILABLE = True
        logger.info(f"✅ PDAL disponible: {result.stdout.strip()}")
    else:
        PDAL_AVAILABLE = False
        logger.warning("⚠️ PDAL détecté mais non fonctionnel")
except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
    PDAL_AVAILABLE = False
    logger.warning("⚠️ PDAL non disponible dans le système")


class MaskComputer:
    """Classe pour le calcul automatique de masques avec différentes méthodes"""
    
    def __init__(self):
        """Initialise le calculateur de masques"""
        self.available_methods = self._check_available_methods()
        logger.info(f"Méthodes disponibles: {', '.join(self.available_methods)}")
    
    def _check_available_methods(self) -> list:
        """Vérifie quelles méthodes sont disponibles"""
        methods = []
        
        if SAGA_AVAILABLE:
            try:
                saga_instance = SAGAIntegration()
                if saga_instance.validate_saga_installation():
                    methods.append('saga')
                    logger.info("✅ SAGA disponible et fonctionnel")
                else:
                    logger.warning("⚠️ SAGA détecté mais non fonctionnel")
            except Exception as e:
                logger.warning(f"⚠️ SAGA non fonctionnel: {e}")
        else:
            logger.warning("⚠️ Module SAGA non disponible")
        
        if PDAL_AVAILABLE:
            try:
                # PDAL_AVAILABLE is now handled directly, so we can just add 'pdal'
                methods.append('pdal')
                logger.info("✅ PDAL disponible et fonctionnel")
            except Exception as e:
                logger.warning(f"⚠️ PDAL non fonctionnel: {e}")
        else:
            logger.warning("⚠️ Module PDAL non disponible")
        
        if not methods:
            logger.error("❌ Aucune méthode d'extraction disponible!")
            logger.error("Veuillez installer SAGA ou PDAL pour continuer")
        
        return methods
    
    def compute_mask(self, mns_file: str, output_mask_file: str, 
                    work_dir: str, method: str = 'saga',
                    cpu_count: int = 4, params: Optional[Dict] = None) -> str:
        """
        Calcule un masque sol/sursol avec la méthode spécifiée
        
        Args:
            mns_file: Fichier MNS d'entrée
            output_mask_file: Fichier de sortie du masque
            work_dir: Répertoire de travail
            method: Méthode à utiliser ('saga' ou 'pdal')
            cpu_count: Nombre de CPUs à utiliser
            params: Paramètres spécifiques à la méthode
            
        Returns:
            Chemin vers le fichier masque généré
        """
        # Validation des entrées
        if not os.path.exists(mns_file):
            raise FileNotFoundError(f"Fichier MNS non trouvé: {mns_file}")
        
        if not self.available_methods:
            raise RuntimeError("Aucune méthode d'extraction disponible")
        
        # Validation de la méthode
        if method not in self.available_methods:
            raise ValueError(f"Méthode '{method}' non disponible. Méthodes disponibles: {', '.join(self.available_methods)}")
        
        # Paramètres par défaut si non fournis
        if params is None:
            params = self._get_default_params(method)
        
        logger.info(f"🚀 Calcul du masque avec {method.upper()}")
        logger.info(f"📁 MNS: {mns_file}")
        logger.info(f"📁 Sortie: {output_mask_file}")
        logger.info(f"⚙️ Paramètres: {params}")
        
        start_time = time.time()
        
        try:
            if method == 'saga':
                mask_file = self._compute_with_saga(mns_file, output_mask_file, work_dir, cpu_count, params)
            elif method == 'pdal':
                mask_file = self._compute_with_pdal(mns_file, output_mask_file, work_dir, cpu_count, params)
            else:
                raise ValueError(f"Méthode non supportée: {method}")
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Masque calculé avec succès en {execution_time:.2f}s")
            logger.info(f"📁 Fichier généré: {mask_file}")
            
            return mask_file
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du calcul du masque avec {method}: {e}")
            raise
    
    def _get_default_params(self, method: str) -> Dict:
        """Retourne les paramètres par défaut pour la méthode spécifiée"""
        if method == 'saga':
            return {
                'radius': 100.0,      # Rayon de 100 (paramètre GEMAUT)
                'tile': 100,          # Dalles de 100x100 (paramètre GEMAUT)
                'no_data_max': -32768, # NoData externe GEMAUT
                'pente': 15.0         # Pente de 15° (paramètre GEMAUT)
            }
        elif method == 'pdal':
            return {
                'radius': 100.0,      # Rayon de 100 (paramètre GEMAUT)
                'tile': 100,          # Dalles de 100x100 (paramètre GEMAUT)
                'no_data_max': -32768, # NoData externe GEMAUT
                'pente': 15.0,        # Pente de 15° (paramètre GEMAUT)
                
                # Paramètres CSF configurables pour améliorer la détection
                'csf_max_iterations': 500,      # 500
                'csf_class_threshold': 0.8,    # 0.8
                'csf_cell_size': 2.0,               # 2.0
                'csf_time_step': 0.8,               # 0.8
                'csf_rigidness': 5,               # 5
                'csf_hdiff': 0.2,                       # 0.2
                'csf_smooth': True,                     # True
            }
        else:
            raise ValueError(f"Méthode non supportée: {method}")
    
    def _compute_with_saga(self, mns_file: str, output_mask_file: str, 
                          work_dir: str, cpu_count: int, params: Dict) -> str:
        """Calcule le masque avec SAGA"""
        logger.info("🔧 Utilisation de SAGA pour l'extraction...")
        
        saga_instance = SAGAIntegration()
        
        # Créer le répertoire de sortie si nécessaire
        os.makedirs(os.path.dirname(output_mask_file), exist_ok=True)
        
        # Calculer le masque
        saga_instance.compute_mask(
            mns_file=mns_file,
            output_mask_file=output_mask_file,
            work_dir=work_dir,
            cpu_count=cpu_count,
            params=params
        )
        

        
        return output_mask_file
    
    def _compute_with_pdal(self, mns_file: str, output_mask_file: str, 
                          work_dir: str, cpu_count: int, params: Dict) -> str:
        """Calcule le masque avec PDAL en utilisant l'algorithme CSF"""
        logger.info("🔧 Utilisation de PDAL pour l'extraction...")
        
        # Créer le répertoire de sortie si nécessaire
        os.makedirs(os.path.dirname(output_mask_file), exist_ok=True)
        
        try:
            # Étape 1: Convertir le raster en nuage de points
            points_file = os.path.join(work_dir, "mns_points.laz")
            self._raster_to_points_pdal(mns_file, points_file)
            
            # Étape 2: Appliquer l'algorithme CSF
            classified_file = os.path.join(work_dir, "classified_points.laz")
            self._apply_csf_pdal(points_file, classified_file, params)
            
            # Étape 3: Filtrer les points de sol
            ground_file = os.path.join(work_dir, "ground_points.laz")
            self._filter_ground_points_pdal(classified_file, ground_file)
            
            # Étape 4: Convertir en raster masque
            mask_file = self._points_to_raster_pdal(ground_file, mns_file, output_mask_file, work_dir)
            
            # Nettoyage des fichiers temporaires
            temp_files = [points_file, classified_file, ground_file]
            self._cleanup_temp_files_pdal(temp_files)
            
            logger.info(f"✅ Masque PDAL généré avec succès: {mask_file}")
            return mask_file
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du calcul du masque PDAL: {e}")
            # Nettoyage en cas d'erreur
            temp_files = [points_file, classified_file, ground_file]
            self._cleanup_temp_files_pdal(temp_files)
            raise
    
    def _raster_to_points_pdal(self, raster_file: str, output_file: str):
        """Convertit un raster en nuage de points avec PDAL"""
        logger.info("🔄 Conversion raster → nuage de points...")
        
        # Pipeline PDAL pour convertir raster en points
        pipeline = {
            "pipeline": [
                {
                    "type": "readers.gdal",
                    "filename": raster_file
                },
                {
                    "type": "filters.chipper",
                    "capacity": 1000
                },
                {
                    "type": "writers.las",
                    "filename": output_file,
                    "compression": "laszip"
                }
            ]
        }
        
        pipeline_file = os.path.join(os.path.dirname(output_file), "raster_to_points.json")
        with open(pipeline_file, 'w') as f:
            json.dump(pipeline, f, indent=2)
        
        # Exécuter le pipeline
        cmd = ['pdal', 'pipeline', pipeline_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"Erreur PDAL raster→points: {result.stderr}")
        
        # Nettoyer le fichier pipeline temporaire
        os.remove(pipeline_file)
    
    def _apply_csf_pdal(self, points_file: str, output_file: str, params: Dict):
        """Applique l'algorithme CSF pour classifier les points"""
        logger.info("🔍 Application de l'algorithme CSF...")
        
        # Pipeline PDAL avec CSF
        pipeline = {
            "pipeline": [
                {
                    "type": "readers.las",
                    "filename": points_file
                },
                {
                    "type": "filters.csf",
                    "max_iterations": params.get('csf_max_iterations', 500),
                    "class_threshold": params.get('csf_class_threshold', 0.8),
                    "cell_size": params.get('csf_cell_size', 2.0),
                    "time_step": params.get('csf_time_step', 0.8),
                    "rigidness": params.get('csf_rigidness', 5),
                    "h_diff": params.get('csf_hdiff', 0.2),
                    "smooth": params.get('csf_smooth', True)
                },
                {
                    "type": "writers.las",
                    "filename": output_file,
                    "compression": "laszip"
                }
            ]
        }
        
        pipeline_file = os.path.join(os.path.dirname(output_file), "csf_pipeline.json")
        with open(pipeline_file, 'w') as f:
            json.dump(pipeline, f, indent=2)
        
        # Exécuter le pipeline
        cmd = ['pdal', 'pipeline', pipeline_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            raise RuntimeError(f"Erreur PDAL CSF: {result.stderr}")
        
        # Nettoyer le fichier pipeline temporaire
        os.remove(pipeline_file)
    
    def _filter_ground_points_pdal(self, classified_file: str, output_file: str):
        """Filtre les points classifiés comme sol"""
        logger.info("🔍 Filtrage des points de sol...")
        
        # Pipeline PDAL pour filtrer les points de sol (classe 2)
        pipeline = {
            "pipeline": [
                {
                    "type": "readers.las",
                    "filename": classified_file
                },
                {
                    "type": "filters.range",
                    "limits": "Classification[2:2]"
                },
                {
                    "type": "writers.las",
                    "filename": output_file,
                    "compression": "laszip"
                }
            ]
        }
        
        pipeline_file = os.path.join(os.path.dirname(output_file), "filter_pipeline.json")
        with open(pipeline_file, 'w') as f:
            json.dump(pipeline, f, indent=2)
        
        # Exécuter le pipeline
        cmd = ['pdal', 'pipeline', pipeline_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"Erreur PDAL filtrage: {result.stderr}")
        
        # Nettoyer le fichier pipeline temporaire
        os.remove(pipeline_file)
    
    def _points_to_raster_pdal(self, points_file: str, reference_raster: str, 
                               output_file: str, work_dir: str) -> str:
        """Convertit les points de sol en raster masque"""
        logger.info("🔄 Conversion points → raster masque...")
        
        # Pipeline PDAL pour convertir points en raster
        pipeline = {
            "pipeline": [
                {
                    "type": "readers.las",
                    "filename": points_file
                },
                {
                    "type": "writers.gdal",
                    "filename": output_file,
                    "output_type": "idw",
                    "resolution": 1.0,
                    "window_size": 6,
                    "gdalopts": {
                        "co": ["TILED=YES", "COMPRESS=LZW"]
                    }
                }
            ]
        }
        
        pipeline_file = os.path.join(work_dir, "points_to_raster.json")
        with open(pipeline_file, 'w') as f:
            json.dump(pipeline, f, indent=2)
        
        # Exécuter le pipeline
        cmd = ['pdal', 'pipeline', pipeline_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"Erreur PDAL points→raster: {result.stderr}")
        
        # Nettoyer le fichier pipeline temporaire
        os.remove(pipeline_file)
        
        return output_file
    
    def _cleanup_temp_files_pdal(self, temp_files: list):
        """Nettoie les fichiers temporaires PDAL"""
        for file_path in temp_files:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"🗑️ Fichier temporaire supprimé: {file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Impossible de supprimer {file_path}: {e}")
    
    def get_method_info(self) -> Dict:
        """Retourne des informations sur les méthodes disponibles"""
        info = {
            'available_methods': self.available_methods,
            'saga_available': 'saga' in self.available_methods,
            'pdal_available': 'pdal' in self.available_methods,
            'recommended_method': 'saga' if 'saga' in self.available_methods else ('pdal' if 'pdal' in self.available_methods else None)
        }
        
        if 'saga' in self.available_methods:
            info['saga_info'] = {
                'description': 'SAGA GIS - Méthode traditionnelle de GEMAUT',
                'advantages': ['Mature et testée', 'Intégrée à GEMAUT', 'Paramètres optimisés'],
                'disadvantages': ['Plus lente', 'Dépendance externe']
            }
        
        if 'pdal' in self.available_methods:
            info['pdal_info'] = {
                'description': 'PDAL - Point Data Abstraction Library',
                'advantages': ['Plus rapide', 'Algorithme CSF avancé', 'Moins de dépendances'],
                'disadvantages': ['Plus récent', 'Paramètres à optimiser']
            }
        
        return info


# Fonction utilitaire pour utilisation directe
def compute_mask_auto(mns_file: str, output_mask_file: str, work_dir: str, 
                     method: str = 'auto', cpu_count: int = 4, 
                     params: Optional[Dict] = None) -> str:
    """
    Fonction utilitaire pour calculer un masque automatiquement
    
    Args:
        mns_file: Fichier MNS d'entrée
        output_mask_file: Fichier de sortie du masque
        work_dir: Répertoire de travail
        method: Méthode à utiliser ('saga', 'pdal', ou 'auto')
        cpu_count: Nombre de CPUs à utiliser
        params: Paramètres spécifiques à la méthode
        
    Returns:
        Chemin vers le fichier masque généré
    """
    computer = MaskComputer()
    return computer.compute_mask(mns_file, output_mask_file, work_dir, method, cpu_count, params)
