#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour la vérification de compatibilité MNS/Masque
"""

import sys
import os
sys.path.append('.')

from image_utils import RasterProcessor
from loguru import logger

def test_compatibility_check():
    """Test de la fonction de vérification de compatibilité"""
    
    # Configuration des logs
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    print("=== Test de vérification de compatibilité MNS/Masque ===\n")
    
    # Test 1: Vérification avec des fichiers existants (si disponibles)
    test_files = [
        ("MNS_example.tif", "mask_example.tif"),
        ("test_mns.tif", "test_mask.tif"),
        ("sample_dem.tif", "sample_mask.tif")
    ]
    
    for mns_file, mask_file in test_files:
        if os.path.exists(mns_file) and os.path.exists(mask_file):
            print(f"Test avec {mns_file} et {mask_file}:")
            try:
                compatible, details = RasterProcessor.validate_raster_compatibility(mns_file, mask_file)
                if compatible:
                    print(f"  ✅ Compatible: {details['mns_info']['width']}x{details['mns_info']['height']}")
                else:
                    print(f"  ❌ Incompatible:")
                    for issue in details['issues']:
                        print(f"    - {issue}")
            except Exception as e:
                print(f"  ⚠️ Erreur: {e}")
            print()
    
    # Test 2: Test avec des fichiers inexistants (gestion d'erreur)
    print("Test avec fichiers inexistants:")
    try:
        compatible, details = RasterProcessor.validate_raster_compatibility(
            "fichier_inexistant.tif", 
            "autre_fichier_inexistant.tif"
        )
    except Exception as e:
        print(f"  ✅ Gestion d'erreur correcte: {e}")
    print()
    
    # Test 3: Affichage des informations d'un fichier existant
    existing_files = [f for f in ["MNS_example.tif", "test_mns.tif", "sample_dem.tif"] if os.path.exists(f)]
    if existing_files:
        test_file = existing_files[0]
        print(f"Informations du fichier {test_file}:")
        try:
            info = RasterProcessor.get_image_info(test_file)
            print(f"  Dimensions: {info['width']}x{info['height']}")
            print(f"  CRS: {info['crs']}")
            print(f"  Type: {info['dtype']}")
            print(f"  NoData: {info['nodata']}")
        except Exception as e:
            print(f"  ⚠️ Erreur: {e}")
    
    print("\n=== Test terminé ===")

if __name__ == "__main__":
    test_compatibility_check() 