#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interface abstraite pour l'extraction de points au sol
Définit le contrat que doivent respecter toutes les implémentations
(SAGA, PDAL, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import os


class GroundExtractionInterface(ABC):
    """
    Interface abstraite pour l'extraction de points au sol
    Toutes les implémentations (SAGA, PDAL) doivent respecter ce contrat
    """
    
    @abstractmethod
    def compute_mask(self, mns_file: str, output_mask_file: str, 
                    work_dir: str, cpu_count: int,
                    params: Dict) -> None:
        """
        Calcule automatiquement le masque sol/sursol
        
        Args:
            mns_file: Chemin vers le fichier MNS
            output_mask_file: Chemin de sortie pour le masque
            work_dir: Répertoire de travail
            cpu_count: Nombre de CPUs à utiliser
            params: Paramètres spécifiques à l'implémentation
        """
        pass
    
    @abstractmethod
    def validate_installation(self) -> bool:
        """Vérifie si l'implémentation est correctement installée"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Obtient la version de l'implémentation installée"""
        pass
    
    @abstractmethod
    def check_dependencies(self) -> Dict[str, bool]:
        """Vérifie les dépendances nécessaires"""
        pass
    
    @abstractmethod
    def log_environment(self) -> None:
        """Enregistre les informations sur l'environnement"""
        pass
    
    def validate_input_file(self, mns_file: str) -> bool:
        """Valide le fichier MNS d'entrée"""
        if not os.path.exists(mns_file):
            raise FileNotFoundError(f"Fichier MNS introuvable: {mns_file}")
        
        if not mns_file.lower().endswith(('.tif', '.tiff')):
            raise ValueError(f"Le fichier MNS doit être au format GeoTIFF: {mns_file}")
        
        return True
    
    def validate_output_path(self, output_mask_file: str) -> bool:
        """Valide le chemin de sortie"""
        output_dir = os.path.dirname(output_mask_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        if not output_mask_file.lower().endswith(('.tif', '.tiff')):
            raise ValueError(f"Le fichier de sortie doit être au format GeoTIFF: {output_mask_file}")
        
        return True
    
    def validate_work_dir(self, work_dir: str) -> bool:
        """Valide et crée le répertoire de travail"""
        if not os.path.exists(work_dir):
            os.makedirs(work_dir, exist_ok=True)
        return True
    
    def validate_cpu_count(self, cpu_count: int) -> bool:
        """Valide le nombre de CPUs"""
        if cpu_count < 1:
            raise ValueError(f"Nombre de CPU invalide: {cpu_count}")
        return True
    
    def validate_params(self, params: Dict) -> bool:
        """Valide les paramètres spécifiques à l'implémentation"""
        required_params = self.get_required_params()
        for param in required_params:
            if param not in params:
                raise ValueError(f"Paramètre requis manquant: {param}")
        return True
    
    @abstractmethod
    def get_required_params(self) -> list:
        """Retourne la liste des paramètres requis"""
        pass
    
    def preprocess_input(self, mns_file: str, work_dir: str) -> str:
        """Préprocesse le fichier MNS d'entrée si nécessaire"""
        # Par défaut, retourne le fichier d'entrée tel quel
        # Les implémentations peuvent surcharger cette méthode
        return mns_file
    
    def postprocess_output(self, output_mask_file: str, work_dir: str) -> str:
        """Postprocesse le fichier de sortie si nécessaire"""
        # Par défaut, retourne le fichier de sortie tel quel
        # Les implémentations peuvent surcharger cette méthode
        return output_mask_file 