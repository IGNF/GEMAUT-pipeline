#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests de régression pour le MNT final
Compare le MNT calculé avec MNT_OUT_REFERENCE.tif
Garantit que la qualité du MNT ne se dégrade pas
"""

import unittest
import numpy as np
import rasterio
import tempfile
import os
import shutil
from rasterio.transform import from_origin
from loguru import logger

# Import des modules à tester
import sys
sys.path.append('..')
from script_gemaut import GEMAUTPipeline
from gemaut_config import GEMAUTConfig


class TestMNTRegression(unittest.TestCase):
    """Tests de régression pour le MNT final"""
    
    @classmethod
    def setUpClass(cls):
        """Exécution unique du pipeline GEMAUT pour tous les tests"""
        # Configuration commune
        cls.temp_dir = tempfile.mkdtemp()
        cls.mns_input = os.path.join(os.path.dirname(__file__), "MNS_IN.tif")
        cls.mnt_reference = os.path.join(os.path.dirname(__file__), "MNT_OUT_REFERENCE.tif")
        cls.mnt_output = os.path.join(cls.temp_dir, "MNT_OUT_TEST.tif")
        cls.work_dir = os.path.join(cls.temp_dir, "work")
        
        # Vérifier que les fichiers de référence existent
        if not os.path.exists(cls.mns_input):
            raise FileNotFoundError(f"Fichier MNS de référence manquant: {cls.mns_input}")
        if not os.path.exists(cls.mnt_reference):
            raise FileNotFoundError(f"Fichier MNT de référence manquant: {cls.mnt_reference}")
        
        # Créer le répertoire de travail
        os.makedirs(cls.work_dir, exist_ok=True)
        
        # Calculer le nombre de CPU à utiliser (2/3 des CPU disponibles)
        import multiprocessing
        available_cpus = multiprocessing.cpu_count()
        test_cpus = max(1, int(available_cpus * 2 / 3))
        
        # Configuration pour le pipeline
        config = GEMAUTConfig(
            mns_input=cls.mns_input,
            mnt_output=cls.mnt_output,
            resolution=4.0,
            cpu_count=test_cpus,
            work_dir=cls.work_dir,
            sigma=0.5,
            regul=0.01,
            tile_size=200,
            pad_size=80,
            clean_temp=False,
            verbose=False  # Pas de logs console
        )
        
        # Exécuter le pipeline une seule fois pour tous les tests
        import time
        logger.info("🚀 Exécution unique du pipeline GEMAUT pour tous les tests")
        start_time = time.time()
        pipeline = GEMAUTPipeline(config)
        pipeline.run()
        end_time = time.time()
        
        execution_time = end_time - start_time
        logger.info(f"⏱️  Temps d'exécution du pipeline: {execution_time:.2f} secondes")
        
        # Vérifier que le fichier de sortie a été créé
        if not os.path.exists(cls.mnt_output):
            raise FileNotFoundError(f"Le fichier MNT de sortie n'a pas été créé: {cls.mnt_output}")
        
        logger.info("✅ Pipeline GEMAUT exécuté avec succès")
    
    def setUp(self):
        """Préparation individuelle pour chaque test (plus nécessaire)"""
        pass
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage final après tous les tests (sauf le MNT de sortie)"""
        import time
        
        # Garder le MNT de sortie pour analyse
        if hasattr(cls, 'mnt_output') and os.path.exists(cls.mnt_output):
            # Copier le MNT dans le répertoire tests pour analyse
            output_dir = os.path.dirname(__file__)
            backup_name = f"MNT_OUT_TEST_{int(time.time())}.tif"
            backup_path = os.path.join(output_dir, backup_name)
            shutil.copy2(cls.mnt_output, backup_path)
            logger.info(f"📁 MNT de test sauvegardé: {backup_path}")
        
        # Supprimer le reste des fichiers temporaires
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def tearDown(self):
        """Nettoyage individuel (plus nécessaire)"""
        pass
    
    def load_raster_data(self, file_path):
        """Charge les données d'un raster"""
        with rasterio.open(file_path) as src:
            data = src.read(1)
            profile = src.profile
            transform = src.transform
            crs = src.crs
            nodata = src.nodata
        return data, profile, transform, crs, nodata
    
    def compare_rasters(self, raster1_path, raster2_path, tolerance=1e-2):
        """Compare deux rasters et retourne les différences"""
        data1, profile1, transform1, crs1, nodata1 = self.load_raster_data(raster1_path)
        data2, profile2, transform2, crs2, nodata2 = self.load_raster_data(raster2_path)
        
        # Vérifier les métadonnées
        metadata_match = {
            'dimensions': data1.shape == data2.shape,
            'crs': str(crs1) == str(crs2),
            'transform': transform1 == transform2,
            'nodata': nodata1 == nodata2,
            'dtype': profile1['dtype'] == profile2['dtype']
        }
        
        # Masquer les valeurs no_data pour la comparaison
        mask1 = data1 != nodata1
        mask2 = data2 != nodata2
        common_mask = mask1 & mask2
        
        # Calculer les différences
        if np.any(common_mask):
            diff = np.abs(data1[common_mask] - data2[common_mask])
            max_diff = np.max(diff)
            mean_diff = np.mean(diff)
            std_diff = np.std(diff)
            pixels_different = np.sum(diff > tolerance)
            total_pixels = np.sum(common_mask)
            percent_different = (pixels_different / total_pixels) * 100
        else:
            max_diff = mean_diff = std_diff = 0
            pixels_different = total_pixels = percent_different = 0
        
        return {
            'metadata_match': metadata_match,
            'max_diff': max_diff,
            'mean_diff': mean_diff,
            'std_diff': std_diff,
            'pixels_different': pixels_different,
            'total_pixels': total_pixels,
            'percent_different': percent_different,
            'tolerance': tolerance
        }
    
    def test_mnt_quality_regression(self):
        """Test principal de régression - MNT calculé vs référence"""
        logger.info("🧪 Test de régression qualité MNT")
        
        # Comparer avec la référence
        comparison = self.compare_rasters(self.mnt_output, self.mnt_reference)
        
        # Tests de régression
        logger.info(f"📊 Résultats de la comparaison:")
        logger.info(f"   - Différence max: {comparison['max_diff']:.6f}")
        logger.info(f"   - Différence moyenne: {comparison['mean_diff']:.6f}")
        logger.info(f"   - Pixels différents: {comparison['pixels_different']}/{comparison['total_pixels']} ({comparison['percent_different']:.2f}%)")
        
        # Assertions de qualité
        self.assertTrue(comparison['metadata_match']['dimensions'], 
                       "Les dimensions doivent être identiques")
        self.assertTrue(comparison['metadata_match']['crs'], 
                       "Le système de coordonnées doit être identique")
        self.assertTrue(comparison['metadata_match']['transform'], 
                       "La transformation géométrique doit être identique")
        
        # Tolérance réaliste pour les différences numériques (précision centimétrique)
        self.assertLess(comparison['max_diff'], 0.1, 
                       f"La différence maximale ({comparison['max_diff']:.6f}) doit être < 0.1 m (10 cm)")
        self.assertLess(comparison['mean_diff'], 0.01, 
                       f"La différence moyenne ({comparison['mean_diff']:.6f}) doit être < 0.01 m (1 cm)")
        
        # Pourcentage de pixels différents - tolérance réaliste
        if comparison['percent_different'] > 5.0:
            logger.warning(f"⚠️  Attention: {comparison['percent_different']:.2f}% de pixels différents")
            logger.warning("   Avec une tolérance de 1 cm, ce pourcentage devrait être < 5%")
            logger.warning("   Vérifiez les paramètres et versions des logiciels")
        
        # Test du pourcentage de pixels différents avec tolérance réaliste
        self.assertLess(comparison['percent_different'], 5.0, 
                       f"Le pourcentage de pixels différents ({comparison['percent_different']:.2f}%) doit être < 5% (tolérance 1 cm)")
        
        logger.info("✅ Test de régression MNT réussi")
    
    def test_mnt_performance(self):
        """Test de performance du pipeline (intégré dans les tests de régression)"""
        logger.info("🧪 Test de performance du pipeline")
        
        # Vérifier que le fichier existe et a une taille raisonnable
        self.assertTrue(os.path.exists(self.mnt_output), 
                       "Le fichier MNT de sortie doit exister")
        
        file_size = os.path.getsize(self.mnt_output)
        logger.info(f"📁 Taille du fichier MNT: {file_size / 1024 / 1024:.2f} MB")
        
        # Vérifier que le fichier a une taille raisonnable (> 10 KB)
        self.assertGreater(file_size, 10 * 1024, 
                          f"Le fichier MNT doit faire plus de 10 KB (actuel: {file_size / 1024:.2f} KB)")
        
        logger.info("✅ Test de performance réussi")
    
    def test_mnt_metadata_consistency(self):
        """Test de la cohérence des métadonnées du MNT"""
        logger.info("🧪 Test de cohérence des métadonnées")
        
        # Charger les métadonnées de référence
        with rasterio.open(self.mnt_reference) as src:
            ref_profile = src.profile
            ref_transform = src.transform
            ref_crs = src.crs
            ref_nodata = src.nodata
        
        # Vérifier les métadonnées du MNT calculé
        with rasterio.open(self.mnt_output) as src:
            test_profile = src.profile
            test_transform = src.transform
            test_crs = src.crs
            test_nodata = src.nodata
        
        # Comparaisons
        self.assertEqual(test_profile['dtype'], ref_profile['dtype'], 
                        "Le type de données doit être identique")
        self.assertEqual(test_profile['count'], ref_profile['count'], 
                        "Le nombre de bandes doit être identique")
        self.assertEqual(str(test_crs), str(ref_crs), 
                        "Le système de coordonnées doit être identique")
        self.assertEqual(test_nodata, ref_nodata, 
                        "La valeur no_data doit être identique")
        
        logger.info("✅ Test de cohérence des métadonnées réussi")
    
    def test_mnt_spatial_extent(self):
        """Test de l'étendue spatiale du MNT"""
        logger.info("🧪 Test de l'étendue spatiale")
        
        # Charger les données de référence
        ref_data, ref_profile, ref_transform, ref_crs, ref_nodata = self.load_raster_data(self.mnt_reference)
        
        # Charger les données calculées
        test_data, test_profile, test_transform, test_crs, test_nodata = self.load_raster_data(self.mnt_output)
        
        # Vérifier les dimensions
        self.assertEqual(test_data.shape, ref_data.shape, 
                        "Les dimensions doivent être identiques")
        
        # Vérifier la transformation géométrique
        self.assertEqual(test_transform, ref_transform, 
                        "La transformation géométrique doit être identique")
        
        # Vérifier que les données ne sont pas vides
        ref_valid = ref_data != ref_nodata
        test_valid = test_data != test_nodata
        
        self.assertGreater(np.sum(ref_valid), 0, 
                          "La référence doit contenir des données valides")
        self.assertGreater(np.sum(test_valid), 0, 
                          "Le MNT calculé doit contenir des données valides")
        
        logger.info("✅ Test de l'étendue spatiale réussi")
    
    def test_mnt_statistical_consistency(self):
        """Test de la cohérence statistique du MNT"""
        logger.info("🧪 Test de cohérence statistique")
        
        # Charger les données de référence
        ref_data, _, _, _, ref_nodata = self.load_raster_data(self.mnt_reference)
        ref_valid = ref_data != ref_nodata
        ref_stats = {
            'min': np.min(ref_data[ref_valid]),
            'max': np.max(ref_data[ref_valid]),
            'mean': np.mean(ref_data[ref_valid]),
            'std': np.std(ref_data[ref_valid])
        }
        
        # Charger les données calculées
        test_data, _, _, _, test_nodata = self.load_raster_data(self.mnt_output)
        test_valid = test_data != test_nodata
        test_stats = {
            'min': np.min(test_data[test_valid]),
            'max': np.max(test_data[test_valid]),
            'mean': np.mean(test_data[test_valid]),
            'std': np.std(test_data[test_valid])
        }
        
        # Comparer les statistiques (tolérance stricte de 1% pour calcul exact)
        tolerance = 0.01
        for stat in ['min', 'max', 'mean', 'std']:
            ref_val = ref_stats[stat]
            test_val = test_stats[stat]
            diff_percent = abs(test_val - ref_val) / abs(ref_val) * 100
            
            logger.info(f"   {stat}: référence={ref_val:.3f}, test={test_val:.3f}, diff={diff_percent:.2f}%")
            
            self.assertLess(diff_percent, 1.0, 
                           f"La différence pour {stat} ({diff_percent:.2f}%) doit être < 1% (calcul exact)")
        
        logger.info("✅ Test de cohérence statistique réussi")





if __name__ == '__main__':
    print("🧪 Tests de régression MNT GEMAUT")
    print("=" * 50)
    unittest.main(verbosity=2) 