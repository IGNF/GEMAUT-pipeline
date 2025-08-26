#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Démonstration des différences entre masque SAGA brut et corrigé
"""

import os
import sys
from loguru import logger

def demo_masque_saga():
    """Démonstration des masques SAGA"""
    
    logger.info("🎯 DÉMONSTRATION DES MASQUES SAGA")
    logger.info("=" * 50)
    
    # Répertoires de test
    test_dirs = [
        "RepTra_ground_mask_SAGA_v9",
        "RepTra_ground_mask_SAGA_v8", 
        "RepTra_ground_mask_SAGA_v7",
        "RepTra_ground_mask_SAGA_v6",
        "RepTra_ground_mask_SAGA_v5",
        "RepTra_ground_mask_SAGA_v4"
    ]
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            logger.info(f"\n📁 Répertoire: {test_dir}")
            logger.info("-" * 30)
            
            # Lister les fichiers
            files = os.listdir(test_dir)
            mask_files = [f for f in files if f.startswith("MASQUE")]
            
            if mask_files:
                logger.info("Fichiers masque trouvés:")
                for f in mask_files:
                    file_path = os.path.join(test_dir, f)
                    size = os.path.getsize(file_path)
                    logger.info(f"  📄 {f} ({size} octets)")
                    
                    # Vérifier le type de masque
                    if "BRUT" in f:
                        logger.info("     → Masque SAGA BRUT (avant correction géographique)")
                        logger.info("     → Contient les différences géographiques originales")
                    elif "CORRIGE" in f:
                        logger.info("     → Masque SAGA CORRIGÉ (après correction géographique)")
                        logger.info("     → Géographiquement aligné avec le MNS")
                    else:
                        logger.info("     → Masque principal (utilisé par le pipeline)")
            else:
                logger.info("❌ Aucun fichier masque trouvé")
        else:
            logger.info(f"❌ Répertoire {test_dir} non trouvé")
    
    logger.info("\n" + "=" * 50)
    logger.info("💡 EXPLICATION DES DIFFÉRENCES:")
    logger.info("")
    logger.info("1. MASQUE_SAGA_BRUT_avant_correction.tif:")
    logger.info("   - Généré directement par SAGA")
    logger.info("   - Peut avoir des différences géographiques avec le MNS")
    logger.info("   - Transformation géographique légèrement différente")
    logger.info("   - Bornes géographiques peuvent varier")
    logger.info("")
    logger.info("2. MASQUE_SAGA_CORRIGE_apres_correction.tif:")
    logger.info("   - Masque après rééchantillonnage par GDAL")
    logger.info("   - Géographiquement aligné avec le MNS")
    logger.info("   - Utilisé par la suite du pipeline GEMAUT")
    logger.info("")
    logger.info("3. MASQUE_compute.tif:")
    logger.info("   - Masque principal utilisé par le pipeline")
    logger.info("   - Peut être brut ou corrigé selon l'étape")

if __name__ == "__main__":
    demo_masque_saga()

