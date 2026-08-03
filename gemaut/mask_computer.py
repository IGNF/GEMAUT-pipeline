#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module pour le calcul automatique de masques sol/sursol
Supporte SAGA et PDAL comme méthodes d'extraction
"""

import os
import sys
import time
from loguru import logger
from typing import Dict, Optional, Tuple
import subprocess
from . import config

# Import des modules d'intégration existants
try:
    from .saga_integration import SAGAIntegration
    SAGA_AVAILABLE = True
except ImportError:
    SAGA_AVAILABLE = False
    logger.warning("Module SAGA non disponible")

try:
    # Import direct de PDAL sans dépendre d'un chemin codé en dur
    from .pdal_integration import PDALIntegration
    PDAL_AVAILABLE = True
except ImportError:
    PDAL_AVAILABLE = False
    logger.warning("⚠️ Module PDAL non disponible")


class MaskComputer:
    """Classe pour le calcul automatique de masques avec différentes méthodes"""
    
    def __init__(self):
        """Initialise le calculateur de masques"""
        self.available_methods = self._check_available_methods()
        logger.debug(f"Méthodes disponibles: {', '.join(self.available_methods)}")
    
    def _check_available_methods(self) -> list:
        """Vérifie quelles méthodes sont disponibles"""
        methods = []
        
        if SAGA_AVAILABLE:
            try:
                saga_instance = SAGAIntegration()
                if saga_instance.validate_saga_installation():
                    methods.append('saga')
                    logger.debug("SAGA disponible et fonctionnel")
                else:
                    logger.warning("⚠️ SAGA détecté mais non fonctionnel")
            except Exception as e:
                logger.warning(f"⚠️ SAGA non fonctionnel: {e}")
        else:
            logger.warning("⚠️ Module SAGA non disponible")
        
        if PDAL_AVAILABLE:
            try:
                pdal_instance = PDALIntegration()
                if pdal_instance._check_pdal_available():
                    methods.append('pdal')
                    logger.debug("PDAL disponible et fonctionnel")
                else:
                    logger.warning("⚠️ PDAL détecté mais non fonctionnel")
            except Exception as e:
                logger.warning(f"⚠️ PDAL non fonctionnel: {e}")
        else:
            logger.warning("⚠️ Module PDAL non disponible")
        
        if not methods:
            logger.error("❌ Aucune méthode d'extraction disponible!")
            logger.error("Veuillez installer SAGA ou PDAL pour continuer")
        
        return methods
    
    def compute_mask(self, mns_file: str, output_mask_file: str, 
                    work_dir: str, method: str = 'pdal',
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
        
        logger.debug(f"Calcul du masque avec {method.upper()}")
        logger.debug(f"MNS: {mns_file}")
        logger.debug(f"Sortie: {output_mask_file}")
        logger.debug(f"Paramètres: {params}")
        
        start_time = time.time()
        
        try:
            if method == 'saga':
                mask_file = self._compute_with_saga(mns_file, output_mask_file, work_dir, cpu_count, params)
            elif method == 'pdal':
                mask_file = self._compute_with_pdal(mns_file, output_mask_file, work_dir, cpu_count, params)
            else:
                raise ValueError(f"Méthode non supportée: {method}")
            
            execution_time = time.time() - start_time
            logger.debug(f"Masque calculé en {execution_time:.2f}s")
            logger.debug(f"Fichier généré: {mask_file}")
            
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
                'csf_max_iterations': config.PDAL_CSF_MAX_ITERATIONS,      # 500
                'csf_class_threshold': config.PDAL_CSF_CLASS_THRESHOLD,    # 0.8
                'csf_cell_size': config.PDAL_CSF_CELL_SIZE,               # 2.0
                'csf_time_step': config.PDAL_CSF_TIME_STEP,               # 0.8
                'csf_rigidness': config.PDAL_CSF_RIGIDNESS,               # 5
                'csf_hdiff': config.PDAL_CSF_HDIFF,                       # 0.2
                'csf_smooth': config.PDAL_CSF_SMOOTH,                     # True
            }
        else:
            raise ValueError(f"Méthode non supportée: {method}")
    
    def _compute_with_saga(self, mns_file: str, output_mask_file: str, 
                          work_dir: str, cpu_count: int, params: Dict) -> str:
        """Calcule le masque avec SAGA"""
        logger.debug("Utilisation de SAGA pour l'extraction...")
        
        # Créer le répertoire de sortie si nécessaire
        os.makedirs(os.path.dirname(output_mask_file), exist_ok=True)
        
        # Calculer le masque avec la méthode statique
        SAGAIntegration.compute_mask_with_saga(
            mns_file=mns_file,
            output_mask_file=output_mask_file,
            saga_work_dir=work_dir,
            cpu_count=cpu_count,
            saga_params=params
        )
        
        return output_mask_file
    
    def _compute_with_pdal(self, mns_file: str, output_mask_file: str, 
                          work_dir: str, cpu_count: int, params: Dict) -> str:
        """Calcule le masque avec PDAL"""
        logger.debug("Utilisation de PDAL pour l'extraction...")
        
        pdal_instance = PDALIntegration()
        
        # Créer le répertoire de sortie si nécessaire
        os.makedirs(os.path.dirname(output_mask_file), exist_ok=True)
        
        # Calculer le masque
        pdal_instance.compute_mask(
            mns_file=mns_file,
            output_mask_file=output_mask_file,
            work_dir=work_dir,
            cpu_count=cpu_count,
            params=params
        )
        
        return output_mask_file
    
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
                     method: str = 'pdal', cpu_count: int = 4, 
                     params: Optional[Dict] = None) -> str:
    """
    Fonction utilitaire pour calculer un masque automatiquement
    
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
    computer = MaskComputer()
    return computer.compute_mask(mns_file, output_mask_file, work_dir, method, cpu_count, params)
