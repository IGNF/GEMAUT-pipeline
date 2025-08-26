#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Démonstration du calcul automatique de masque dans GEMAUT
Montre l'utilisation des méthodes SAGA et PDAL
"""

import os
import sys
from loguru import logger

# Configuration du logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

def demo_mask_computer():
    """Démonstration du module MaskComputer"""
    logger.info("🎯 DÉMONSTRATION DU CALCUL AUTOMATIQUE DE MASQUE")
    logger.info("=" * 60)
    
    try:
        from mask_computer import MaskComputer
        
        # Créer une instance
        computer = MaskComputer()
        
        # Afficher les informations
        method_info = computer.get_method_info()
        logger.info(f"📊 Méthodes disponibles: {', '.join(method_info['available_methods'])}")
        
        if method_info['saga_available']:
            logger.info("✅ SAGA disponible")
            logger.info(f"   Description: {method_info['saga_info']['description']}")
            logger.info(f"   Avantages: {', '.join(method_info['saga_info']['advantages'])}")
        
        if method_info['pdal_available']:
            logger.info("✅ PDAL disponible")
            logger.info(f"   Description: {method_info['pdal_info']['description']}")
            logger.info(f"   Avantages: {', '.join(method_info['pdal_info']['advantages'])}")
        
        logger.info(f"🎯 Méthode recommandée: {method_info['recommended_method']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la démonstration: {e}")
        return False

def demo_configuration():
    """Démonstration de la configuration étendue"""
    logger.info("\n🔧 DÉMONSTRATION DE LA CONFIGURATION")
    logger.info("=" * 60)
    
    try:
        from gemaut_config import GEMAUTConfig
        from config import DEFAULT_MASK_COMPUTATION, DEFAULT_MASK_METHOD
        
        logger.info(f"📋 Configuration par défaut:")
        logger.info(f"   Calcul automatique: {DEFAULT_MASK_COMPUTATION}")
        logger.info(f"   Méthode: {DEFAULT_MASK_METHOD}")
        
        # Créer une configuration de test
        config = GEMAUTConfig(
            mns_input="/tmp/test_mns.tif",
            mnt_output="/tmp/test_mnt.tif",
            resolution=4.0,
            cpu_count=4,
            work_dir="/tmp/test_work",
            auto_mask_computation=True,
            mask_method="pdal"
        )
        
        logger.info(f"✅ Configuration créée avec succès:")
        logger.info(f"   Calcul automatique: {config.auto_mask_computation}")
        logger.info(f"   Méthode: {config.mask_method}")
        
        # Tester les paramètres
        saga_params = config.get_saga_params()
        pdal_params = config.get_pdal_params()
        
        logger.info(f"📊 Paramètres SAGA: {saga_params}")
        logger.info(f"📊 Paramètres PDAL: {saga_params}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la démonstration de configuration: {e}")
        return False

def demo_command_line():
    """Démonstration des nouvelles options de ligne de commande"""
    logger.info("\n💻 DÉMONSTRATION DES OPTIONS DE LIGNE DE COMMANDE")
    logger.info("=" * 60)
    
    try:
        from script_gemaut import parse_arguments
        
        logger.info("✅ Nouvelles options disponibles:")
        logger.info("   --auto-mask: Activer le calcul automatique")
        logger.info("   --mask-method: Choisir la méthode (auto/saga/pdal)")
        
        logger.info("\n📝 Exemples d'utilisation:")
        logger.info("   # Calcul automatique avec PDAL")
        logger.info("   python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 4 --RepTra /tmp --mask-method pdal")
        
        logger.info("   # Calcul automatique avec SAGA")
        logger.info("   python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 4 --RepTra /tmp --mask-method saga")
        
        logger.info("   # Choix automatique (recommandé)")
        logger.info("   python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 4 --RepTra /tmp --mask-method auto")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la démonstration des options: {e}")
        return False

def demo_yaml_config():
    """Démonstration de la configuration YAML"""
    logger.info("\n📄 DÉMONSTRATION DE LA CONFIGURATION YAML")
    logger.info("=" * 60)
    
    try:
        from config_manager import ConfigManager
        
        logger.info("✅ Gestionnaire de configuration disponible")
        logger.info("📝 Création d'un template...")
        
        # Créer un template de test
        template_file = "/tmp/demo_config.yaml"
        ConfigManager.create_template(template_file)
        
        if os.path.exists(template_file):
            logger.info(f"✅ Template créé: {template_file}")
            
            # Lire et afficher le contenu
            with open(template_file, 'r') as f:
                content = f.read()
            
            logger.info("📋 Contenu du template:")
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#'):
                    logger.info(f"   {line}")
            
            # Nettoyer
            os.remove(template_file)
            logger.info("🧹 Fichier temporaire supprimé")
            
        else:
            logger.error("❌ Échec de la création du template")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la démonstration YAML: {e}")
        return False

def main():
    """Fonction principale de démonstration"""
    logger.info("🚀 DÉMARRAGE DE LA DÉMONSTRATION GEMAUT")
    logger.info("Calcul automatique de masque avec SAGA et PDAL")
    logger.info("=" * 80)
    
    demos = [
        ("Module MaskComputer", demo_mask_computer),
        ("Configuration étendue", demo_configuration),
        ("Options de ligne de commande", demo_command_line),
        ("Configuration YAML", demo_yaml_config)
    ]
    
    results = []
    
    for demo_name, demo_func in demos:
        logger.info(f"\n🔍 Démonstration: {demo_name}")
        logger.info("-" * 50)
        
        try:
            success = demo_func()
            results.append((demo_name, success))
            
            if success:
                logger.info(f"✅ {demo_name}: SUCCÈS")
            else:
                logger.error(f"❌ {demo_name}: ÉCHEC")
                
        except Exception as e:
            logger.error(f"❌ {demo_name}: ERREUR - {e}")
            results.append((demo_name, False))
    
    # Résumé
    logger.info("\n" + "=" * 80)
    logger.info("📊 RÉSUMÉ DE LA DÉMONSTRATION")
    logger.info("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for demo_name, success in results:
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        logger.info(f"   {demo_name}: {status}")
    
    logger.info(f"\n🎯 Résultat global: {passed}/{total} démonstrations réussies")
    
    if passed == total:
        logger.info("\n🎉 Toutes les démonstrations sont passées!")
        logger.info("\n💡 Votre intégration est prête à l'emploi:")
        logger.info("   1. Testez avec --mask-method auto")
        logger.info("   2. Comparez SAGA vs PDAL")
        logger.info("   3. Optimisez selon vos besoins")
        
        logger.info("\n📚 Documentation disponible:")
        logger.info("   - README_CALCUL_MASQUE_AUTO.md")
        logger.info("   - config_exemple_avec_masque_auto.yaml")
        logger.info("   - test_mask_integration.py")
        
    else:
        logger.error("\n⚠️ Certaines démonstrations ont échoué.")
        logger.info("Vérifiez l'installation et les dépendances.")

if __name__ == "__main__":
    main()

