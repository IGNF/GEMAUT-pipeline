#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour vérifier la sauvegarde du masque brut SAGA
"""

import os
import shutil
from loguru import logger

def test_save_mask():
    """Test de sauvegarde du masque"""
    
    # Simuler un fichier masque
    work_dir = "test_save_mask"
    os.makedirs(work_dir, exist_ok=True)
    
    # Créer un fichier test
    test_file = os.path.join(work_dir, "test_mask.tif")
    with open(test_file, "w") as f:
        f.write("test content")
    
    # Sauvegarder le masque brut
    mask_brut_saga = os.path.join(work_dir, 'MASQUE_SAGA_BRUT_avant_correction.tif')
    shutil.copy2(test_file, mask_brut_saga)
    
    logger.info(f"💾 Masque SAGA brut sauvegardé: {mask_brut_saga}")
    logger.info(f"   Taille du fichier brut: {os.path.getsize(test_file)} octets")
    
    # Vérifier que le fichier existe
    if os.path.exists(mask_brut_saga):
        logger.info("✅ Fichier brut créé avec succès!")
    else:
        logger.error("❌ Fichier brut non créé!")
    
    # Lister les fichiers
    logger.info("Fichiers dans le répertoire:")
    for f in os.listdir(work_dir):
        logger.info(f"  - {f}")

if __name__ == "__main__":
    test_save_mask()

