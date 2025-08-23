#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Démonstration de la vérification de compatibilité MNS/Masque
"""

import sys
import os
sys.path.append('.')

from image_utils import RasterProcessor
from loguru import logger

def demo_compatibility_check():
    """Démonstration de la fonctionnalité de vérification"""
    
    # Configuration des logs
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    print("🚀 DÉMONSTRATION - Vérification de Compatibilité MNS/Masque")
    print("=" * 70)
    
    # Exemple 1: Simulation d'une vérification réussie
    print("\n📋 Exemple 1: Vérification réussie")
    print("-" * 40)
    
    # Simulons des informations de fichiers compatibles
    print("✅ MNS et Masque sont compatibles:")
    print("   • Dimensions: 1000x1000 pixels")
    print("   • CRS: EPSG:2154 (Lambert-93)")
    print("   • Résolution: 1m")
    print("   • Étendue: Identique")
    
    # Exemple 2: Simulation d'une incompatibilité
    print("\n📋 Exemple 2: Incompatibilité détectée")
    print("-" * 40)
    
    print("❌ Problèmes détectés:")
    print("   • Hauteur différente: MNS=1000, Masque=800")
    print("   • CRS différent: MNS=EPSG:2154, Masque=EPSG:4326")
    print("   • Résolution différente: MNS=1m, Masque=5m")
    
    print("\n🔧 Actions recommandées:")
    print("   1. Rééchantillonner le masque à la résolution du MNS")
    print("   2. Reprojeter le masque dans le CRS du MNS")
    print("   3. Recadrer le masque sur l'étendue du MNS")
    
    # Exemple 3: Utilisation dans le pipeline
    print("\n📋 Exemple 3: Intégration dans le pipeline GEMAUT")
    print("-" * 40)
    
    print("Le pipeline vérifie automatiquement:")
    print("   • Au début: Si un fichier masque est fourni")
    print("   • Après calcul: Si le masque est calculé par SAGA")
    print("   • Arrêt automatique en cas d'incompatibilité")
    
    # Exemple 4: Code d'utilisation
    print("\n📋 Exemple 4: Code d'utilisation")
    print("-" * 40)
    
    code_example = '''
# Import de la fonction
from image_utils import RasterProcessor

# Vérification de compatibilité
compatible, details = RasterProcessor.validate_raster_compatibility(
    mns_path, 
    mask_path
)

if not compatible:
    print("❌ Incompatibilité détectée:")
    for issue in details['issues']:
        print(f"  - {issue}")
    # Arrêter le traitement
    raise ValueError("MNS et Masque incompatibles")
else:
    print("✅ Compatibilité validée")
    print(f"  Dimensions: {details['mns_info']['width']}x{details['mns_info']['height']}")
    print(f"  CRS: {details['mns_info']['crs']}")
'''
    
    print(code_example)
    
    # Exemple 5: Messages du pipeline
    print("\n📋 Exemple 5: Messages du pipeline GEMAUT")
    print("-" * 40)
    
    print("Messages de succès:")
    print("  ✅ Compatibilité MNS/Masque validée")
    print("  ✅ Compatibilité validée après calcul du masque")
    
    print("\nMessages d'erreur:")
    print("  ❌ INCOMPATIBILITÉ DÉTECTÉE entre le MNS et le masque!")
    print("  ❌ Le masque calculé n'est pas compatible avec le MNS")
    
    print("\n" + "=" * 70)
    print("🎯 La vérification de compatibilité est maintenant intégrée au pipeline!")
    print("   Elle s'exécute automatiquement et arrête le traitement en cas de problème.")
    print("   Cela évite les erreurs en cours de traitement et améliore la robustesse.")

if __name__ == "__main__":
    demo_compatibility_check() 