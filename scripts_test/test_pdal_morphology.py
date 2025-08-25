#!/usr/bin/env python3
"""
Script de test des opérations morphologiques PDAL
Teste les fonctions qui remplaceront SAGA ta_morphometry
"""

import sys
import os

def test_pdal_slope():
    """Test du calcul de pente avec PDAL"""
    try:
        import pdal
        
        print("📊 Test calcul de pente PDAL...")
        
        # Pipeline simple pour la pente
        pipeline_str = """
        {
            "pipeline": [
                {"type": "readers.raster", "filename": "data/MNS_IN.tif"},
                {"type": "filters.morphology", "operation": "slope"},
                {"type": "writers.raster", "filename": "output/pdal_results/slope_pdal.tif"}
            ]
        }
        """
        
        pipeline = pdal.Pipeline(pipeline_str)
        print("✅ Pipeline pente PDAL créé")
        
        # Créer le répertoire de sortie
        os.makedirs("output/pdal_results", exist_ok=True)
        
        # Exécuter le pipeline
        result = pipeline.execute()
        print(f"✅ Pente calculée avec PDAL")
        print(f"   Résultat: {result.arrays[0].shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur calcul pente PDAL: {e}")
        return False

def main():
    """Fonction principale"""
    print("🧪 TESTS DES OPÉRATIONS MORPHOLOGIQUES PDAL")
    print("=" * 50)
    
    # Vérifier que PDAL est installé
    try:
        import pdal
    except ImportError:
        print("❌ PDAL non installé. Installez d'abord avec:")
        print("   conda install -c conda-forge pdal pdal-python")
        sys.exit(1)
    
    # Test de la pente
    if test_pdal_slope():
        print("\n🎉 Test de pente PDAL réussi !")
    else:
        print("\n⚠️  Test de pente PDAL échoué")

if __name__ == "__main__":
    main() 