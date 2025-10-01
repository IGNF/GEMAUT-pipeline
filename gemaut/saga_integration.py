#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module pour l'intégration avec SAGA
Gère le calcul automatique du masque sol/sursol avec SAGA
"""

import os
import subprocess
from loguru import logger
from typing import Dict
from SAGA.script_saga_ground_extraction import main_saga_ground_extraction


class SAGAIntegration:
    """Classe pour l'intégration avec SAGA"""
    
    @staticmethod
    def compute_mask_with_saga(mns_file: str, output_mask_file: str, 
                              saga_work_dir: str, cpu_count: int,
                              saga_params: Dict) -> None:
        """
        Calcule automatiquement le masque sol/sursol avec SAGA
        
        Args:
            mns_file: Chemin vers le fichier MNS
            output_mask_file: Chemin de sortie pour le masque
            saga_work_dir: Répertoire de travail pour SAGA
            cpu_count: Nombre de CPUs à utiliser
            saga_params: Paramètres SAGA (radius, tile, no_data_max, pente)
        """
        try:
            logger.info("Calcul automatique du masque avec SAGA")
            
            # Vérifier si le fichier de sortie existe déjà
            if os.path.isfile(output_mask_file):
                os.remove(output_mask_file)
                logger.info(f"Fichier {output_mask_file} supprimé: il va être recalculé")
            else:
                logger.info(f"Fichier {output_mask_file} n'existe pas: il va être recalculé")
            
            # Appeler le script SAGA
            main_saga_ground_extraction(
                mns_file,
                output_mask_file,
                saga_work_dir,
                cpu_count,
                saga_params['radius'],
                saga_params['tile'],
                saga_params['no_data_max'],
                saga_params['pente']
            )
            
            logger.info(f"Masque SAGA calculé avec succès: {output_mask_file}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur lors de l'exécution du script SAGA: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors du calcul du masque SAGA: {e}")
            raise
    
    @staticmethod
    def validate_saga_installation() -> bool:
        """Vérifie si SAGA est correctement installé"""
        try:
            # Tenter d'exécuter une commande SAGA simple
            result = subprocess.run(['saga_cmd', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("SAGA détecté et fonctionnel")
                return True
            else:
                logger.warning("SAGA détecté mais retourne un code d'erreur")
                return False
        except FileNotFoundError:
            logger.error("SAGA non trouvé dans le PATH")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Timeout lors de la vérification de SAGA")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de SAGA: {e}")
            return False
    
    @staticmethod
    def get_saga_version() -> str:
        """Obtient la version de SAGA installée"""
        try:
            result = subprocess.run(['saga_cmd', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "Version inconnue"
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention de la version SAGA: {e}")
            return "Version inconnue"
    
    @staticmethod
    def check_saga_dependencies() -> Dict[str, bool]:
        """Vérifie les dépendances SAGA nécessaires"""
        dependencies = {
            'saga_cmd': False,
            'gdal': False,
            'python_saga': False
        }
        
        # Vérifier saga_cmd
        try:
            result = subprocess.run(['saga_cmd', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            dependencies['saga_cmd'] = result.returncode == 0
        except:
            pass
        
        # Vérifier gdal
        try:
            result = subprocess.run(['gdalinfo', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            dependencies['gdal'] = result.returncode == 0
        except:
            pass
        
        # Vérifier python_saga (module SAGA)
        try:
            import SAGA
            dependencies['python_saga'] = True
        except ImportError:
            pass
        
        return dependencies
    
    @staticmethod
    def log_saga_environment() -> None:
        """Enregistre les informations sur l'environnement SAGA"""
        logger.info("=== Informations environnement SAGA ===")
        
        # Version SAGA
        saga_version = SAGAIntegration.get_saga_version()
        logger.info(f"SAGA version: {saga_version}")
        
        # Dépendances
        dependencies = SAGAIntegration.check_saga_dependencies()
        logger.info("Dépendances SAGA:")
        for dep, available in dependencies.items():
            status = "✓" if available else "✗"
            logger.info(f"  {status} {dep}")
        
        # Variables d'environnement importantes
        env_vars = ['SAGA_MLB', 'SAGA_TLB', 'GDAL_DATA', 'PROJ_LIB']
        logger.info("Variables d'environnement:")
        for var in env_vars:
            value = os.environ.get(var, "Non définie")
            logger.info(f"  {var}: {value}")
        
        logger.info("========================================") 