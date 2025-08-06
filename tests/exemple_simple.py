#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exemple très simple de tests unitaires
Pour comprendre les concepts de base
"""

import unittest


# Une fonction simple à tester
def addition(a, b):
    """Additionne deux nombres"""
    return a + b


def division(a, b):
    """Divise a par b"""
    if b == 0:
        raise ValueError("Division par zéro impossible")
    return a / b


# Classe de test
class TestCalculs(unittest.TestCase):
    """Tests pour les fonctions de calcul"""
    
    def setUp(self):
        """Appelé avant chaque test"""
        print("🔧 setUp() - Préparation des données")
        self.nombre1 = 10
        self.nombre2 = 5
    
    def tearDown(self):
        """Appelé après chaque test"""
        print("🧹 tearDown() - Nettoyage")
        # Ici on pourrait nettoyer des fichiers temporaires
    
    def test_addition_positifs(self):
        """Test de l'addition avec des nombres positifs"""
        print("  📝 Test: addition avec nombres positifs")
        
        # Act - appeler la fonction
        resultat = addition(self.nombre1, self.nombre2)
        
        # Assert - vérifier le résultat
        self.assertEqual(resultat, 15, "10 + 5 devrait donner 15")
    
    def test_addition_negatifs(self):
        """Test de l'addition avec des nombres négatifs"""
        print("  📝 Test: addition avec nombres négatifs")
        
        resultat = addition(-3, -7)
        self.assertEqual(resultat, -10, "-3 + (-7) devrait donner -10")
    
    def test_division_normale(self):
        """Test de la division normale"""
        print("  📝 Test: division normale")
        
        resultat = division(self.nombre1, self.nombre2)
        self.assertEqual(resultat, 2.0, "10 / 5 devrait donner 2.0")
    
    def test_division_par_zero(self):
        """Test de la division par zéro"""
        print("  📝 Test: division par zéro")
        
        # Vérifier qu'une exception est levée
        with self.assertRaises(ValueError):
            division(10, 0)


# Tests d'intégration
class TestWorkflow(unittest.TestCase):
    """Tests d'un workflow complet"""
    
    def test_workflow_complet(self):
        """Test d'un calcul complexe"""
        print("  📝 Test: workflow complet")
        
        # Calcul complexe : (a + b) / 2
        a, b = 10, 6
        somme = addition(a, b)
        moyenne = division(somme, 2)
        
        self.assertEqual(moyenne, 8.0, "Moyenne de 10 et 6 devrait être 8.0")


if __name__ == '__main__':
    print("🚀 Démarrage des tests unitaires")
    print("=" * 50)
    
    # Exécuter les tests avec verbosité maximale
    unittest.main(verbosity=2)
    
    print("=" * 50)
    print("✅ Tests terminés") 