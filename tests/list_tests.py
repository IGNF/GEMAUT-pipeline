#!/usr/bin/env python3
"""
Script pour lister tous les tests disponibles dans le projet GEMAUT
"""

import unittest
import os
import sys

def list_all_tests():
    """Liste tous les tests disponibles"""
    
    # Ajouter le répertoire parent au path pour importer les modules
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Découvrir tous les tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test*.py')
    
    print("🧪 SUITE DE TESTS GEMAUT - INVENTAIRE COMPLET")
    print("=" * 60)
    
    test_count = 0
    class_count = 0
    
    for test_suite in suite:
        for test_case in test_suite:
            if hasattr(test_case, '_tests'):
                for test in test_case._tests:
                    if hasattr(test, '_tests'):
                        # C'est une classe de test
                        class_name = test.__class__.__name__
                        class_count += 1
                        print(f"\n📚 CLASSE: {class_name}")
                        print("-" * 40)
                        
                        # Lister les méthodes de test
                        for method in test._tests:
                            if hasattr(method, '_testMethodName'):
                                test_name = method._testMethodName
                                test_count += 1
                                print(f"  🧪 {test_name}")
                    else:
                        # C'est un test individuel
                        test_name = test._testMethodName
                        test_count += 1
                        print(f"  🧪 {test_name}")
    
    print("\n" + "=" * 60)
    print(f"📊 RÉSUMÉ:")
    print(f"   📚 Classes de test: {class_count}")
    print(f"   🧪 Tests individuels: {test_count}")
    print(f"   📁 Fichiers de test: {len([f for f in os.listdir(start_dir) if f.startswith('test') and f.endswith('.py')])}")
    print("=" * 60)

if __name__ == '__main__':
    list_all_tests() 