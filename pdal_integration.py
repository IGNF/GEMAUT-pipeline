#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module pour l'intégration avec PDAL
Gère le calcul automatique du masque sol/sursol avec PDAL
"""

import os
import subprocess
from loguru import logger
from typing import Dict


class PDALIntegration:
    """Classe pour l'intégration avec PDAL"""
    
    def __init__(self):
        """Initialise l'intégration PDAL"""
        pass
    
    def _check_pdal_available(self) -> bool:
        """Vérifie si PDAL est disponible et fonctionnel"""
        try:
            # Tenter d'exécuter une commande PDAL simple
            result = subprocess.run(['pdal', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("PDAL détecté et fonctionnel")
                return True
            else:
                logger.warning("PDAL détecté mais retourne un code d'erreur")
                return False
        except FileNotFoundError:
            logger.error("PDAL non trouvé dans le PATH")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Timeout lors de la vérification de PDAL")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de PDAL: {e}")
            return False
    
    def compute_mask(self, mns_file: str, output_mask_file: str, 
                    work_dir: str, cpu_count: int, params: Dict) -> None:
        """
        Calcule automatiquement le masque sol/sursol avec PDAL
        
        Args:
            mns_file: Chemin vers le fichier MNS
            output_mask_file: Chemin de sortie pour le masque
            work_dir: Répertoire de travail pour PDAL
            cpu_count: Nombre de CPUs à utiliser
            params: Paramètres PDAL
        """
        try:
            logger.info("Calcul automatique du masque avec PDAL")
            logger.warning("⚠️ Implémentation PDAL non encore complète - Fallback vers SAGA")
            
            # Pour l'instant, on fait un fallback vers SAGA
            # TODO: Implémenter le vrai calcul PDAL
            from saga_integration import SAGAIntegration
            
            # Convertir les paramètres SAGA
            saga_params = {
                'radius': params.get('radius', 100.0),
                'tile': params.get('tile', 100),
                'no_data_max': params.get('no_data_max', -32768),
                'pente': params.get('pente', 15.0)
            }
            
            # Utiliser SAGA en fallback
            saga_instance = SAGAIntegration()
            saga_instance.compute_mask_with_saga(
                mns_file, output_mask_file, work_dir, cpu_count, saga_params
            )
            
            logger.info(f"Masque calculé avec SAGA (fallback): {output_mask_file}")
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du masque PDAL: {e}")
            raise
    
    @staticmethod
    def get_pdal_version() -> str:
        """Obtient la version de PDAL installée"""
        try:
            result = subprocess.run(['pdal', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "Version inconnue"
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention de la version PDAL: {e}")
            return "Version inconnue"
