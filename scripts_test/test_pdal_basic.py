#!/usr/bin/env python3
"""
Script de test de base pour PDAL
Teste l'installation et la fonctionnalité de base
"""

import sys

def test_pdal_installation():
    """Test que PDAL est installé et fonctionnel"""
    try:
        import pdal
        print(f"✅ PDAL installé avec succès")
        print(f"   Version: {pdal.__version__}")
        return True
    except ImportError as e:
        print(f"❌ PDAL non installé: {e}")
        print("   Installez avec: conda install -c conda-forge pdal pdal-python")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TESTS DE BASE PDAL")
    print("=" * 50)
    
    # Test 1: Installation
    if not test_pdal_installation():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Tests de base PDAL terminés")
    print("   PDAL est prêt pour les tests avancés !")

if __name__ == "__main__":
    main() 