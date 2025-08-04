#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration centralisée pour le script GEMAUT
Contient toutes les constantes et paramètres par défaut
"""

# Paramètres de traitement GEMO
DEFAULT_SIGMA = 0.5
DEFAULT_REGUL = 0.01
DEFAULT_TILE_SIZE = 300
DEFAULT_PAD_SIZE = 120
DEFAULT_NORME = "hubertukey"

# Valeurs NoData
DEFAULT_NODATA_EXT = -32768
DEFAULT_NODATA_INT = -32767
NODATA_INTERNE_MASK = 11
NODATA_MAX = 32768

# Paramètres SAGA
RADIUS_SAGA = 100
TILE_SAGA = 100
PENTE_SAGA = 15

# Paramètres de traitement des trous
DEFAULT_WEIGHT_TYPE = 1  # Distance Euclidienne
DEFAULT_EDGE_SIZE = 5

# Paramètres de géoréférencement
DEFAULT_CRS = "EPSG:4326"  # WGS84 par défaut

# Extensions de fichiers
FILE_EXTENSIONS = {
    'tif': '.tif',
    'tmp': '_tmp.tif',
    'filled': '_filled.tif',
    'nodata': '_nodata.tif',
    'sous_ech': '_SousEch.tif'
}

# Noms de fichiers temporaires
TEMP_FILES = {
    'mns_sans_trou': 'MNS_sans_trou.tif',
    'mns4saga': 'MNS4SAGA_nodata_max.tif',
    'mns_sous_ech': 'MNS_SousEch_tmp.tif',
    'masque_4gemo': 'MASQUE_4gemo.tif',
    'masque_nodata': 'MASQUE_nodata.tif',
    'masque_sous_ech': 'MASQUE_SousEch.tif',
    'mnt_out_tmp': 'OUT_MNT_tmp.tif',
    'init_sous_ech': 'INIT.tif'
}

# Répertoires temporaires
TEMP_DIRS = {
    'saga': 'RepTra_SAGA',
    'tmp': 'tmp'
}

# Paramètres de logging
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
LOG_LEVEL = "INFO"

# Paramètres de performance
DEFAULT_OMP_THREADS = '1'

# Messages d'information
INFO_MESSAGES = {
    'start': "Programme démarré à : {start_time}",
    'holes_filling': "Remplissage des trous dans MNS.",
    'nodata_replacement': "Remplacement des valeurs NoData max dans MNS.",
    'mask_computation': "Le masque n'a pas été fourni. Calcul à partir du MNS avec SAGA.",
    'mask_labeling': "Étiquetage et remplissage des valeurs NoData.",
    'nodata_management': "Gestion des valeurs NoData externes et internes.",
    'subsampling': "Sous-échantillonnage à la résolution de {reso} mètres.",
    'tiles_calculation': "Calcul du nombre de dalles.",
    'tiles_cutting': "Découpage des dalles pour chantier GEMO.",
    'gemo_execution': "Exécution parallèle de GEMO.",
    'final_assembly': "Raboutage final avec Rasterio.",
    'cleanup': "Nettoyage des fichiers temporaires effectué.",
    'end': "END"
}

# Messages d'erreur
ERROR_MESSAGES = {
    'saga_execution': "Erreur lors de l'exécution du script SAGA: {error}",
    'general': "Erreur: {error}"
} 