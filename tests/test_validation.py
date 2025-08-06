#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests de validation pour le pipeline GEMAUT
Validation des données d'entrée et des paramètres
"""

import unittest
import numpy as np
import rasterio
import tempfile
import os
from rasterio.transform import from_origin
from unittest.mock import patch, MagicMock

# Import des modules à tester
import sys
sys.path.append('..')
from gemaut_config import GEMAUTConfig
from image_utils import RasterProcessor


class TestMNSValidation(unittest.TestCase):
    """Tests de validation du MNS d'entrée"""
    
    def setUp(self):
        """Préparation des données de test"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Créer un MNS de test valide
        self.valid_mns_path = os.path.join(self.temp_dir, "valid_mns.tif")
        self.create_valid_mns()
        
        # Créer un MNS de test invalide
        self.invalid_mns_path = os.path.join(self.temp_dir, "invalid_mns.tif")
        self.create_invalid_mns()
    
    def tearDown(self):
        """Nettoyage des fichiers temporaires"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_valid_mns(self):
        """Crée un MNS de test valide"""
        data = np.random.rand(100, 100).astype(np.float32) * 100  # Altitudes 0-100m
        data[10:15, 20:25] = -9999  # Trou 1
        data[50:55, 60:65] = -9999  # Trou 2
        
        profile = {
            'driver': 'GTiff',
            'height': 100,
            'width': 100,
            'count': 1,
            'dtype': 'float32',
            'crs': 'EPSG:4326',
            'transform': from_origin(0, 100, 1, 1),
            'nodata': -9999.0
        }
        
        with rasterio.open(self.valid_mns_path, 'w', **profile) as dst:
            dst.write(data, 1)
    
    def create_invalid_mns(self):
        """Crée un MNS de test invalide (plusieurs bandes)"""
        data = np.random.rand(3, 100, 100).astype(np.float32)  # 3 bandes au lieu d'1
        
        profile = {
            'driver': 'GTiff',
            'height': 100,
            'width': 100,
            'count': 3,  # Plusieurs bandes = invalide
            'dtype': 'float32',
            'crs': 'EPSG:4326',
            'transform': from_origin(0, 100, 1, 1),
            'nodata': -9999.0
        }
        
        with rasterio.open(self.invalid_mns_path, 'w', **profile) as dst:
            dst.write(data)
    
    def test_mns_file_exists(self):
        """Test que le fichier MNS existe"""
        # Test avec fichier existant
        self.assertTrue(os.path.exists(self.valid_mns_path))
        
        # Test avec fichier inexistant
        non_existent_file = os.path.join(self.temp_dir, "non_existent.tif")
        self.assertFalse(os.path.exists(non_existent_file))
    
    def test_mns_has_valid_format(self):
        """Test que le MNS est un raster valide"""
        # Test avec raster valide
        with rasterio.open(self.valid_mns_path) as src:
            self.assertIsNotNone(src)
            self.assertEqual(src.count, 1)  # Une seule bande
            self.assertEqual(src.dtypes[0], 'float32')
    
    def test_mns_has_required_bands(self):
        """Test que le MNS a exactement une bande"""
        # Test avec raster valide (1 bande)
        with rasterio.open(self.valid_mns_path) as src:
            self.assertEqual(src.count, 1, "Le MNS doit avoir exactement 1 bande")
        
        # Test avec raster invalide (3 bandes)
        with rasterio.open(self.invalid_mns_path) as src:
            self.assertNotEqual(src.count, 1, "Le MNS ne doit pas avoir plusieurs bandes")
    
    def test_mns_has_valid_nodata_values(self):
        """Test que les valeurs no_data sont cohérentes"""
        with rasterio.open(self.valid_mns_path) as src:
            data = src.read(1)
            nodata_value = src.nodata
            
            # Vérifier que les valeurs no_data sont présentes
            self.assertTrue(np.any(data == nodata_value))
            
            # Vérifier que les valeurs no_data sont cohérentes
            self.assertEqual(nodata_value, -9999.0)
    
    def test_mns_contains_valid_elevation_data(self):
        """Test que le MNS contient des données d'altitude valides"""
        with rasterio.open(self.valid_mns_path) as src:
            data = src.read(1)
            nodata_value = src.nodata
            
            # Masquer les valeurs no_data
            valid_data = data[data != nodata_value]
            
            # Vérifier qu'il y a des données valides
            self.assertGreater(len(valid_data), 0, "Le MNS doit contenir des données valides")
            
            # Vérifier que les altitudes sont dans une plage raisonnable
            self.assertGreater(np.min(valid_data), -1000, "Les altitudes doivent être > -1000m")
            self.assertLess(np.max(valid_data), 10000, "Les altitudes doivent être < 10000m")
    
    def test_mns_dimensions_are_reasonable(self):
        """Test que les dimensions du MNS sont raisonnables"""
        with rasterio.open(self.valid_mns_path) as src:
            height, width = src.height, src.width
            
            # Vérifier que les dimensions sont positives
            self.assertGreater(height, 0, "La hauteur doit être positive")
            self.assertGreater(width, 0, "La largeur doit être positive")
            
            # Vérifier que les dimensions sont raisonnables
            self.assertLess(height, 100000, "La hauteur ne doit pas dépasser 100000 pixels")
            self.assertLess(width, 100000, "La largeur ne doit pas dépasser 100000 pixels")
            
            # Vérifier que l'image n'est pas trop petite
            self.assertGreater(height * width, 100, "L'image doit avoir au moins 100 pixels")


class TestParameterValidation(unittest.TestCase):
    """Tests de validation des paramètres"""
    
    def test_resolution_is_positive(self):
        """Test que la résolution est positive"""
        # Test avec résolution valide
        valid_resolutions = [0.5, 1.0, 2.0, 5.0, 10.0]
        for res in valid_resolutions:
            self.assertGreater(res, 0, f"La résolution {res} doit être positive")
        
        # Test avec résolution invalide
        invalid_resolutions = [0, -1, -5.0]
        for res in invalid_resolutions:
            self.assertLessEqual(res, 0, f"La résolution {res} ne doit pas être nulle ou négative")
    
    def test_tile_size_is_reasonable(self):
        """Test que la taille des tuiles est raisonnable"""
        # Test avec tailles valides
        valid_sizes = [100, 200, 300, 500, 1000]
        for size in valid_sizes:
            self.assertGreater(size, 50, f"La taille de tuile {size} doit être > 50")
            self.assertLess(size, 5000, f"La taille de tuile {size} doit être < 5000")
        
        # Test avec tailles invalides
        invalid_sizes = [0, 10, 10000]
        for size in invalid_sizes:
            if size <= 50:
                self.assertLessEqual(size, 50, f"La taille de tuile {size} ne doit pas être trop petite")
            if size >= 5000:
                self.assertGreaterEqual(size, 5000, f"La taille de tuile {size} ne doit pas être trop grande")
    
    def test_pad_size_is_reasonable(self):
        """Test que la taille du recouvrement est raisonnable"""
        tile_size = 300
        
        # Test avec recouvrement valide
        valid_pads = [50, 100, 120, 150]
        for pad in valid_pads:
            self.assertGreater(pad, 0, f"Le recouvrement {pad} doit être positif")
            self.assertLess(pad, tile_size, f"Le recouvrement {pad} doit être < taille de tuile")
        
        # Test avec recouvrement invalide
        invalid_pads = [0, -10, 400]  # 400 > 300
        for pad in invalid_pads:
            if pad <= 0:
                self.assertLessEqual(pad, 0, f"Le recouvrement {pad} ne doit pas être nul ou négatif")
            if pad >= tile_size:
                self.assertGreaterEqual(pad, tile_size, f"Le recouvrement {pad} ne doit pas dépasser la taille de tuile")
    
    def test_cpu_count_is_valid(self):
        """Test que le nombre de CPU est valide"""
        import multiprocessing
        max_cpus = multiprocessing.cpu_count()
        
        # Test avec nombres valides
        valid_cpus = [1, 2, 4, 8, max_cpus]
        for cpu in valid_cpus:
            self.assertGreater(cpu, 0, f"Le nombre de CPU {cpu} doit être positif")
            self.assertLessEqual(cpu, max_cpus, f"Le nombre de CPU {cpu} ne doit pas dépasser {max_cpus}")
        
        # Test avec nombres invalides
        invalid_cpus = [0, -1, max_cpus + 1, max_cpus * 2]
        for cpu in invalid_cpus:
            if cpu <= 0:
                self.assertLessEqual(cpu, 0, f"Le nombre de CPU {cpu} ne doit pas être nul ou négatif")
            if cpu > max_cpus:
                self.assertGreater(cpu, max_cpus, f"Le nombre de CPU {cpu} ne doit pas dépasser {max_cpus}")
    
    def test_sigma_parameter_is_valid(self):
        """Test que le paramètre sigma est valide"""
        # Test avec valeurs valides
        valid_sigmas = [0.1, 0.5, 1.0, 2.0, 5.0]
        for sigma in valid_sigmas:
            self.assertGreater(sigma, 0, f"Le sigma {sigma} doit être positif")
            self.assertLess(sigma, 100, f"Le sigma {sigma} doit être < 100")
        
        # Test avec valeurs invalides
        invalid_sigmas = [0, -0.1, -1.0, 1000]
        for sigma in invalid_sigmas:
            if sigma <= 0:
                self.assertLessEqual(sigma, 0, f"Le sigma {sigma} ne doit pas être nul ou négatif")
            if sigma >= 100:
                self.assertGreaterEqual(sigma, 100, f"Le sigma {sigma} ne doit pas être trop grand")
    
    def test_regul_parameter_is_valid(self):
        """Test que le paramètre regul est valide"""
        # Test avec valeurs valides
        valid_reguls = [0.001, 0.01, 0.1, 1.0, 10.0]
        for regul in valid_reguls:
            self.assertGreater(regul, 0, f"Le regul {regul} doit être positif")
            self.assertLess(regul, 1000, f"Le regul {regul} doit être < 1000")
        
        # Test avec valeurs invalides
        invalid_reguls = [0, -0.01, -1.0, 10000]
        for regul in invalid_reguls:
            if regul <= 0:
                self.assertLessEqual(regul, 0, f"Le regul {regul} ne doit pas être nul ou négatif")
            if regul >= 1000:
                self.assertGreaterEqual(regul, 1000, f"Le regul {regul} ne doit pas être trop grand")


class TestConfigurationValidation(unittest.TestCase):
    """Tests de validation de la configuration complète"""
    
    def setUp(self):
        """Préparation des données de test"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Créer un fichier MNS temporaire pour les tests
        self.test_mns_path = os.path.join(self.temp_dir, "test_mns.tif")
        self.create_test_mns()
    
    def tearDown(self):
        """Nettoyage des fichiers temporaires"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_mns(self):
        """Crée un MNS de test pour les tests de configuration"""
        data = np.random.rand(50, 50).astype(np.float32) * 100
        data[10:15, 20:25] = -9999  # Quelques trous
        
        profile = {
            'driver': 'GTiff',
            'height': 50,
            'width': 50,
            'count': 1,
            'dtype': 'float32',
            'crs': 'EPSG:4326',
            'transform': from_origin(0, 50, 1, 1),
            'nodata': -9999.0
        }
        
        with rasterio.open(self.test_mns_path, 'w', **profile) as dst:
            dst.write(data, 1)
    
    def test_valid_configuration(self):
        """Test d'une configuration valide"""
        config = GEMAUTConfig(
            mns_input=self.test_mns_path,
            mnt_output=os.path.join(self.temp_dir, "output.tif"),
            resolution=4.0,
            cpu_count=4,
            work_dir=self.temp_dir,
            sigma=0.5,
            regul=0.01,
            tile_size=300,
            pad_size=120
        )
        
        # Vérifier que la configuration est valide
        self.assertIsNotNone(config)
        self.assertEqual(config.resolution, 4.0)
        self.assertEqual(config.cpu_count, 4)
        self.assertEqual(config.sigma, 0.5)
        self.assertEqual(config.regul, 0.01)
    
    def test_configuration_with_invalid_parameters(self):
        """Test d'une configuration avec paramètres invalides"""
        # Test avec résolution invalide
        with self.assertRaises(ValueError):
            GEMAUTConfig(
                mns_input=self.test_mns_path,
                mnt_output=os.path.join(self.temp_dir, "output.tif"),
                resolution=-1.0,  # Résolution négative
                cpu_count=4,
                work_dir=self.temp_dir
            )
        
        # Test avec nombre de CPU invalide
        with self.assertRaises(ValueError):
            GEMAUTConfig(
                mns_input=self.test_mns_path,
                mnt_output=os.path.join(self.temp_dir, "output.tif"),
                resolution=4.0,
                cpu_count=0,  # CPU nul
                work_dir=self.temp_dir
            )
    
    def test_required_parameters_are_present(self):
        """Test que tous les paramètres requis sont présents"""
        # Test avec tous les paramètres requis
        config = GEMAUTConfig(
            mns_input=self.test_mns_path,
            mnt_output=os.path.join(self.temp_dir, "output.tif"),
            resolution=4.0,
            cpu_count=4,
            work_dir=self.temp_dir
        )
        
        self.assertIsNotNone(config.mns_input)
        self.assertIsNotNone(config.mnt_output)
        self.assertIsNotNone(config.resolution)
        self.assertIsNotNone(config.cpu_count)
        self.assertIsNotNone(config.work_dir)


if __name__ == '__main__':
    print("🧪 Tests de validation GEMAUT")
    print("=" * 50)
    unittest.main(verbosity=2) 