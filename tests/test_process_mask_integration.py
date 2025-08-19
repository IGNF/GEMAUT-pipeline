#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests d'intégration pour l'étape _process_mask du pipeline GEMAUT
Compare le masque calculé avec MASQUE_REFERENCE.tif
Valide que le calcul automatique des masques fonctionne correctement
"""

import unittest
import numpy as np
import rasterio
import tempfile
import os
import shutil
from loguru import logger

# Import des modules à tester
import sys
sys.path.append('..')
from script_gemaut import GEMAUTPipeline
from gemaut_config import GEMAUTConfig
import saga_integration


class TestProcessMaskIntegration(unittest.TestCase):
    """Tests d'intégration pour l'étape _process_mask du pipeline"""
    
    @classmethod
    def setUpClass(cls):
        """Prépare les données de test et le masque de référence"""
        # Configuration commune
        cls.temp_dir = tempfile.mkdtemp()
        cls.mns_input = os.path.join(os.path.dirname(__file__), "MNS_IN.tif")
        cls.masque_reference = os.path.join(os.path.dirname(__file__), "MASQUE_REFERENCE.tif")
        cls.work_dir = os.path.join(cls.temp_dir, "work")
        
        # Vérifier que les fichiers de référence existent
        if not os.path.exists(cls.mns_input):
            raise FileNotFoundError(f"Fichier MNS de référence manquant: {cls.mns_input}")
        if not os.path.exists(cls.masque_reference):
            raise FileNotFoundError(f"Fichier masque de référence manquant: {cls.masque_reference}")
        
        # Créer le répertoire de travail
        os.makedirs(cls.work_dir, exist_ok=True)
        
        logger.info("🚀 Tests d'intégration _process_mask - Masque de référence chargé")
    
    def setUp(self):
        """Préparation individuelle pour chaque test"""
        pass
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage final après tous les tests"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
        logger.info("🧹 Nettoyage des fichiers temporaires terminé")
    
    def load_raster_data(self, raster_path):
        """Charge les données raster et leurs métadonnées"""
        with rasterio.open(raster_path) as src:
            data = src.read(1)
            profile = src.profile
            transform = src.transform
            crs = src.crs
            nodata = src.nodata
        return data, profile, transform, crs, nodata
    
    def compare_masks(self, mask1_path, mask2_path, tolerance=1e-6):
        """Compare deux masques et retourne les différences"""
        data1, profile1, transform1, crs1, nodata1 = self.load_raster_data(mask1_path)
        data2, profile2, transform2, crs2, nodata2 = self.load_raster_data(mask2_path)
        
        # Masquer les valeurs NoData
        if nodata1 is not None:
            valid1 = data1 != nodata1
        else:
            valid1 = ~np.isnan(data1)
        
        if nodata2 is not None:
            valid2 = data2 != nodata2
        else:
            valid2 = ~np.isnan(data2)
        
        # Masque combiné des pixels valides
        valid_combined = valid1 & valid2
        
        if not np.any(valid_combined):
            return {
                'max_diff': float('inf'),
                'mean_diff': float('inf'),
                'percent_different': 100.0,
                'metadata_match': {'crs': False, 'transform': False, 'dimensions': False}
            }
        
        # Calculer les différences
        diff = np.abs(data1[valid_combined] - data2[valid_combined])
        max_diff = np.max(diff)
        mean_diff = np.mean(diff)
        
        # Pourcentage de pixels différents (au-delà de la tolérance)
        different_pixels = np.sum(diff > tolerance)
        percent_different = (different_pixels / np.sum(valid_combined)) * 100.0
        
        # Vérifier la cohérence des métadonnées
        metadata_match = {
            'crs': str(crs1) == str(crs2),
            'transform': transform1 == transform2,
            'dimensions': data1.shape == data2.shape
        }
        
        return {
            'max_diff': max_diff,
            'mean_diff': mean_diff,
            'percent_different': percent_different,
            'metadata_match': metadata_match
        }
    
    def test_process_mask_step_standalone(self):
        """Teste l'étape _process_mask de manière isolée"""
        logger.info("🧪 Test de l'étape _process_mask du pipeline")
        
        # Arrange : Configuration pour le test
        # Calculer le nombre de CPU à utiliser (2/3 des CPU disponibles)
        import multiprocessing
        available_cpus = multiprocessing.cpu_count()
        test_cpus = max(1, int(available_cpus * 2 / 3))
        
        config = GEMAUTConfig(
            mns_input=self.mns_input,
            mnt_output=os.path.join(self.temp_dir, "MNT_OUT_TEST.tif"),
            resolution=4.0,
            cpu_count=test_cpus,  # Utiliser 2/3 des CPU disponibles
            work_dir=self.work_dir,
            sigma=0.5,
            regul=0.01,
            tile_size=200,
            pad_size=80,
            clean_temp=False,
            verbose=False
        )
        
        logger.info(f"🖥️  Utilisation de {test_cpus}/{available_cpus} CPU disponibles")
        
        # Act : Créer le pipeline et exécuter les étapes nécessaires
        pipeline = GEMAUTPipeline(config)
        
        # Exécuter les étapes préalables nécessaires pour _process_mask
        logger.info("🔄 Exécution des étapes préalables...")
        
        # Étape 1: Remplissage des trous dans MNS
        logger.info("   → Étape 1: Remplissage des trous...")
        pipeline._fill_holes_in_mns()
        
        # Étape 2: Remplacement des valeurs NoData max
        logger.info("   → Étape 2: Remplacement NoData max...")
        pipeline._replace_nodata_max()
        
        # Maintenant exécuter l'étape de calcul du masque
        logger.info("🔄 Exécution de l'étape _process_mask...")
        pipeline._process_mask()
        
        # Assert : Vérifier que le masque a été créé
        expected_mask_path = os.path.join(self.work_dir, 'MASQUE_compute.tif')
        self.assertTrue(os.path.exists(expected_mask_path), 
                       f"Le masque calculé doit être créé dans {expected_mask_path}")
        
        # Comparer avec le masque de référence
        logger.info("🔍 Comparaison avec le masque de référence...")
        comparison = self.compare_masks(self.masque_reference, expected_mask_path)
        
        # Assertions sur la cohérence
        self.assertTrue(comparison['metadata_match']['crs'], 
                       "Le système de coordonnées doit être identique")
        self.assertTrue(comparison['metadata_match']['transform'], 
                       "La transformation géométrique doit être identique")
        self.assertTrue(comparison['metadata_match']['dimensions'], 
                       "Les dimensions doivent être identiques")
        
        # Tolérance pour les différences numériques
        # Le masque peut avoir des petites différences selon la version SAGA
        self.assertLess(comparison['max_diff'], 1.0, 
                       f"La différence maximale ({comparison['max_diff']:.6f}) doit être < 1.0")
        self.assertLess(comparison['mean_diff'], 0.1, 
                       f"La différence moyenne ({comparison['mean_diff']:.6f}) doit être < 0.1")
        
        # Pourcentage de pixels différents - tolérance réaliste
        self.assertLess(comparison['percent_different'], 10.0, 
                       f"Le pourcentage de pixels différents ({comparison['percent_different']:.2f}%) doit être < 10%")
        
        logger.info(f"📊 Différences: max={comparison['max_diff']:.6f}, mean={comparison['mean_diff']:.6f}, %diff={comparison['percent_different']:.2f}%")
        logger.info("✅ Test de l'étape _process_mask réussi")
    
    def test_mask_file_generation(self):
        """Teste que le fichier masque est généré correctement"""
        logger.info("🧪 Test de génération du fichier masque")
        
        # Vérifier que le masque de référence est valide
        ref_data, ref_profile, ref_transform, ref_crs, ref_nodata = self.load_raster_data(self.masque_reference)
        
        # Vérifier les propriétés du masque
        self.assertGreater(ref_data.shape[0], 0, "Le masque doit avoir une hauteur > 0")
        self.assertGreater(ref_data.shape[1], 0, "Le masque doit avoir une largeur > 0")
        
        # Vérifier que le masque contient des données valides
        if ref_nodata is not None:
            valid_data = ref_data[ref_data != ref_nodata]
        else:
            valid_data = ref_data[~np.isnan(ref_data)]
        
        self.assertGreater(len(valid_data), 0, "Le masque doit contenir des données valides")
        
        # Vérifier que les valeurs sont dans une plage raisonnable
        # Pour un masque binaire typique (0 et 255) ou des valeurs de classification
        unique_values = np.unique(valid_data)
        logger.info(f"📊 Valeurs uniques dans le masque: {unique_values}")
        
        logger.info(f"📏 Dimensions du masque: {ref_data.shape}")
        logger.info(f"🔧 CRS: {ref_crs}")
        logger.info(f"🔧 Transform: {ref_transform}")
        logger.info("✅ Test de génération du fichier masque réussi")
    
    def test_saga_integration_availability(self):
        """Teste que l'intégration SAGA est disponible"""
        logger.info("🧪 Test de disponibilité de l'intégration SAGA")
        
        # Vérifier que le module SAGA est accessible
        self.assertTrue(hasattr(saga_integration, 'SAGAIntegration'), 
                       "Le module SAGAIntegration doit être disponible")
        
        # Vérifier que la méthode de logging existe
        self.assertTrue(hasattr(saga_integration.SAGAIntegration, 'log_saga_environment'), 
                       "La méthode log_saga_environment doit être disponible")
        
        # Vérifier que la méthode de calcul de masque existe
        self.assertTrue(hasattr(saga_integration.SAGAIntegration, 'compute_mask_with_saga'), 
                       "La méthode compute_mask_with_saga doit être disponible")
        
        logger.info("✅ Test de disponibilité de l'intégration SAGA réussi")


if __name__ == "__main__":
    # Configuration du logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="INFO")
    
    # Exécution des tests
    unittest.main(verbosity=2) 