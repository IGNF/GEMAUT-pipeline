#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitaires pour le traitement d'images raster
Centralise les fonctions communes de manipulation d'images
"""

import rasterio
import numpy as np
from rasterio.windows import Window, from_bounds
from scipy.spatial import distance_matrix
from scipy.interpolate import griddata, LinearNDInterpolator
from loguru import logger
import os
import shutil
from typing import Tuple, Optional


class RasterProcessor:
    """Classe pour le traitement des images raster"""
    
    @staticmethod
    def get_image_dimensions(file_path: str) -> Tuple[int, int]:
        """Obtient les dimensions d'une image raster"""
        try:
            with rasterio.open(file_path) as dataset:
                return dataset.height, dataset.width
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du fichier {file_path}: {e}")
            raise
    
    @staticmethod
    def get_image_info(file_path: str) -> dict:
        """Obtient les informations complètes d'une image raster"""
        try:
            with rasterio.open(file_path) as dataset:
                return {
                    'height': dataset.height,
                    'width': dataset.width,
                    'crs': dataset.crs,
                    'transform': dataset.transform,
                    'bounds': dataset.bounds,
                    'dtype': dataset.dtypes[0],
                    'nodata': dataset.nodata
                }
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des infos de {file_path}: {e}")
            raise
    
    @staticmethod
    def validate_raster_compatibility(mns_path: str, mask_path: str) -> Tuple[bool, dict]:
        """
        Vérifie la compatibilité entre le MNS et le masque
        
        Args:
            mns_path: Chemin vers le fichier MNS
            mask_path: Chemin vers le fichier masque
            
        Returns:
            Tuple[bool, dict]: (compatible, détails des différences)
        """
        try:
            # Obtenir les informations des deux fichiers
            mns_info = RasterProcessor.get_image_info(mns_path)
            mask_info = RasterProcessor.get_image_info(mask_path)
            
            # Vérifications
            issues = []
            
            # Vérification des dimensions
            if mns_info['height'] != mask_info['height']:
                issues.append(f"Hauteur différente: MNS={mns_info['height']}, Masque={mask_info['height']}")
            
            if mns_info['width'] != mask_info['width']:
                issues.append(f"Largeur différente: MNS={mns_info['width']}, Masque={mask_info['width']}")
            
            # Vérification du CRS
            if mns_info['crs'] != mask_info['crs']:
                issues.append(f"CRS différent: MNS={mns_info['crs']}, Masque={mask_info['crs']}")
            
            # Vérification de la transformation géographique
            if mns_info['transform'] != mask_info['transform']:
                issues.append(f"Transformation géographique différente")
            
            # Vérification des bornes
            if mns_info['bounds'] != mask_info['bounds']:
                issues.append(f"Bornes géographiques différentes")
            
            # Résumé des informations
            summary = {
                'mns_info': mns_info,
                'mask_info': mask_info,
                'issues': issues,
                'compatible': len(issues) == 0
            }
            
            return len(issues) == 0, summary
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation de compatibilité: {e}")
            return False, {'error': str(e), 'compatible': False}
    
    @staticmethod
    def contains_valid_data(file_path: str, no_data_value: float = -9999) -> bool:
        """Vérifie si une image contient des données valides"""
        try:
            with rasterio.open(file_path) as src:
                data = src.read(1)
                return not np.all(data == no_data_value)
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des données de {file_path}: {e}")
            return False
    
    @staticmethod
    def save_raster(data: np.ndarray, file_path: str, profile: dict) -> None:
        """Sauvegarde une image raster"""
        try:
            with rasterio.open(file_path, 'w', **profile) as dst:
                dst.write(data, 1)
            logger.debug(f"Image sauvegardée: {file_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de {file_path}: {e}")
            raise


class HoleFiller:
    """Classe pour le remplissage des trous dans les images raster"""
    
    @staticmethod
    def fill_holes_simple(input_path: str, output_path: str, 
                         no_data_int: float, no_data_ext: float) -> None:
        """Remplit les trous dans une image raster"""
        try:
            with rasterio.open(input_path) as src:
                mns = src.read(1)
                
                # Masque pour les pixels no_data_int uniquement
                mask_invalid = (mns == no_data_int)
                
                # Coordonnées des pixels valides et trous
                valid_indices = np.argwhere(~mask_invalid & (mns != no_data_ext))
                hole_indices = np.argwhere(mask_invalid)
                valid_values = mns[valid_indices[:, 0], valid_indices[:, 1]]
                
                if hole_indices.size == 0:
                    logger.info("Aucun trou détecté, aucune interpolation nécessaire.")
                    mns_filled = mns.copy()
                else:
                    # Utiliser LinearNDInterpolator
                    interpolator = LinearNDInterpolator(valid_indices, valid_values)
                    interpolated_values = interpolator(hole_indices)
                    
                    # Remplir les trous avec les valeurs interpolées
                    mns_filled = mns.copy()
                    valid_hole_indices = ~np.isnan(interpolated_values)
                    mns_filled[hole_indices[valid_hole_indices, 0], 
                              hole_indices[valid_hole_indices, 1]] = interpolated_values[valid_hole_indices]
                
                # Sauvegarde du résultat
                out_meta = src.meta.copy()
                out_meta.update({"dtype": 'float32'})
                RasterProcessor.save_raster(mns_filled, output_path, out_meta)
                
        except Exception as e:
            logger.error(f"Erreur lors du remplissage des trous: {e}")
            raise
    
    @staticmethod
    def fill_holes_with_interpolation(input_path: str, output_path: str,
                                    no_data_int: float, no_data_ext: float,
                                    edge_size: int = 5, weight_type: int = 1) -> None:
        """Remplit les trous avec interpolation pondérée"""
        try:
            with rasterio.open(input_path) as src:
                mns = src.read(1)
                
                # Masque des pixels NoData pour combler uniquement les trous no_data_int
                mask_invalid = (mns == no_data_int)
                
                # Identifier les indices des pixels valides et des trous
                valid_indices = np.argwhere(~mask_invalid & (mns != no_data_ext))
                hole_indices = np.argwhere(mask_invalid)
                
                if hole_indices.size == 0:
                    logger.info("Aucun trou détecté.")
                    mns_filled = mns.copy()
                else:
                    # Extraire les valeurs des pixels valides
                    valid_values = mns[valid_indices[:, 0], valid_indices[:, 1]]
                    
                    # Masque de pixels de bordure pour l'interpolation
                    edge_mask = np.zeros_like(mns, dtype=bool)
                    for i, j in hole_indices:
                        edge_mask[max(0, i - edge_size):min(i + edge_size + 1, mns.shape[0]),
                                 max(0, j - edge_size):min(j + edge_size + 1, mns.shape[1])] = True
                    
                    # Exclure les pixels NoData et garder uniquement les pixels de bordure
                    edge_mask &= ~mask_invalid & (mns != no_data_ext)
                    edge_indices = np.argwhere(edge_mask)
                    
                    if edge_indices.size == 0:
                        logger.warning("Aucun pixel de bordure trouvé, utilisation de tous les pixels valides")
                        edge_indices = valid_indices
                        edge_values = valid_values
                    else:
                        edge_values = mns[edge_indices[:, 0], edge_indices[:, 1]]
                    
                    # Interpolation pondérée
                    interpolated_values = griddata(
                        edge_indices,
                        edge_values,
                        hole_indices,
                        method='linear'
                    )
                    
                    # Remplir les trous
                    mns_filled = mns.copy()
                    for (i, j), val in zip(hole_indices, interpolated_values):
                        if not np.isnan(val):
                            mns_filled[i, j] = val
                
                # Sauvegarde
                out_meta = src.meta.copy()
                out_meta.update({"dtype": 'float32'})
                RasterProcessor.save_raster(mns_filled, output_path, out_meta)
                
        except Exception as e:
            logger.error(f"Erreur lors du remplissage avec interpolation: {e}")
            raise


class MaskProcessor:
    """Classe pour le traitement des masques"""
    
    @staticmethod
    def set_groundval_mask_to_0(input_path: str, output_path: str, ground_value: int) -> None:
        """Convertit un masque pour GEMO: SOL = 0 / SURSOL = 255"""
        try:
            with rasterio.open(input_path) as src:
                img_array = src.read(1)
                
                # Appliquer la condition : si le pixel est égal à groundval, mettre 0, sinon 255
                masque_binaire = np.where(img_array == ground_value, 0, 255).astype(np.uint8)
                
                # Paramètres pour le fichier de sortie
                out_meta = src.meta.copy()
                out_meta.update({
                    "dtype": 'uint8',
                    "count": 1,
                    "compress": 'lzw'
                })
                
                RasterProcessor.save_raster(masque_binaire, output_path, out_meta)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du masque: {e}")
            raise
    
    @staticmethod
    def set_nodata_extern_to_nodata_intern_mask(mask_path: str, mns_path: str, 
                                              output_path: str, no_data_ext: float, 
                                              no_data_interne_mask: int) -> None:
        """Gère les valeurs NoData externes et internes dans le masque"""
        try:
            with rasterio.open(mask_path) as src_mask, rasterio.open(mns_path) as src_mns:
                # Vérifier que les dimensions sont identiques
                if src_mask.shape != src_mns.shape:
                    raise ValueError("Les deux images doivent avoir les mêmes dimensions.")
                
                # Lire les bandes
                masque_4gemo = src_mask.read(1)
                mns_in = src_mns.read(1)
                
                # Appliquer la condition pour générer le masque de sortie
                masque_nodata = np.where(mns_in == no_data_ext, 
                                       no_data_interne_mask, masque_4gemo).astype(np.uint8)
                
                # Préparer les métadonnées
                out_meta = src_mask.meta.copy()
                out_meta.update({
                    "dtype": 'uint8',
                    "count": 1,
                    "compress": 'lzw'
                })
                
                RasterProcessor.save_raster(masque_nodata, output_path, out_meta)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement NoData du masque: {e}")
            raise


class DataReplacer:
    """Classe pour le remplacement de valeurs dans les images"""
    
    @staticmethod
    def replace_nodata_max(input_path: str, output_path: str, 
                          no_data_ext: float, no_data_max: float) -> None:
        """Remplace les valeurs no_data_ext par no_data_max"""
        try:
            with rasterio.open(input_path) as src:
                profile = src.profile
                data = src.read(1)
                
                # Vérifier et remplacer la valeur no_data_ext par no_data_max
                data[data == no_data_ext] = no_data_max
                
                # Mettre à jour la valeur no_data dans les métadonnées
                profile.update(nodata=no_data_max)
                
                RasterProcessor.save_raster(data, output_path, profile)
                
        except Exception as e:
            logger.error(f"Erreur lors du remplacement NoData: {e}")
            raise
    
    @staticmethod
    def set_nodata_extern_to_final_gemo_dtm(mnt_tmp_path: str, mns_sous_ech_path: str,
                                           output_path: str, no_data_ext: float) -> None:
        """Applique le masque NoData externe au MNT final"""
        try:
            with rasterio.open(mnt_tmp_path) as src_mnt, rasterio.open(mns_sous_ech_path) as src_mns:
                if src_mnt.shape != src_mns.shape:
                    raise ValueError("Les deux images doivent avoir les mêmes dimensions.")
                
                # Lire les bandes
                mnt_tmp = src_mnt.read(1)
                mns_in = src_mns.read(1)
                
                # Appliquer la condition pour générer le masque de sortie
                mnt_out = np.where(mns_in == no_data_ext, no_data_ext, mnt_tmp).astype(np.float32)
                
                # Préparer les métadonnées
                out_meta = src_mnt.meta.copy()
                out_meta.update({
                    "dtype": 'float32',
                    "count": 1,
                    "compress": 'lzw'
                })
                
                RasterProcessor.save_raster(mnt_out, output_path, out_meta)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'application du masque NoData final: {e}")
            raise 