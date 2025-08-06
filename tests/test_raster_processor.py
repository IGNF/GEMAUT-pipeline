#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests unitaires pour RasterProcessor
Exemple simple pour comprendre les tests unitaires
"""

import unittest
import numpy as np
import rasterio
import tempfile
import os
from rasterio.transform import from_origin

# Import de la classe à tester
import sys
sys.path.append('..')  # Pour pouvoir importer les modules du projet
from image_utils import RasterProcessor


class TestRasterProcessor(unittest.TestCase):
    """Tests unitaires pour la classe RasterProcessor"""
    
    def setUp(self):
        """Méthode appelée avant chaque test - prépare les données de test"""
        # Créer un fichier raster temporaire pour les tests
        self.temp_dir = tempfile.mkdtemp()
        self.test_raster_path = os.path.join(self.temp_dir, "test_raster.tif")
        
        # Créer des données de test
        self.test_data = np.array([
            [1.0, 2.0, 3.0, -9999.0],  # -9999 = no_data
            [4.0, 5.0, 6.0, 7.0],
            [8.0, -9999.0, 10.0, 11.0],
            [12.0, 13.0, 14.0, 15.0]
        ], dtype=np.float32)
        
        # Sauvegarder le raster de test
        profile = {
            'driver': 'GTiff',
            'height': 4,
            'width': 4,
            'count': 1,
            'dtype': 'float32',
            'crs': 'EPSG:4326',
            'transform': from_origin(0, 4, 1, 1),
            'nodata': -9999.0
        }
        
        with rasterio.open(self.test_raster_path, 'w', **profile) as dst:
            dst.write(self.test_data, 1)
    
    def tearDown(self):
        """Méthode appelée après chaque test - nettoie les fichiers temporaires"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_image_dimensions(self):
        """Test de la méthode get_image_dimensions"""
        # Arrange (préparer) - déjà fait dans setUp()
        
        # Act (agir) - appeler la méthode à tester
        height, width = RasterProcessor.get_image_dimensions(self.test_raster_path)
        
        # Assert (vérifier) - vérifier que le résultat est correct
        self.assertEqual(height, 4, "La hauteur devrait être 4")
        self.assertEqual(width, 4, "La largeur devrait être 4")
    
    def test_get_image_info(self):
        """Test de la méthode get_image_info"""
        # Act
        info = RasterProcessor.get_image_info(self.test_raster_path)
        
        # Assert
        self.assertEqual(info['height'], 4)
        self.assertEqual(info['width'], 4)
        self.assertEqual(info['dtype'], 'float32')
        self.assertEqual(info['nodata'], -9999.0)
        self.assertIn('crs', info)
        self.assertIn('transform', info)
        self.assertIn('bounds', info)
    
    def test_contains_valid_data_with_valid_data(self):
        """Test de contains_valid_data avec des données valides"""
        # Act
        has_valid_data = RasterProcessor.contains_valid_data(self.test_raster_path, -9999.0)
        
        # Assert
        self.assertTrue(has_valid_data, "Le raster devrait contenir des données valides")
    
    def test_contains_valid_data_with_only_nodata(self):
        """Test de contains_valid_data avec seulement des no_data"""
        # Arrange - créer un raster avec seulement des no_data
        nodata_raster_path = os.path.join(self.temp_dir, "nodata_raster.tif")
        nodata_data = np.full((2, 2), -9999.0, dtype=np.float32)
        
        profile = {
            'driver': 'GTiff',
            'height': 2,
            'width': 2,
            'count': 1,
            'dtype': 'float32',
            'crs': 'EPSG:4326',
            'transform': from_origin(0, 2, 1, 1),
            'nodata': -9999.0
        }
        
        with rasterio.open(nodata_raster_path, 'w', **profile) as dst:
            dst.write(nodata_data, 1)
        
        # Act
        has_valid_data = RasterProcessor.contains_valid_data(nodata_raster_path, -9999.0)
        
        # Assert
        self.assertFalse(has_valid_data, "Le raster ne devrait contenir que des no_data")
    
    def test_get_image_dimensions_file_not_found(self):
        """Test de get_image_dimensions avec un fichier inexistant"""
        # Act & Assert
        with self.assertRaises(Exception):
            RasterProcessor.get_image_dimensions("fichier_inexistant.tif")
    
    def test_save_raster(self):
        """Test de la méthode save_raster"""
        # Arrange
        new_data = np.array([[100.0, 200.0], [300.0, 400.0]], dtype=np.float32)
        output_path = os.path.join(self.temp_dir, "output_raster.tif")
        
        profile = {
            'driver': 'GTiff',
            'height': 2,
            'width': 2,
            'count': 1,
            'dtype': 'float32',
            'crs': 'EPSG:4326',
            'transform': from_origin(0, 2, 1, 1),
            'nodata': -9999.0
        }
        
        # Act
        RasterProcessor.save_raster(new_data, output_path, profile)
        
        # Assert
        self.assertTrue(os.path.exists(output_path), "Le fichier devrait être créé")
        
        # Vérifier le contenu
        with rasterio.open(output_path) as src:
            saved_data = src.read(1)
            np.testing.assert_array_equal(saved_data, new_data)


# Tests d'intégration - tests plus complexes
class TestRasterProcessorIntegration(unittest.TestCase):
    """Tests d'intégration pour RasterProcessor"""
    
    def setUp(self):
        """Préparation pour les tests d'intégration"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après les tests d'intégration"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow(self):
        """Test d'un workflow complet : créer, analyser, modifier, sauvegarder"""
        # Arrange
        raster_path = os.path.join(self.temp_dir, "workflow_test.tif")
        
        # Créer un raster
        data = np.random.rand(10, 10).astype(np.float32)
        profile = {
            'driver': 'GTiff',
            'height': 10,
            'width': 10,
            'count': 1,
            'dtype': 'float32',
            'crs': 'EPSG:4326',
            'transform': from_origin(0, 10, 1, 1),
            'nodata': -9999.0
        }
        
        # Act - workflow complet
        RasterProcessor.save_raster(data, raster_path, profile)
        height, width = RasterProcessor.get_image_dimensions(raster_path)
        info = RasterProcessor.get_image_info(raster_path)
        has_valid_data = RasterProcessor.contains_valid_data(raster_path)
        
        # Assert
        self.assertEqual(height, 10)
        self.assertEqual(width, 10)
        self.assertTrue(has_valid_data)
        self.assertEqual(info['height'], 10)
        self.assertEqual(info['width'], 10)


if __name__ == '__main__':
    # Exécuter les tests
    unittest.main(verbosity=2) 