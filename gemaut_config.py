#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe de configuration pour GEMAUT
Gère tous les paramètres et constantes du pipeline
"""

import os
from dataclasses import dataclass
from typing import Optional
import config


@dataclass
class GEMAUTConfig:
    """Configuration centralisée pour le pipeline GEMAUT"""
    
    # Paramètres d'entrée/sortie
    mns_input: str
    mnt_output: str
    resolution: float
    cpu_count: int
    work_dir: str
    
    # Paramètres optionnels
    mask_file: Optional[str] = None
    ground_value: int = 0
    init_file: Optional[str] = None
    nodata_ext: int = config.DEFAULT_NODATA_EXT
    nodata_int: int = config.DEFAULT_NODATA_INT
    
    # Paramètres GEMO
    sigma: float = config.DEFAULT_SIGMA
    regul: float = config.DEFAULT_REGUL
    tile_size: int = config.DEFAULT_TILE_SIZE
    pad_size: int = config.DEFAULT_PAD_SIZE
    norme: str = config.DEFAULT_NORME
    
    # Paramètres SAGA
    radius_saga: int = config.RADIUS_SAGA
    tile_saga: int = config.TILE_SAGA
    pente_saga: int = config.PENTE_SAGA
    
    # Paramètres internes
    nodata_interne_mask: int = config.NODATA_INTERNE_MASK
    nodata_max: int = config.NODATA_MAX
    
    # Options de traitement
    clean_temp: bool = False
    verbose: bool = False
    
    def __post_init__(self):
        """Validation et initialisation post-création"""
        self._validate_inputs()
        self._setup_paths()
    
    def _validate_inputs(self):
        """Valide les paramètres d'entrée"""
        if not os.path.exists(self.mns_input):
            raise FileNotFoundError(f"Fichier MNS introuvable: {self.mns_input}")
        
        if self.mask_file and not os.path.exists(self.mask_file):
            raise FileNotFoundError(f"Fichier masque introuvable: {self.mask_file}")
        
        if self.init_file and not os.path.exists(self.init_file):
            raise FileNotFoundError(f"Fichier d'initialisation introuvable: {self.init_file}")
        
        if self.cpu_count < 1:
            raise ValueError(f"Nombre de CPU invalide: {self.cpu_count}")
        
        if self.resolution <= 0:
            raise ValueError(f"Résolution invalide: {self.resolution}")
    
    def _setup_paths(self):
        """Configure les chemins de fichiers temporaires"""
        self.tmp_dir = os.path.join(self.work_dir, config.TEMP_DIRS['tmp'])
        self.saga_dir = os.path.join(self.tmp_dir, config.TEMP_DIRS['saga'])
        
        # Chemins des fichiers temporaires
        self.temp_files = {
            'mns_sans_trou': os.path.join(self.tmp_dir, config.TEMP_FILES['mns_sans_trou']),
            'mns4saga': os.path.join(self.tmp_dir, config.TEMP_FILES['mns4saga']),
            'mns_sous_ech': os.path.join(self.tmp_dir, config.TEMP_FILES['mns_sous_ech']),
            'masque_4gemo': os.path.join(self.tmp_dir, config.TEMP_FILES['masque_4gemo']),
            'masque_nodata': os.path.join(self.tmp_dir, config.TEMP_FILES['masque_nodata']),
            'masque_sous_ech': os.path.join(self.tmp_dir, config.TEMP_FILES['masque_sous_ech']),
            'mnt_out_tmp': os.path.join(self.tmp_dir, config.TEMP_FILES['mnt_out_tmp']),
            'init_sous_ech': os.path.join(self.tmp_dir, config.TEMP_FILES['init_sous_ech'])
        }
    
    def get_tile_dimensions(self):
        """Retourne les dimensions des tuiles"""
        return (self.tile_size, self.tile_size)
    
    def get_gemo_params(self):
        """Retourne les paramètres pour GEMO"""
        return {
            'sigma': self.sigma,
            'lambda': self.regul,
            'norme': self.norme,
            'no_data_value': self.nodata_ext
        }
    
    def get_saga_params(self):
        """Retourne les paramètres pour SAGA"""
        return {
            'radius': self.radius_saga,
            'tile': self.tile_saga,
            'no_data_max': self.nodata_max,
            'pente': self.pente_saga
        }
    
    def create_directories(self):
        """Crée les répertoires nécessaires"""
        os.makedirs(self.work_dir, exist_ok=True)
        os.makedirs(self.tmp_dir, exist_ok=True)
        os.makedirs(self.saga_dir, exist_ok=True)
    
    def get_log_file_path(self):
        """Génère le chemin du fichier de log"""
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return os.path.join(os.path.dirname(self.mnt_output), f"log_{timestamp}.txt")
    
    def to_dict(self):
        """Convertit la configuration en dictionnaire pour le logging"""
        return {
            'mns_input': self.mns_input,
            'mnt_output': self.mnt_output,
            'resolution': self.resolution,
            'cpu_count': self.cpu_count,
            'work_dir': self.work_dir,
            'mask_file': self.mask_file,
            'ground_value': self.ground_value,
            'init_file': self.init_file,
            'sigma': self.sigma,
            'regul': self.regul,
            'tile_size': self.tile_size,
            'pad_size': self.pad_size,
            'norme': self.norme,
            'clean_temp': self.clean_temp,
            'verbose': self.verbose
        } 