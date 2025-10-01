#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire de configuration pour GEMAUT
Permet de charger les paramètres depuis un fichier YAML
"""

import yaml
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class GEMAUTConfigFromFile:
    """Configuration chargée depuis un fichier YAML"""
    
    # Paramètres d'entrée/sortie
    mns_file: str
    output_file: str
    work_dir: str
    mask_file: Optional[str] = None
    init_file: Optional[str] = None
    
    # Paramètres de traitement
    resolution: float = 4.0
    cpu_count: int = 8
    clean_temp: bool = False
    verbose: bool = False
    
    # Paramètres GEMO
    sigma: float = 0.5
    regul: float = 0.01
    norme: str = "hubertukey"
    
    # Paramètres de tuilage
    tile_size: int = 300
    pad_size: int = 120
    
    # Paramètres NoData
    nodata_ext: int = -32768
    nodata_int: int = -32767
    
    # Paramètres masque
    ground_value: int = 0
    
    # Paramètres SAGA
    saga_radius: int = 100
    saga_tile: int = 100
    saga_pente: int = 15
    
    # Paramètres de calcul automatique de masque
    auto_mask_computation: bool = True
    mask_method: str = 'auto'


class ConfigManager:
    """Gestionnaire de configuration YAML"""
    
    @staticmethod
    def load_config(config_file: str) -> GEMAUTConfigFromFile:
        """Charge la configuration depuis un fichier YAML"""
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
            
            # Extraire les paramètres avec valeurs par défaut
            input_data = config_data.get('input', {})
            processing_data = config_data.get('processing', {})
            gemo_data = config_data.get('gemo', {})
            tiling_data = config_data.get('tiling', {})
            nodata_data = config_data.get('nodata', {})
            mask_data = config_data.get('mask', {})
            saga_data = config_data.get('saga', {})
            mask_computation_data = config_data.get('mask_computation', {})
            pdal_data = config_data.get('pdal', {})
            
            return GEMAUTConfigFromFile(
                # Paramètres d'entrée/sortie
                mns_file=input_data.get('mns_file'),
                output_file=input_data.get('output_file'),
                work_dir=input_data.get('work_dir'),
                mask_file=input_data.get('mask_file'),
                init_file=input_data.get('init_file'),
                
                # Paramètres de traitement
                resolution=processing_data.get('resolution', 4.0),
                cpu_count=processing_data.get('cpu_count', 8),
                clean_temp=processing_data.get('clean_temp', False),
                verbose=processing_data.get('verbose', False),
                
                # Paramètres GEMO
                sigma=gemo_data.get('sigma', 0.5),
                regul=gemo_data.get('regul', 0.01),
                norme=gemo_data.get('norme', 'hubertukey'),
                
                # Paramètres de tuilage
                tile_size=tiling_data.get('tile_size', 300),
                pad_size=tiling_data.get('pad_size', 120),
                
                # Paramètres NoData
                nodata_ext=nodata_data.get('external', -32768),
                nodata_int=nodata_data.get('internal', -32767),
                
                # Paramètres masque
                ground_value=mask_data.get('ground_value', 0),
                
                # Paramètres SAGA
                saga_radius=saga_data.get('radius', 100),
                saga_tile=saga_data.get('tile', 100),
                saga_pente=saga_data.get('pente', 15),
                
                # Paramètres de calcul automatique de masque
                auto_mask_computation=mask_computation_data.get('auto_computation', True),
                mask_method=mask_computation_data.get('method', 'auto')
            )
            
        except FileNotFoundError:
            logger.error(f"Fichier de configuration introuvable: {config_file}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Erreur de syntaxe YAML dans {config_file}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            raise
    
    @staticmethod
    def create_template(config_file: str) -> None:
        """Crée un fichier de configuration template"""
        template_config = {
            'input': {
                'mns_file': '/chemin/vers/MNS.tif',
                'mask_file': None,
                'init_file': None,
                'output_file': '/chemin/vers/MNT.tif',
                'work_dir': '/chemin/vers/RepTra'
            },
            'processing': {
                'resolution': 4.0,
                'cpu_count': 8,
                'clean_temp': False,
                'verbose': False
            },
            'gemo': {
                'sigma': 0.5,
                'regul': 0.01,
                'norme': 'hubertukey'
            },
            'tiling': {
                'tile_size': 300,
                'pad_size': 120
            },
            'nodata': {
                'external': -32768,
                'internal': -32767
            },
            'mask': {
                'ground_value': 0
            },
            'saga': {
                'radius': 100,
                'tile': 100,
                'pente': 15
            },
            'mask_computation': {
                'auto_computation': True,
                'method': 'auto'
            },
            'pdal': {
                'csf': {
                    'max_iterations': 500,
                    'class_threshold': 0.8,
                    'cell_size': 2.0,
                    'time_step': 0.8,
                    'rigidness': 5,
                    'hdiff': 0.2,
                    'smooth': True
                }
            }
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as file:
                yaml.dump(template_config, file, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            logger.info(f"Template de configuration créé: {config_file}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du template: {e}")
            raise
    
    @staticmethod
    def validate_config(config: GEMAUTConfigFromFile) -> None:
        """Valide la configuration chargée"""
        errors = []
        
        # Vérifier les fichiers obligatoires
        if not config.mns_file:
            errors.append("mns_file est obligatoire")
        elif not os.path.exists(config.mns_file):
            errors.append(f"Fichier MNS introuvable: {config.mns_file}")
        
        if not config.output_file:
            errors.append("output_file est obligatoire")
        
        if not config.work_dir:
            errors.append("work_dir est obligatoire")
        
        # Vérifier les paramètres numériques
        if config.resolution <= 0:
            errors.append("resolution doit être positive")
        
        if config.cpu_count < 1:
            errors.append("cpu_count doit être positif")
        
        if config.sigma <= 0:
            errors.append("sigma doit être positif")
        
        if config.regul <= 0:
            errors.append("regul doit être positif")
        
        if config.tile_size < 1:
            errors.append("tile_size doit être positif")
        
        if config.pad_size < 0:
            errors.append("pad_size doit être positif ou nul")
        
        if config.pad_size >= config.tile_size:
            errors.append("pad_size doit être inférieur à tile_size")
        
        # Afficher les erreurs
        if errors:
            error_msg = "Erreurs de configuration:\n" + "\n".join(f"  - {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validée avec succès")
    
    @staticmethod
    def convert_to_gemaut_config(config: GEMAUTConfigFromFile):
        """Convertit la configuration YAML en GEMAUTConfig"""
        from .gemaut_config import GEMAUTConfig
        
        return GEMAUTConfig(
            mns_input=config.mns_file,
            mnt_output=config.output_file,
            resolution=config.resolution,
            cpu_count=config.cpu_count,
            work_dir=config.work_dir,
            mask_file=config.mask_file,
            ground_value=config.ground_value,
            init_file=config.init_file,
            auto_mask_computation=getattr(config, 'auto_mask_computation', True),
            mask_method=getattr(config, 'mask_method', 'auto'),
            nodata_ext=config.nodata_ext,
            nodata_int=config.nodata_int,
            sigma=config.sigma,
            regul=config.regul,
            tile_size=config.tile_size,
            pad_size=config.pad_size,
            norme=config.norme,
            clean_temp=config.clean_temp,
            verbose=config.verbose
        ) 