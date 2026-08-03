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
from . import config
from .gemaut_config import GEMAUTConfig
from . import image_utils
from . import tile_processor
from . import gemo_executor
from . import saga_integration

from pprint import pprint

class GEMAUTPipeline:
    """Pipeline principal GEMAUT refactorisé"""
    
    def __init__(self, config: GEMAUTConfig):
        """Initialise le pipeline avec la configuration"""
        self.config = config
        self.setup_logging()
        self.config.create_directories()
        
    def setup_logging(self):
        """Configure le logging : fichier + console (toujours).

        - Fichier : à côté du MNT de sortie
        - Console : INFO par défaut, DEBUG si verbose
        """
        log_file_path = self.config.get_log_file_path()
        log_dir = os.path.dirname(log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        console_level = "DEBUG" if self.config.verbose else config.LOG_LEVEL

        logger.remove()  # retire le handler par défaut loguru
        # Fichier: détail complet ; console: INFO (ou DEBUG si --verbose)
        logger.add(log_file_path, level="DEBUG", format=config.LOG_FORMAT)
        logger.add(sys.stderr, level=console_level, format=config.LOG_FORMAT)

    def run(self):
        """Exécute le pipeline complet"""
        start_time = time.time()
        start_time_str = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(start_time))
        
        try:
            logger.info(f"Programme démarré à : {start_time_str}")
            self._log_run_summary()
            logger.debug(f"Configuration complète: {self.config.to_dict()}")
            
            # Étape 1: Compatibilité MNS/Masque (si masque fourni)
            self._validate_input_compatibility()
            
            # Étape 2: Remplissage des trous dans MNS
            self._fill_holes_in_mns()
            logger.info("[2/12] Remplissage des trous MNS — OK")
            
            # Étape 3: Préparation MNS pour calcul de masque
            self._replace_nodata_max()
            logger.info("[3/12] Préparation MNS pour masque — OK")
            
            # Étape 4: Calcul ou utilisation du masque
            self._process_mask()
            
            # Étape 5: Traitement du masque pour GEMO
            self._prepare_mask_for_gemo()
            logger.info("[5/12] Préparation masque GEMO — OK")
            
            # Étape 6: Gestion des valeurs NoData externes et internes
            self._handle_nodata_values()
            logger.info("[6/12] Gestion NoData masque — OK")
            
            # Étape 7: Sous-échantillonnage
            self._resample_data()
            logger.info(f"[7/12] Sous-échantillonnage @ {self.config.resolution} m — OK")
            
            # Étape 8: Calcul du nombre de dalles
            nbre_dalle_x, nbre_dalle_y = self._calculate_tile_count()
            n_tiles = nbre_dalle_x * nbre_dalle_y
            logger.info(f"[8/12] Calcul des dalles — {n_tiles} tuiles ({nbre_dalle_x}×{nbre_dalle_y})")

            # Étape 9: Découpage des dalles
            self._cut_tiles()
            logger.info("[9/12] Découpage des dalles — OK")
            
            # Étape 10: Exécution de GEMO en parallèle
            self._run_gemo_parallel(nbre_dalle_x, nbre_dalle_y)
            logger.info(f"[10/12] GEMO parallèle — {n_tiles} tuiles")

            # Étape 11: Assemblage final
            self._assemble_final_result(nbre_dalle_x, nbre_dalle_y)
            logger.info("[11/12] Assemblage MNT — OK")

            # Étape 12: Application du masque NoData final (+ nettoyage optionnel)
            self._apply_final_nodata_mask()
            if self.config.clean_temp:
                self._cleanup_temp_files()
                logger.info("[12/12] NoData final + nettoyage — OK")
            else:
                logger.info("[12/12] NoData final — OK (nettoyage non demandé)")
            
            logger.info(f"MNT écrit: {self.config.mnt_output}")
            self._log_completion_time(start_time)
            logger.info("END")
            
        except Exception as e:
            logger.error(f"ERREUR FATALE dans le pipeline: {e}")
            logger.error(f"Type d'erreur: {type(e).__name__}")
            import traceback
            logger.debug(f"Traceback complet:\n{traceback.format_exc()}")
            raise

    def _log_run_summary(self):
        """Résumé compact de la config (niveau INFO)."""
        if self.config.mask_file:
            mask_info = f"masque fourni: {self.config.mask_file}"
        else:
            mask_info = f"calcul auto ({self.config.mask_method})"
        logger.info(f"MNS: {self.config.mns_input}")
        logger.info(f"MNT: {self.config.mnt_output}")
        logger.info(f"work_dir: {self.config.work_dir}")
        logger.info(f"Masque: {mask_info}")
        logger.info(
            f"Résolution: {self.config.resolution} m | "
            f"CPU: {self.config.cpu_count} | "
            f"tuiles GEMO: {self.config.tile_size}/pad {self.config.pad_size}"
        )
    
    def _validate_input_compatibility(self):
        """Vérifie la compatibilité entre le MNS et le masque fourni."""
        if self.config.mask_file is None:
            logger.debug("Pas de masque fourni — compatibilité vérifiée après calcul")
            logger.info("[1/12] Compatibilité MNS/masque — skip (masque à calculer)")
            return
        
        logger.info("[1/12] Compatibilité MNS/masque")
        try:
            compatible, details = image_utils.RasterProcessor.validate_raster_compatibility(
                self.config.mns_input, 
                self.config.mask_file
            )
            
            if not compatible:
                logger.error("INCOMPATIBILITÉ entre le MNS et le masque:")
                for issue in details['issues']:
                    logger.error(f"  - {issue}")
                logger.error(
                    f"  MNS: {details['mns_info']['width']}x{details['mns_info']['height']}, "
                    f"CRS: {details['mns_info']['crs']}"
                )
                logger.error(
                    f"  Masque: {details['mask_info']['width']}x{details['mask_info']['height']}, "
                    f"CRS: {details['mask_info']['crs']}"
                )
                raise ValueError("Le MNS et le masque ne sont pas compatibles. Vérifiez les dimensions et le CRS.")

            logger.info(
                f"[1/12] Compatibilité MNS/masque — OK "
                f"({details['mns_info']['width']}x{details['mns_info']['height']})"
            )
            logger.debug(f"CRS: {details['mns_info']['crs']}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de compatibilité: {e}")
            raise
    
    def _fill_holes_in_mns(self):
        """Remplit les trous dans le MNS"""
        logger.debug(config.INFO_MESSAGES['holes_filling'])
        image_utils.HoleFiller.fill_holes_simple(
            self.config.mns_input,
            self.config.temp_files['mns_sans_trou'],
            self.config.nodata_int,
            self.config.nodata_ext
        )
    
    def _replace_nodata_max(self):
        """Remplace les valeurs NoData max dans MNS"""
        logger.debug(config.INFO_MESSAGES['nodata_replacement'])
        image_utils.DataReplacer.replace_nodata_max(
            self.config.temp_files['mns_sans_trou'],
            self.config.temp_files['mns_for_mask'],
            self.config.nodata_ext,
            self.config.nodata_max
        )
    
    def _process_mask(self):
        """Traite le masque : fichier fourni, sinon calcul automatique (pdal/saga)."""
        if self.config.mask_file is not None:
            logger.info(f"[4/12] Masque fourni — {self.config.mask_file}")
            return

        method = self.config.mask_method
        logger.info(f"[4/12] Calcul masque ({method})")
        output_mask_file = os.path.join(self.config.work_dir, 'MASQUE_compute.tif')
        t0 = time.time()

        try:
            from .mask_computer import MaskComputer
            mask_computer = MaskComputer()

            method_info = mask_computer.get_method_info()
            logger.debug(f"Méthodes disponibles: {', '.join(method_info['available_methods'])}")

            if method == 'saga':
                params = self.config.get_saga_params()
            elif method == 'pdal':
                params = self.config.get_pdal_params()
            else:
                raise ValueError(
                    f"Méthode non supportée: {method}. Utilisez 'pdal' ou 'saga'."
                )

            mask_file = mask_computer.compute_mask(
                mns_file=self.config.temp_files['mns_for_mask'],
                output_mask_file=output_mask_file,
                work_dir=self.config.work_dir,
                method=method,
                cpu_count=self.config.cpu_count,
                params=params
            )

            if method == 'saga':
                mask_brut_saga = os.path.join(self.config.work_dir, 'MASQUE_SAGA_BRUT_avant_correction.tif')
                shutil.copy2(mask_file, mask_brut_saga)
                logger.debug(f"Masque SAGA brut sauvegardé: {mask_brut_saga}")

            self.config.mask_file = mask_file
            self._log_mask_class_stats(mask_file)
            elapsed = time.time() - t0
            logger.info(f"[4/12] Calcul masque ({method}) — OK ({elapsed:.1f}s) → {mask_file}")

        except ImportError as e:
            logger.error(f"Module de calcul automatique non disponible: {e}")
            raise RuntimeError(f"Impossible d'importer le module de calcul automatique: {e}")
        except Exception as e:
            logger.error(f"Erreur lors du calcul du masque avec {method}: {e}")
            raise RuntimeError(f"Erreur lors du calcul du masque avec {method}: {e}")

        # Vérifier la compatibilité après calcul du masque
        self._validate_computed_mask_compatibility(method)

    def _log_mask_class_stats(self, mask_path: str) -> None:
        """Log INFO Sol/Sursol (même présentation pour PDAL et SAGA)."""
        try:
            import numpy as np
            import rasterio
            with rasterio.open(mask_path) as src:
                data = src.read(1)
            total = data.size
            if total == 0:
                return
            # Convention GEMAUT: 0 = sol, 1 = sursol (autres valeurs ignorées dans le résumé)
            sol = int(np.sum(data == 0))
            sursol = int(np.sum(data == 1))
            logger.info(
                f"        Sol {100.0 * sol / total:.1f}% | "
                f"Sursol {100.0 * sursol / total:.1f}%"
            )
        except Exception as e:
            logger.debug(f"Impossible de calculer les stats masque: {e}")

    def _validate_computed_mask_compatibility(self, method: str) -> None:
        """Valide le masque calculé vs MNS.

        - dimensions / CRS différents → erreur
        - transform / bornes seuls (souvent SAGA) → DEBUG seulement
        """
        logger.debug("Vérification de la compatibilité après calcul du masque...")
        try:
            compatible, details = image_utils.RasterProcessor.validate_raster_compatibility(
                self.config.mns_input,
                self.config.mask_file
            )
            if compatible:
                logger.debug("Compatibilité validée après calcul du masque")
                return

            issues = details.get('issues', [])
            critical = [
                i for i in issues
                if i.startswith('Hauteur') or i.startswith('Largeur') or i.startswith('CRS')
            ]
            minor = [i for i in issues if i not in critical]

            for issue in minor:
                logger.debug(f"Différence géographique mineure (masque): {issue}")

            if critical:
                for issue in critical:
                    logger.error(f"Différence géographique masque: {issue}")
                raise ValueError("Le masque calculé n'est pas compatible avec le MNS")

            logger.debug(
                f"Masque {method}: dimensions OK, écarts géo mineurs ignorés "
                "(alignement affiné au sous-échantillonnage)"
            )
        except ValueError:
            raise
        except Exception as e:
            logger.warning(f"Impossible de vérifier la compatibilité: {e} — continuation")
    

    def _prepare_mask_for_gemo(self):
        """Prépare le masque pour GEMO"""
        logger.debug(config.INFO_MESSAGES['mask_labeling'])
        image_utils.MaskProcessor.set_groundval_mask_to_0(
            self.config.mask_file,
            self.config.temp_files['masque_4gemo'],
            self.config.ground_value
        )
    
    def _handle_nodata_values(self):
        """Gère les valeurs NoData externes et internes"""
        logger.debug(config.INFO_MESSAGES['nodata_management'])
        image_utils.MaskProcessor.set_nodata_extern_to_nodata_intern_mask(
            self.config.temp_files['masque_4gemo'],
            self.config.mns_input,
            self.config.temp_files['masque_nodata'],
            self.config.nodata_ext,
            self.config.nodata_int,
            self.config.nodata_interne_mask
        )
    
    def _resample_data(self):
        """Rééchantillonne les données à la résolution de travail"""
        logger.debug(config.INFO_MESSAGES['subsampling'].format(reso=self.config.resolution))
        
        # Rééchantillonnage du MNS
        gemo_executor.GDALProcessor.resample_mns(
            self.config.temp_files['mns_sans_trou'],
            self.config.temp_files['mns_sous_ech'],
            self.config.resolution,
            self.config.nodata_ext
        )
        
        # Combler les trous restants après sous-échantillonnage
        mns_sous_ech_filled = self.config.temp_files['mns_sous_ech'] + '.filled.tif'
        image_utils.HoleFiller.fill_holes_simple(
            self.config.temp_files['mns_sous_ech'],
            mns_sous_ech_filled,
            self.config.nodata_int,
            self.config.nodata_ext
        )
        shutil.move(mns_sous_ech_filled, self.config.temp_files['mns_sous_ech'])
        
        # Rééchantillonnage du masque
        gemo_executor.GDALProcessor.resample_mask(
            self.config.temp_files['masque_nodata'],
            self.config.temp_files['masque_sous_ech'],
            self.config.resolution,
            self.config.nodata_interne_mask
        )
        
        # Initialisation GEMO : même surface que le MNS comblé sous-échantillonné.
        # GEMO normalise INIT avec le min/max du MNS (GEA.cpp) : des -32767 dans INIT
        # produisent un point de départ aberrant pour l'optimiseur.
        if self.config.init_file is None:
            shutil.copy2(
                self.config.temp_files['mns_sous_ech'],
                self.config.temp_files['init_sous_ech']
            )
        else:
            gemo_executor.GDALProcessor.resample_init(
                self.config.init_file,
                self.config.temp_files['init_sous_ech'],
                self.config.resolution,
                self.config.nodata_ext
            )
    
    def _calculate_tile_count(self):
        """Calcule le nombre de dalles"""
        logger.debug(config.INFO_MESSAGES['tiles_calculation'])
        return tile_processor.TileCalculator.get_tile_dimensions(
            self.config.temp_files['mns_sous_ech'],
            self.config.tile_size,
            self.config.pad_size
        )
    
    def _cut_tiles(self):
        """Découpe le chantier en tuiles"""
        logger.debug(config.INFO_MESSAGES['tiles_cutting'])
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
        logger.debug(config.INFO_MESSAGES['gemo_execution'])
        gemo_executor.GEMOExecutor.run_gemo_parallel(
            self.config.tmp_dir,
            nbre_dalle_x,
            nbre_dalle_y,
            self.config.get_gemo_params(),
            self.config.cpu_count
        )
    
    def _assemble_final_result(self, nbre_dalle_x, nbre_dalle_y):
        """Assemble le résultat final"""
        logger.debug(config.INFO_MESSAGES['final_assembly'])
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
        logger.debug(config.INFO_MESSAGES['cleanup'])
        shutil.rmtree(self.config.tmp_dir)
    
    def _log_completion_time(self, start_time):
        """Enregistre le temps de traitement total"""
        end_time = time.time()
        elapsed_time = end_time - start_time
        formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        logger.info(f"Temps total: {formatted_time}")

# def parse_arguments():
#     """Parse les arguments de ligne de commande"""
#     parser = argparse.ArgumentParser(
#         description='GEMAUT - Génération de Modèles Automatiques de Terrain (Version Refactorisée)'
#         Auteur: Nicolas Champion - nicolas.champion@ign.fr""",
#         formatter_class=argparse.RawTextHelpFormatter,
#         epilog="""EXEMPLES D'UTILISATION:
        
# def parse_arguments():
#     """Parse les arguments de ligne de commande"""
#     parser = argparse.ArgumentParser(
#         description='GEMAUT - Génération de Modèles Automatiques de Terrain (Version Refactorisée)',
#         epilog="""EXEMPLES D'UTILISATION:

def parse_arguments():
    """Parse les arguments de ligne de commande"""

    parser = argparse.ArgumentParser(
        description="""GEMAUT - Génération de Modèles Automatiques de Terrain (Version Refactorisée)
Auteur: Nicolas Champion - nicolas.champion@ign.fr""",
        epilog="""EXEMPLES D'UTILISATION:

1. Avec fichier de configuration YAML (recommandé):
   gemaut --config config.yaml

2. Avec arguments de ligne de commande:
   gemaut --mns /chem/vers/MNS_in.tif --out /chem/vers/MNT.tif --reso 4 --cpu 24 --RepTra /chem/vers/RepTra [--sigma 0.5] [--regul 0.01] [--tile 300] [--pad 120] [--norme hubertukey] [--nodata_ext -32768] [--nodata_int -32767] [--init /chem/vers/MNS_in.tif] [--masque /chem/vers/MASQUE_GEMO.tif] [--groundval 0] [--mask-method saga|pdal] [--clean]

3. Créer un template de configuration:
   gemaut --create-config config.yaml

4. Calcul automatique de masque (si --masque n'est pas fourni):
   # Avec PDAL (défaut, algorithme CSF)
   gemaut --mns MNS.tif --out MNT.tif --reso 4 --cpu 24 --RepTra /tmp --mask-method pdal
   
   # Avec SAGA
   gemaut --mns MNS.tif --out MNT.tif --reso 4 --cpu 24 --RepTra /tmp --mask-method saga

IMPORTANT: Le MNS doit avoir des valeurs de no_data différentes pour les bords de chantier [no_data_ext] et les trous à l'intérieur du chantier [no_data_int] là où la corrélation a échoué par exemple
    
Any Questions, please contact me at nicolas.champion@ign.fr

""",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Groupe pour les modes d'exécution
    mode_group = parser.add_mutually_exclusive_group(required=False)
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
    
    # Méthode de calcul du masque si --masque n'est pas fourni
    parser.add_argument("--mask-method", choices=config.MASK_COMPUTATION_METHODS, 
                       default=config.DEFAULT_MASK_METHOD,
                       help=f"méthode de calcul du masque si --masque absent: {', '.join(config.MASK_COMPUTATION_METHODS)} (défaut: {config.DEFAULT_MASK_METHOD})")
    
    parser.add_argument("--nodata_ext", type=int, default=config.DEFAULT_NODATA_EXT, help="Valeur du no_data sur les bords")
    parser.add_argument("--nodata_int", type=int, default=config.DEFAULT_NODATA_INT, help="Valeur du no_data pour les trous")
    parser.add_argument("--sigma", type=float, default=config.DEFAULT_SIGMA, help="sigma / précision du Z MNS")
    parser.add_argument("--regul", type=float, default=config.DEFAULT_REGUL, help="regul / rigidité de la nappe")
    parser.add_argument("--tile", type=int, default=config.DEFAULT_TILE_SIZE, help="taille de la tuile")
    parser.add_argument("--pad", type=int, default=config.DEFAULT_PAD_SIZE, help="recouvrement entre tuiles")
    parser.add_argument("--norme", type=str, default=config.DEFAULT_NORME, help="choix entre les normes")
    parser.add_argument("--clean", action='store_true', help="supprimer les fichiers temporaires")
    parser.add_argument(
        "--verbose",
        action='store_true',
        help="activer le niveau DEBUG sur la console (les INFO/ERROR sont toujours affichés)",
    )
    
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
            from .config_manager import ConfigManager
            ConfigManager.create_template(args.create_config)
            print(f"Template de configuration créé: {args.create_config}")
            print("Modifiez ce fichier selon vos besoins, puis utilisez 'gemaut --config' pour l'exécuter.")
            return
        
        if args.config:
            # Mode fichier de configuration YAML
            from .config_manager import ConfigManager
            yaml_config = ConfigManager.load_config(args.config)
            ConfigManager.validate_config(yaml_config)
            config_obj = ConfigManager.convert_to_gemaut_config(yaml_config)
            # --verbose CLI prime sur le YAML
            if args.verbose:
                config_obj.verbose = True
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
                mask_method=args.mask_method,
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
