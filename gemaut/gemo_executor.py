#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module pour l'exécution de GEMO en parallèle
Gère l'exécution des commandes GEMO sur les tuiles
"""

import os
import subprocess
import shutil
from multiprocessing import Pool
from tqdm import tqdm
import signal
from loguru import logger
from typing import List, Dict
from . import image_utils


class GEMOExecutor:
    """Classe pour l'exécution de GEMO en parallèle"""
    
    # Commande GEMO unitaire
    GEMO_UNIT_CMD = 'main_GEMAUT_unit'
    
    @staticmethod
    def init_worker():
        """Initialise le worker pour ignorer les signaux d'interruption"""
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    
    @staticmethod
    def run_command_without_output(cmd: str) -> int:
        """Exécute une commande sans afficher la sortie"""
        try:
            result = subprocess.run(cmd, shell=True, 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
            return result.returncode
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la commande: {e}")
            return -1
    
    @staticmethod
    def build_gemo_command(mns_file: str, masque_file: str, init_file: str, 
                          output_file: str, sigma: float, lambda_val: float, 
                          no_data_value: float, norme: str) -> str:
        """Construit la commande GEMO pour une tuile"""
        return f"{GEMOExecutor.GEMO_UNIT_CMD} {mns_file} {masque_file} {init_file} {output_file} {sigma:.5f} {lambda_val:.5f} {no_data_value:.5f} {norme}"
    
    @staticmethod
    def process_tile(args: tuple) -> str:
        """Traite une tuile avec GEMO"""
        x, y, rep_travail_tmp, gemo_params = args
        
        try:
            # Chemins des fichiers pour cette tuile
            rep_dalle_xy = os.path.join(rep_travail_tmp, f"Dalle_{x}_{y}")
            chem_out_mns = os.path.join(rep_dalle_xy, f"Out_MNS_{x}_{y}.tif")
            chem_out_masque = os.path.join(rep_dalle_xy, f"Out_MASQUE_{x}_{y}.tif")
            chem_out_init = os.path.join(rep_dalle_xy, f"Out_INIT_{x}_{y}.tif")
            chem_out_mnt = os.path.join(rep_dalle_xy, f"Out_MNT_{x}_{y}.tif")
            
            # Vérifier si la tuile contient des données valides
            if image_utils.RasterProcessor.contains_valid_data(chem_out_mns, gemo_params['no_data_value']):
                # Construire et exécuter la commande GEMO
                cmd = GEMOExecutor.build_gemo_command(
                    chem_out_mns, chem_out_masque, chem_out_init, chem_out_mnt,
                    gemo_params['sigma'], gemo_params['lambda'], 
                    gemo_params['no_data_value'], gemo_params['norme']
                )
                
                logger.debug(f"Exécution GEMO pour tuile {x}_{y}: {cmd}")
                result = GEMOExecutor.run_command_without_output(cmd)
                
                if result == 0:
                    return f"Tuile {x}_{y} traitée avec succès"
                else:
                    return f"Erreur lors du traitement de la tuile {x}_{y} (code: {result})"
            else:
                # Copier le MNS vers le MNT si pas de données valides
                shutil.copyfile(chem_out_mns, chem_out_mnt)
                return f"Tuile {x}_{y} copiée (pas de données valides)"
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la tuile {x}_{y}: {e}")
            return f"Erreur lors du traitement de la tuile {x}_{y}: {e}"
    
    @staticmethod
    def run_gemo_parallel(rep_travail_tmp: str, nbre_dalle_x: int, nbre_dalle_y: int,
                         gemo_params: Dict, cpu_count: int) -> None:
        """Exécute GEMO en parallèle sur toutes les tuiles"""
        
        # Préparer les arguments pour chaque tuile
        tasks = []
        for x in range(nbre_dalle_x):
            for y in range(nbre_dalle_y):
                tasks.append((x, y, rep_travail_tmp, gemo_params))
        
        logger.info(f"Lancement de GEMO sur {len(tasks)} tuiles avec {cpu_count} CPUs")
        
        # Exécuter en parallèle
        with Pool(processes=cpu_count, initializer=GEMOExecutor.init_worker) as pool:
            results = list(tqdm(
                pool.imap_unordered(GEMOExecutor.process_tile, tasks), 
                total=len(tasks), 
                desc="Lancement de GEMO unitaire en parallèle"
            ))
        
        # Analyser les résultats
        success_count = sum(1 for result in results if "succès" in result)
        error_count = len(results) - success_count
        
        logger.info(f"Traitement GEMO terminé: {success_count} succès, {error_count} erreurs")
        
        # Afficher les erreurs si il y en a
        if error_count > 0:
            logger.warning("Erreurs détectées:")
            for result in results:
                if "Erreur" in result:
                    logger.warning(f"  - {result}")


class GDALProcessor:
    """Classe pour les opérations GDAL"""
    
    @staticmethod
    def run_gdal_command(cmd: str, description: str = "") -> None:
        """Exécute une commande GDAL"""
        try:
            if description:
                logger.info(f"{description}: {cmd}")
            
            result = subprocess.run(cmd, shell=True, 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
            
            if result.returncode != 0:
                logger.error(f"Erreur lors de l'exécution de la commande GDAL: {cmd}")
                raise subprocess.CalledProcessError(result.returncode, cmd)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution GDAL: {e}")
            raise
    
    @staticmethod
    def resample_raster(input_file: str, output_file: str, resolution: float, 
                       src_nodata: float, dst_nodata: float, output_type: str = None) -> None:
        """Rééchantillonne un raster avec GDAL"""
        cmd_parts = [
            "gdalwarp",
            f"-tr {resolution:.10f} {resolution:.10f}",
            f"-srcnodata {src_nodata}",
            f"-dstnodata {dst_nodata}",
            input_file,
            output_file,
            "-overwrite"
        ]
        
        if output_type:
            cmd_parts.insert(-2, f"-ot {output_type}")
        
        cmd = " ".join(cmd_parts)
        GDALProcessor.run_gdal_command(cmd, f"Sous-échantillonnage à la résolution de {resolution} mètres")
    
    @staticmethod
    def resample_mns(input_file: str, output_file: str, resolution: float, 
                    no_data_ext: float) -> None:
        """Rééchantillonne le MNS"""
        GDALProcessor.resample_raster(input_file, output_file, resolution, 
                                    no_data_ext, no_data_ext)
    
    @staticmethod
    def resample_mask(input_file: str, output_file: str, resolution: float, 
                     no_data_interne_mask: int) -> None:
        """Rééchantillonne le masque"""
        GDALProcessor.resample_raster(input_file, output_file, resolution, 
                                    no_data_interne_mask, no_data_interne_mask, "Byte")
    
    @staticmethod
    def resample_init(input_file: str, output_file: str, resolution: float, 
                     no_data_ext: float) -> None:
        """Rééchantillonne le fichier d'initialisation"""
        GDALProcessor.resample_raster(input_file, output_file, resolution, 
                                    no_data_ext, no_data_ext) 