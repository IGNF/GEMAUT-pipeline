#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pipeline GEMAUT refactorisé
Version maintenable et modulaire du script de génération de modèles automatiques de terrain
"""

import sys
import os
import time
import shutil
import argparse
from loguru import logger

# Import des modules refactorisés
import config
from gemaut_config import GEMAUTConfig
import image_utils
import tile_processor
import gemo_executor
import saga_integration


class GEMAUTPipeline:
    """Pipeline principal GEMAUT refactorisé"""
    
    def __init__(self, config: GEMAUTConfig):
        """Initialise le pipeline avec la configuration"""
        self.config = config
        self.setup_logging()
        self.config.create_directories()
        
    def setup_logging(self):
        """Configure le système de logging"""
        log_file_path = self.config.get_log_file_path()
        logger.remove()  # Supprimer les handlers par défaut
        logger.add(log_file_path, level=config.LOG_LEVEL, format=config.LOG_FORMAT)
        
        # Ajouter un handler pour la console si l'option verbose est activée
        if self.config.verbose:
            logger.add(sys.stderr, level=config.LOG_LEVEL, format=config.LOG_FORMAT)
    
    def run(self):
        """Exécute le pipeline complet"""
        start_time = time.time()
        start_time_str = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(start_time))
        
        try:
            logger.info(config.INFO_MESSAGES['start'].format(start_time=start_time_str))
            logger.info(f"Configuration: {self.config.to_dict()}")
            
            # Étape 1: Remplissage des trous dans MNS
            self._fill_holes_in_mns()
            
            # Étape 2: Remplacement des valeurs NoData max
            self._replace_nodata_max()
            
            # Étape 3: Calcul ou utilisation du masque
            self._process_mask()
            
            # Étape 4: Traitement du masque pour GEMO
            self._prepare_mask_for_gemo()
            
            # Étape 5: Gestion des valeurs NoData externes et internes
            self._handle_nodata_values()
            
            # Étape 6: Sous-échantillonnage
            self._resample_data()
            
            # Étape 7: Calcul du nombre de dalles
            nbre_dalle_x, nbre_dalle_y = self._calculate_tile_count()
            
            # Étape 8: Découpage des dalles
            self._cut_tiles()
            
            # Étape 9: Exécution de GEMO en parallèle
            self._run_gemo_parallel(nbre_dalle_x, nbre_dalle_y)
            
            # Étape 10: Assemblage final
            self._assemble_final_result(nbre_dalle_x, nbre_dalle_y)
            
            # Étape 11: Application du masque NoData final
            self._apply_final_nodata_mask()
            
            # Étape 12: Nettoyage (optionnel)
            if self.config.clean_temp:
                self._cleanup_temp_files()
            
            # Calcul et affichage du temps total
            self._log_completion_time(start_time)
            
            logger.info(config.INFO_MESSAGES['end'])
            
        except Exception as e:
            logger.error(config.ERROR_MESSAGES['general'].format(error=e))
            raise
    
    def _fill_holes_in_mns(self):
        """Remplit les trous dans le MNS"""
        logger.info(config.INFO_MESSAGES['holes_filling'])
        image_utils.HoleFiller.fill_holes_simple(
            self.config.mns_input,
            self.config.temp_files['mns_sans_trou'],
            self.config.nodata_int,
            self.config.nodata_ext
        )
    
    def _replace_nodata_max(self):
        """Remplace les valeurs NoData max dans MNS"""
        logger.info(config.INFO_MESSAGES['nodata_replacement'])
        image_utils.DataReplacer.replace_nodata_max(
            self.config.temp_files['mns_sans_trou'],
            self.config.temp_files['mns4saga'],
            self.config.nodata_ext,
            self.config.nodata_max
        )
    
    def _process_mask(self):
        """Traite le masque (calcul SAGA ou utilisation du fichier fourni)"""
        if self.config.mask_file is None:
            logger.info(config.INFO_MESSAGES['mask_computation'])
            output_mask_file = os.path.join(self.config.work_dir, 'MASQUE_compute.tif')
            
            # Vérifier l'environnement SAGA
            saga_integration.SAGAIntegration.log_saga_environment()
            
            # Calculer le masque avec SAGA
            saga_integration.SAGAIntegration.compute_mask_with_saga(
                self.config.temp_files['mns4saga'],
                output_mask_file,
                self.config.saga_dir,
                self.config.cpu_count,
                self.config.get_saga_params()
            )
            self.config.mask_file = output_mask_file
        else:
            logger.info(f"Utilisation du masque fourni: {self.config.mask_file}")
    
    def _prepare_mask_for_gemo(self):
        """Prépare le masque pour GEMO"""
        logger.info(config.INFO_MESSAGES['mask_labeling'])
        image_utils.MaskProcessor.set_groundval_mask_to_0(
            self.config.mask_file,
            self.config.temp_files['masque_4gemo'],
            self.config.ground_value
        )
    
    def _handle_nodata_values(self):
        """Gère les valeurs NoData externes et internes"""
        logger.info(config.INFO_MESSAGES['nodata_management'])
        image_utils.MaskProcessor.set_nodata_extern_to_nodata_intern_mask(
            self.config.temp_files['masque_4gemo'],
            self.config.mns_input,
            self.config.temp_files['masque_nodata'],
            self.config.nodata_ext,
            self.config.nodata_interne_mask
        )
    
    def _resample_data(self):
        """Rééchantillonne les données à la résolution de travail"""
        logger.info(config.INFO_MESSAGES['subsampling'].format(reso=self.config.resolution))
        
        # Rééchantillonnage du MNS
        gemo_executor.GDALProcessor.resample_mns(
            self.config.temp_files['mns_sans_trou'],
            self.config.temp_files['mns_sous_ech'],
            self.config.resolution,
            self.config.nodata_ext
        )
        
        # Rééchantillonnage du masque
        gemo_executor.GDALProcessor.resample_mask(
            self.config.temp_files['masque_nodata'],
            self.config.temp_files['masque_sous_ech'],
            self.config.resolution,
            self.config.nodata_interne_mask
        )
        
        # Rééchantillonnage du fichier d'initialisation
        init_file = self.config.mns_input if self.config.init_file is None else self.config.init_file
        gemo_executor.GDALProcessor.resample_init(
            init_file,
            self.config.temp_files['init_sous_ech'],
            self.config.resolution,
            self.config.nodata_ext
        )
    
    def _calculate_tile_count(self):
        """Calcule le nombre de dalles"""
        logger.info(config.INFO_MESSAGES['tiles_calculation'])
        return tile_processor.TileCalculator.get_tile_dimensions(
            self.config.temp_files['mns_sous_ech'],
            self.config.tile_size,
            self.config.pad_size
        )
    
    def _cut_tiles(self):
        """Découpe le chantier en tuiles"""
        logger.info(config.INFO_MESSAGES['tiles_cutting'])
        tile_processor.TileCutter.cut_workspace(
            self.config.temp_files['mns_sous_ech'],
            self.config.temp_files['masque_sous_ech'],
            self.config.temp_files['init_sous_ech'],
            self.config.tile_size,
            self.config.pad_size,
            self.config.nodata_ext,
            self.config.tmp_dir,
            self.config.cpu_count
        )
    
    def _run_gemo_parallel(self, nbre_dalle_x, nbre_dalle_y):
        """Exécute GEMO en parallèle"""
        logger.info(config.INFO_MESSAGES['gemo_execution'])
        gemo_executor.GEMOExecutor.run_gemo_parallel(
            self.config.tmp_dir,
            nbre_dalle_x,
            nbre_dalle_y,
            self.config.get_gemo_params(),
            self.config.cpu_count
        )
    
    def _assemble_final_result(self, nbre_dalle_x, nbre_dalle_y):
        """Assemble le résultat final"""
        logger.info(config.INFO_MESSAGES['final_assembly'])
        tile_processor.TileAssembler.assemble_tiles(
            self.config.tmp_dir,
            nbre_dalle_x,
            nbre_dalle_y,
            self.config.temp_files['mnt_out_tmp']
        )
    
    def _apply_final_nodata_mask(self):
        """Applique le masque NoData final"""
        image_utils.DataReplacer.set_nodata_extern_to_final_gemo_dtm(
            self.config.temp_files['mnt_out_tmp'],
            self.config.temp_files['mns_sous_ech'],
            self.config.mnt_output,
            self.config.nodata_ext
        )
    
    def _cleanup_temp_files(self):
        """Nettoie les fichiers temporaires"""
        logger.info(config.INFO_MESSAGES['cleanup'])
        shutil.rmtree(self.config.tmp_dir)
    
    def _log_completion_time(self, start_time):
        """Enregistre le temps de traitement total"""
        end_time = time.time()
        elapsed_time = end_time - start_time
        formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        logger.info(f"Temps total de traitement: {formatted_time}")


def parse_arguments():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(
        description='GEMAUT - Génération de Modèles Automatiques de Terrain (Version Refactorisée)',
        epilog="""EXEMPLES D'UTILISATION:

1. Avec fichier de configuration YAML (recommandé):
   python script_gemaut.py --config config.yaml

2. Avec arguments de ligne de commande:
   python script_gemaut.py --mns /chem/vers/MNS_in.tif --out /chem/vers/MNT.tif --reso 4 --cpu 24 --RepTra /chem/vers/RepTra [--sigma 0.5] [--regul 0.01] [--tile 300] [--pad 120] [--norme hubertukey] [--nodata_ext -32768] [--nodata_int -32767] [--init /chem/vers/MNS_in.tif] [--masque /chem/vers/MASQUE_GEMO.tif] [--groundval 0] [--clean]

3. Créer un template de configuration:
   python script_gemaut.py --create-config config.yaml

IMPORTANT: Le MNS doit avoir des valeurs de no_data différentes pour les bords de chantier [no_data_ext] et les trous à l'intérieur du chantier [no_data_int] là où la corrélation a échoué par exemple
    """,
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Groupe pour les modes d'exécution
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--config", type=str, help="fichier de configuration YAML")
    mode_group.add_argument("--create-config", type=str, help="créer un template de configuration YAML")
    
    # Arguments pour le mode ligne de commande (optionnels si --config est utilisé)
    parser.add_argument("--mns", type=str, help="input DSM")
    parser.add_argument("--out", type=str, help="output DTM")
    parser.add_argument("--reso", type=float, help="resolution du MNT en sortie")
    parser.add_argument("--cpu", type=int, help="nombre de CPUs à utiliser")
    parser.add_argument("--RepTra", type=str, help="repertoire de Travail")
    
    # Arguments optionnels (pour le mode ligne de commande)
    
    # Arguments optionnels
    parser.add_argument("--masque", type=str, help="input ground/above-ground MASK")
    parser.add_argument("--groundval", default=0, type=int, help="valeur de masque pour le SOL")
    parser.add_argument("--init", type=str, help="initialisation [par défaut le MNS]")
    parser.add_argument("--nodata_ext", type=int, default=config.DEFAULT_NODATA_EXT, help="Valeur du no_data sur les bords")
    parser.add_argument("--nodata_int", type=int, default=config.DEFAULT_NODATA_INT, help="Valeur du no_data pour les trous")
    parser.add_argument("--sigma", type=float, default=config.DEFAULT_SIGMA, help="sigma / précision du Z MNS")
    parser.add_argument("--regul", type=float, default=config.DEFAULT_REGUL, help="regul / rigidité de la nappe")
    parser.add_argument("--tile", type=int, default=config.DEFAULT_TILE_SIZE, help="taille de la tuile")
    parser.add_argument("--pad", type=int, default=config.DEFAULT_PAD_SIZE, help="recouvrement entre tuiles")
    parser.add_argument("--norme", type=str, default=config.DEFAULT_NORME, help="choix entre les normes")
    parser.add_argument("--clean", action='store_true', help="supprimer les fichiers temporaires")
    parser.add_argument("--verbose", action='store_true', help="afficher les messages dans la console en plus du fichier de log")
    
    args = parser.parse_args()
    
    # Validation pour le mode ligne de commande
    if not args.config and not args.create_config:
        # Vérifier que tous les arguments obligatoires sont présents
        required_args = ['mns', 'out', 'reso', 'cpu', 'RepTra']
        missing_args = [arg for arg in required_args if not getattr(args, arg)]
        if missing_args:
            parser.error(f"Arguments obligatoires manquants: {', '.join(missing_args)}")
    
    if args.masque and args.groundval is None:
        parser.error("--groundval est obligatoire si --masque est renseigné.")

    return args


def main():
    """Fonction principale"""
    try:
        # Parser les arguments
        args = parse_arguments()
        
        # Gérer les différents modes
        if args.create_config:
            # Mode création de template
            from config_manager import ConfigManager
            ConfigManager.create_template(args.create_config)
            print(f"Template de configuration créé: {args.create_config}")
            print("Modifiez ce fichier selon vos besoins, puis utilisez --config pour l'exécuter.")
            return
        
        if args.config:
            # Mode fichier de configuration YAML
            from config_manager import ConfigManager
            yaml_config = ConfigManager.load_config(args.config)
            ConfigManager.validate_config(yaml_config)
            config_obj = ConfigManager.convert_to_gemaut_config(yaml_config)
        else:
            # Mode ligne de commande classique
            config_obj = GEMAUTConfig(
                mns_input=args.mns,
                mnt_output=args.out,
                resolution=args.reso,
                cpu_count=args.cpu,
                work_dir=args.RepTra,
                mask_file=args.masque,
                ground_value=args.groundval,
                init_file=args.init,
                nodata_ext=args.nodata_ext,
                nodata_int=args.nodata_int,
                sigma=args.sigma,
                regul=args.regul,
                tile_size=args.tile,
                pad_size=args.pad,
                norme=args.norme,
                clean_temp=args.clean,
                verbose=args.verbose
            )
        
        # Créer et exécuter le pipeline
        pipeline = GEMAUTPipeline(config_obj)
        pipeline.run()
        
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()