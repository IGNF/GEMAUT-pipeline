#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module pour le traitement des tuiles (découpage et assemblage)
Gère le découpage des grandes images en tuiles et leur assemblage final
"""

import os
import numpy as np
import rasterio
from rasterio.windows import Window, from_bounds
from multiprocessing import Pool
from tqdm import tqdm
import random
from loguru import logger
from typing import Tuple, List, Dict
from . import image_utils


class TileCalculator:
    """Classe pour calculer les paramètres de découpage en tuiles"""
    
    @staticmethod
    def calculate_tile_count(nb_colonnes: int, nb_lignes: int, 
                           taille_dalle: int, recouv_entre_dalles: int) -> Tuple[int, int]:
        """Calcule le nombre de dalles en X et en Y"""
        num_x = nb_colonnes - taille_dalle
        num_y = nb_lignes - taille_dalle
        denom = taille_dalle - recouv_entre_dalles
        
        # Calcul du nombre de dalles en X
        if num_x % denom == 0:
            nbre_dalle_x = num_x // denom + 1
        else:
            nbre_dalle_x = int((num_x / denom) + 1) + 1
        
        # Calcul du nombre de dalles en Y
        if num_y % denom == 0:
            nbre_dalle_y = num_y // denom + 1
        else:
            nbre_dalle_y = int((num_y / denom) + 1) + 1
        
        return int(nbre_dalle_x), int(nbre_dalle_y)
    
    @staticmethod
    def get_tile_dimensions(file_path: str, tile_size: int, pad_size: int) -> Tuple[int, int]:
        """Obtient les dimensions des tuiles pour un fichier donné"""
        with rasterio.open(file_path) as src:
            largeur = src.width
            hauteur = src.height
            
            # Calculer le pas entre les dalles en fonction du recouvrement
            pas_x = tile_size - pad_size
            pas_y = tile_size - pad_size
            
            # Calculer le nombre de dalles avec recouvrement
            nbre_dalle_x = (largeur - pad_size + pas_x - 1) // pas_x
            nbre_dalle_y = (hauteur - pad_size + pas_y - 1) // pas_y
            
            return nbre_dalle_x, nbre_dalle_y


class TileCutter:
    """Classe pour le découpage des images en tuiles"""
    
    @staticmethod
    def cut_tile(args: Tuple) -> None:
        """
        Découpe une tuile spécifique d'une image
        Conçue pour être utilisée avec multiprocessing
        """
        mns_file, masque_file, init_file, col_dalle, lig_dalle, x_offset, y_offset, l_dalle, h_dalle, no_data_value, rep_travail_tmp = args
        
        try:
            # Créer le répertoire de la dalle
            rep_dalle_xy = os.path.join(rep_travail_tmp, f"Dalle_{col_dalle}_{lig_dalle}")
            os.makedirs(rep_dalle_xy, exist_ok=True)
            
            # Lire les trois images avec rasterio
            with rasterio.open(mns_file) as mns_src, \
                 rasterio.open(masque_file) as masque_src, \
                 rasterio.open(init_file) as init_src:
                
                # Lire les dalles
                mns_dalle = mns_src.read(1, window=Window(x_offset, y_offset, l_dalle, h_dalle))
                masque_dalle = masque_src.read(1, window=Window(x_offset, y_offset, l_dalle, h_dalle))
                init_dalle = init_src.read(1, window=Window(x_offset, y_offset, l_dalle, h_dalle))
                
                # Créer et sauvegarder les trois dalles
                fichiers_dalles = {
                    "mns": os.path.join(rep_dalle_xy, f"Out_MNS_{col_dalle}_{lig_dalle}.tif"),
                    "masque": os.path.join(rep_dalle_xy, f"Out_MASQUE_{col_dalle}_{lig_dalle}.tif"),
                    "init": os.path.join(rep_dalle_xy, f"Out_INIT_{col_dalle}_{lig_dalle}.tif")
                }
                
                # Sauvegarder les dalles
                for name, dalle, src in zip(fichiers_dalles.keys(), 
                                          [mns_dalle, masque_dalle, init_dalle], 
                                          [mns_src, masque_src, init_src]):
                    profil = src.profile
                    profil.update({
                        'height': h_dalle,
                        'width': l_dalle,
                        'transform': src.window_transform(Window(x_offset, y_offset, l_dalle, h_dalle))
                    })
                    
                    image_utils.RasterProcessor.save_raster(dalle, fichiers_dalles[name], profil)
                    
        except Exception as e:
            logger.error(f"Erreur lors du découpage de la dalle {col_dalle}_{lig_dalle}: {e}")
            raise
    
    @staticmethod
    def cut_workspace(mns_file: str, masque_file: str, init_file: str, 
                     tile_size: int, pad_size: int, no_data_value: float, 
                     rep_travail_tmp: str, cpu_count: int) -> None:
        """Découpe un chantier complet en tuiles"""
        with rasterio.open(mns_file) as mns_src:
            largeur = mns_src.width
            hauteur = mns_src.height
            
            # Calculer le pas entre les dalles
            pas_x = tile_size - pad_size
            pas_y = tile_size - pad_size
            
            # Calculer le nombre de dalles
            nbre_dalle_x = (largeur - pad_size + pas_x - 1) // pas_x
            nbre_dalle_y = (hauteur - pad_size + pas_y - 1) // pas_y
            
            # Créer une liste des paramètres pour chaque dalle
            params = []
            for x in range(nbre_dalle_x):
                for y in range(nbre_dalle_y):
                    # Calculer la position pour chaque dalle
                    x_offset = x * pas_x
                    y_offset = y * pas_y
                    
                    # Calculer la largeur et hauteur de chaque bloc
                    l_bloc = min(tile_size, largeur - x_offset)
                    h_bloc = min(tile_size, hauteur - y_offset)
                    
                    # Ajouter les paramètres
                    params.append((mns_file, masque_file, init_file, x, y, 
                                 x_offset, y_offset, l_bloc, h_bloc, 
                                 no_data_value, rep_travail_tmp))
            
            # Utiliser multiprocessing pour traiter les dalles
            with Pool(processes=cpu_count) as pool:
                results = list(tqdm(pool.imap_unordered(TileCutter.cut_tile, params), 
                                  total=len(params), desc="- Traitement des dalles -"))


class TileAssembler:
    """Classe pour l'assemblage des tuiles en image finale"""
    
    @staticmethod
    def calculate_weight_mask(width: int, height: int, axis: int) -> np.ndarray:
        """Calcule un masque de pondération linéaire"""
        if axis == 1:  # Pondération horizontale
            x = np.linspace(0, 1, width)
            mask = np.tile(x, (height, 1))
        else:  # Pondération verticale
            y = np.linspace(0, 1, height)
            mask = np.tile(y[:, np.newaxis], (1, width))
        
        return mask
    
    @staticmethod
    def get_overlap_zone(src1, src2) -> Tuple[Window, Window]:
        """Calcule les fenêtres de chevauchement entre deux images"""
        bounds1 = src1.bounds
        bounds2 = src2.bounds
        intersection_bounds = (
            max(bounds1.left, bounds2.left),
            max(bounds1.bottom, bounds2.bottom),
            min(bounds1.right, bounds2.right),
            min(bounds1.top, bounds2.top)
        )
        
        if intersection_bounds[0] >= intersection_bounds[2] or intersection_bounds[1] >= intersection_bounds[3]:
            raise ValueError("Les images ne se chevauchent pas.")
        
        # Conversion des coordonnées d'intersection en fenêtres
        window1 = from_bounds(*intersection_bounds, src1.transform)
        window2 = from_bounds(*intersection_bounds, src2.transform)
        
        return window1, window2
    
    @staticmethod
    def assemble_tiles(rep_travail_tmp: str, nbre_dalle_x: int, nbre_dalle_y: int, 
                      chem_mnt_out: str) -> None:
        """Assemble toutes les tuiles en image finale"""
        total_steps = (nbre_dalle_y * nbre_dalle_x) + nbre_dalle_y + 1
        
        with tqdm(total=total_steps, desc="Progression globale", unit="étape") as pbar:
            # Assemblage horizontal (ligne par ligne)
            for y in range(nbre_dalle_y):
                ligne_dalles = []
                
                for x in range(nbre_dalle_x):
                    chem_dalle = os.path.join(rep_travail_tmp, f"Dalle_{x}_{y}", f"Out_MNT_{x}_{y}.tif")
                    
                    with rasterio.open(chem_dalle) as src:
                        profile = src.profile
                        
                        if x > 0:
                            # Fusion avec la dalle précédente
                            prev_dalle_path = ligne_dalles[-1]
                            with rasterio.open(prev_dalle_path) as src_prev:
                                prev_dalle = src_prev.read(1)
                                
                                # Obtenir zone de chevauchement
                                window_prev, window_curr = TileAssembler.get_overlap_zone(src_prev, src)
                                chevauchement_prev = src_prev.read(1, window=window_prev)
                                chevauchement_curr = src.read(1, window=window_curr)
                                
                                # Créer les masques de pondération
                                largeur, hauteur = chevauchement_curr.shape[1], chevauchement_curr.shape[0]
                                mask_droite = TileAssembler.calculate_weight_mask(largeur, hauteur, axis=1)
                                mask_gauche = 1 - mask_droite
                                
                                # Fusion pondérée
                                fusion = (chevauchement_prev * mask_gauche + chevauchement_curr * mask_droite)
                                prev_dalle[:, -largeur:] = fusion
                                dalle = src.read(1)
                                dalle = dalle[:, largeur:]
                                
                                # Enregistrer prev_dalle fusionnée
                                with rasterio.open(prev_dalle_path, 'w', **src_prev.profile) as dst_prev:
                                    dst_prev.write(prev_dalle, 1)
                                
                                # Création d'un profil de culture pour la dalle corrigée
                                src_crop = src.profile.copy()
                                src_crop.update(
                                    width=dalle.shape[1],
                                    height=dalle.shape[0],
                                    transform=src.window_transform(Window(largeur, 0, dalle.shape[1], dalle.shape[0]))
                                )
                                
                                # Enregistrer la dalle corrigée
                                temp_dalle_path = os.path.join(rep_travail_tmp, f"Dalle_corrigee_{x}_{y}.tif")
                                with rasterio.open(temp_dalle_path, 'w', **src_crop) as dst:
                                    dst.write(dalle, 1)
                        else:
                            dalle = src.read(1)
                            temp_dalle_path = os.path.join(rep_travail_tmp, f"Dalle_corrigee_{x}_{y}.tif")
                            with rasterio.open(temp_dalle_path, 'w', **profile) as dst:
                                dst.write(dalle, 1)
                        
                        ligne_dalles.append(temp_dalle_path)
                        pbar.update(1)
                
                # Construction de la mosaïque pour la ligne
                ligne_dalles_data = []
                for path in ligne_dalles:
                    with rasterio.open(path) as src:
                        data = src.read(1)
                        ligne_dalles_data.append(data)
                
                # Concatenation de la ligne
                ligne_mosaic = np.concatenate(ligne_dalles_data, axis=1)
                
                # Récupération des informations de géoréférencement
                with rasterio.open(ligne_dalles[0]) as src:
                    transform = src.transform
                    crs = src.crs
                    profile = src.profile
                
                # Mise à jour du profil
                profile.update(
                    width=ligne_mosaic.shape[1],
                    height=ligne_mosaic.shape[0],
                    transform=transform,
                    crs=crs,
                    count=1,
                    dtype=rasterio.float32
                )
                
                # Sauvegarder la mosaïque de la ligne
                output_path = os.path.join(rep_travail_tmp, f"ligne_mosaic_{y}.tif")
                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(ligne_mosaic, 1)
                
                pbar.update(1)
            
            # Assemblage vertical (toutes les lignes)
            all_mosaics = []
            
            for y in range(nbre_dalle_y):
                output_path = os.path.join(rep_travail_tmp, f"ligne_mosaic_{y}.tif")
                
                with rasterio.open(output_path) as src:
                    profile = src.profile
                    
                    if y > 0:
                        # Fusion avec la mosaïque de ligne précédente
                        prev_mosaic_path = all_mosaics[-1]
                        with rasterio.open(prev_mosaic_path) as src_prev:
                            prev_mosaic = src_prev.read(1)
                            
                            # Obtenir la zone de chevauchement vertical
                            window_prev, window_curr = TileAssembler.get_overlap_zone(src_prev, src)
                            chevauchement_prev = src_prev.read(1, window=window_prev)
                            chevauchement_curr = src.read(1, window=window_curr)
                            
                            largeur, hauteur = chevauchement_curr.shape[1], chevauchement_curr.shape[0]
                            mask_bas = TileAssembler.calculate_weight_mask(largeur, hauteur, axis=0)
                            mask_haut = 1 - mask_bas
                            
                            # Fusion pondérée des chevauchements
                            fusion = (chevauchement_prev * mask_haut + chevauchement_curr * mask_bas)
                            prev_mosaic[-hauteur:, :] = fusion
                            ligne_mosaic = src.read(1)
                            ligne_mosaic = ligne_mosaic[hauteur:, :]
                            
                            with rasterio.open(prev_mosaic_path, 'w', **src_prev.profile) as dst_prev:
                                dst_prev.write(prev_mosaic, 1)
                            
                            src_crop = src.profile.copy()
                            src_crop.update(
                                width=ligne_mosaic.shape[1],
                                height=ligne_mosaic.shape[0],
                                transform=src.window_transform(Window(0, hauteur, ligne_mosaic.shape[1], ligne_mosaic.shape[0]))
                            )
                            
                            temp_mosaic_path = os.path.join(rep_travail_tmp, f"ligne_mosaic_CORRIGEE_{y}.tif")
                            with rasterio.open(temp_mosaic_path, 'w', **src_crop) as dst:
                                dst.write(ligne_mosaic, 1)
                    else:
                        ligne_mosaic = src.read(1)
                        temp_mosaic_path = os.path.join(rep_travail_tmp, f"ligne_mosaic_CORRIGEE_{y}.tif")
                        with rasterio.open(temp_mosaic_path, 'w', **profile) as dst:
                            dst.write(ligne_mosaic, 1)
                    
                    all_mosaics.append(temp_mosaic_path)
                    pbar.update(1)
            
            # Construction de la mosaïque finale
            all_mosaics_data = []
            for path in all_mosaics:
                with rasterio.open(path) as src:
                    data = src.read(1)
                    all_mosaics_data.append(data)
            
            # Concatenation finale
            mosaic_final = np.concatenate(all_mosaics_data, axis=0)
            
            # Récupération des informations de géoréférencement
            with rasterio.open(all_mosaics[0]) as src:
                transform = src.transform
                crs = src.crs
                profile = src.profile
            
            # Mise à jour du profil final
            profile.update(
                width=mosaic_final.shape[1],
                height=mosaic_final.shape[0],
                transform=transform,
                crs=crs,
                count=1,
                dtype=rasterio.float32
            )
            
            # Sauvegarder la mosaïque finale
            with rasterio.open(chem_mnt_out, 'w', **profile) as dst:
                dst.write(mosaic_final, 1)
            
            logger.info(f"Mosaïque finale sauvegardée sous {chem_mnt_out}")
            pbar.update(pbar.total - pbar.n) 