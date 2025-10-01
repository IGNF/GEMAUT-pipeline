#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GEMAUT - Génération de Modèles Automatiques de Terrain
Package principal pour le traitement automatique des nuages de points LiDAR
"""

__version__ = "0.1.0"
__author__ = "Nicolas Champion"
__email__ = "nicolas.champion@ign.fr"

# Imports principaux pour faciliter l'utilisation du package
from .config import *
from .gemaut_config import GEMAUTConfig
from .script_gemaut import main, GEMAUTPipeline

__all__ = [
    'GEMAUTConfig',
    'GEMAUTPipeline',
    'main',
]

