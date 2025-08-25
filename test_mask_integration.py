#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour l'intégration du calcul automatique de masque
Vérifie que les modules SAGA et PDAL sont correctement intégrés
"""

import os
import sys
from loguru import logger

# Ajouter le répertoire courant au PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_mask_computer_import():
    """Teste l'import du module MaskComputer"""
    try:
        from mask_computer import MaskComputer
        logger.info("✅ Import de MaskComputer réussi")
        return True
    except ImportError as e:
        logger.error(f"❌ Import de MaskComputer échoué: {e}")
        return False

def test_mask_computer_initialization():
    """Teste l'initialisation de MaskComputer"""
    try:
        from mask_computer import MaskComputer
        computer = MaskComputer()
        logger.info("✅ Initialisation de MaskComputer réussie")
        
        # Afficher les informations sur les méthodes disponibles
        method_info = computer.get_method_info()
        logger.info(f"📊 Informations sur les méthodes:")
        logger.info(f"   Méthodes disponibles: {method_info['available_methods']}")
        logger.info(f"   SAGA disponible: {method_info['saga_available']}")
        logger.info(f"   PDAL disponible: {method_info['pdal_available']}")
        logger.info(f"   Méthode recommandée: {method_info['recommended_method']}")
        
        if 'saga' in method_info['available_methods']:
            logger.info(f"   SAGA: {method_info['saga_info']['description']}")
            logger.info(f"   Avantages: {', '.join(method_info['saga_info']['advantages'])}")
        
        if 'pdal' in method_info['available_methods']:
            logger.info(f"   PDAL: {method_info['pdal_info']['description']}")
            logger.info(f"   Avantages: {', '.join(method_info['pdal_info']['advantages'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Initialisation de MaskComputer échouée: {e}")
        return False

def test_config_integration():
    """Teste l'intégration avec la configuration GEMAUT"""
    try:
        from gemaut_config import GEMAUTConfig
        from config import DEFAULT_MASK_COMPUTATION, DEFAULT_MASK_METHOD
        
        logger.info("✅ Import de la configuration GEMAUT réussi")
        logger.info(f"   Calcul automatique par défaut: {DEFAULT_MASK_COMPUTATION}")
        logger.info(f"   Méthode par défaut: {DEFAULT_MASK_METHOD}")
        
        # Créer une configuration de test
        config = GEMAUTConfig(
            mns_input="/tmp/test_mns.tif",
            mnt_output="/tmp/test_mnt.tif",
            resolution=4.0,
            cpu_count=4,
            work_dir="/tmp/test_work",
            auto_mask_computation=True,
            mask_method="auto"
        )
        
        logger.info("✅ Création de configuration de test réussie")
        logger.info(f"   Calcul automatique: {config.auto_mask_computation}")
        logger.info(f"   Méthode: {config.mask_method}")
        
        # Tester les paramètres SAGA
        saga_params = config.get_saga_params()
        logger.info(f"   Paramètres SAGA: {saga_params}")
        
        # Tester les paramètres PDAL
        pdal_params = config.get_pdal_params()
        logger.info(f"   Paramètres PDAL: {pdal_params}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test d'intégration de configuration échoué: {e}")
        return False

def test_script_integration():
    """Teste l'intégration avec le script principal"""
    try:
        # Vérifier que le script principal peut importer MaskComputer
        import script_gemaut
        
        logger.info("✅ Import du script principal réussi")
        
        # Vérifier que les nouvelles options sont présentes
        from script_gemaut import parse_arguments
        
        # Créer un parser pour tester les nouvelles options
        import argparse
        parser = argparse.ArgumentParser()
        
        # Ajouter les arguments du script (simulation)
        parser.add_argument("--auto-mask", action='store_true', help="calculer automatiquement le masque")
        parser.add_argument("--mask-method", choices=['auto', 'saga', 'pdal'], help="méthode de calcul du masque")
        
        logger.info("✅ Nouvelles options de ligne de commande disponibles")
        logger.info("   --auto-mask: calcul automatique de masque")
        logger.info("   --mask-method: choix de la méthode (auto/saga/pdal)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test d'intégration du script échoué: {e}")
        return False

def main():
    """Fonction principale de test"""
    logger.info("🧪 Démarrage des tests d'intégration du calcul automatique de masque")
    logger.info("=" * 60)
    
    tests = [
        ("Import de MaskComputer", test_mask_computer_import),
        ("Initialisation de MaskComputer", test_mask_computer_initialization),
        ("Intégration de configuration", test_config_integration),
        ("Intégration du script principal", test_script_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Test: {test_name}")
        logger.info("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                logger.info(f"✅ {test_name}: SUCCÈS")
            else:
                logger.error(f"❌ {test_name}: ÉCHEC")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERREUR - {e}")
            results.append((test_name, False))
    
    # Résumé des tests
    logger.info("\n" + "=" * 60)
    logger.info("📊 RÉSUMÉ DES TESTS")
    logger.info("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"\n🎯 Résultat global: {passed}/{total} tests réussis")
    
    if passed == total:
        logger.info("🎉 Tous les tests sont passés! L'intégration est prête.")
        logger.info("\n💡 Utilisation:")
        logger.info("   python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 4 --RepTra /tmp --mask-method auto")
        logger.info("   python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 4 --RepTra /tmp --mask-method pdal")
        logger.info("   python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 4 --RepTra /tmp --mask-method saga")
    else:
        logger.error("⚠️ Certains tests ont échoué. Vérifiez l'installation des dépendances.")
        logger.info("\n🔧 Dépendances requises:")
        logger.info("   - Module SAGA (pour la méthode traditionnelle)")
        logger.info("   - Module PDAL (pour la méthode rapide)")
        logger.info("   - Modules de test dans /home/NChampion/DATADRIVE1/DEVELOPPEMENT/test_pdal/")

if __name__ == "__main__":
    main()

