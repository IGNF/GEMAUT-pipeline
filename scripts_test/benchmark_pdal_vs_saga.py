#!/usr/bin/env python3
"""
Script de benchmark PDAL vs SAGA
Compare les performances des deux solutions
"""

import sys
import os
import time

def check_pdal():
    """Vérifie que PDAL est installé"""
    try:
        import pdal
        return True, pdal.__version__
    except ImportError:
        return False, None

def check_saga():
    """Vérifie que SAGA est installé"""
    try:
        import subprocess
        result = subprocess.run(['saga_cmd', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, "Installé"
        return False, None
    except:
        return False, None

def benchmark_pdal():
    """Benchmark PDAL"""
    try:
        import pdal
        
        print("🔄 Benchmark PDAL en cours...")
        
        pipeline_str = """
        {
            "pipeline": [
                {"type": "readers.raster", "filename": "data/MNS_IN.tif"},
                {"type": "filters.morphology", "operation": "slope"},
                {"type": "writers.raster", "filename": "output/pdal_results/slope_benchmark.tif"}
            ]
        }
        """
        
        pipeline = pdal.Pipeline(pipeline_str)
        os.makedirs("output/pdal_results", exist_ok=True)
        
        start_time = time.time()
        result = pipeline.execute()
        execution_time = time.time() - start_time
        
        print(f"✅ PDAL terminé en {execution_time:.2f}s")
        return True, execution_time
        
    except Exception as e:
        print(f"❌ Erreur benchmark PDAL: {e}")
        return False, 0

def benchmark_saga():
    """Benchmark SAGA"""
    try:
        import subprocess
        
        print("🔄 Benchmark SAGA en cours...")
        
        os.makedirs("output/saga_results", exist_ok=True)
        
        cmd = [
            'saga_cmd', 'ta_morphometry', '0',
            '-ELEVATION', 'data/MNS_IN.tif',
            '-SLOPE', 'output/saga_results/slope_benchmark.tif',
            '-METHOD', '1'
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300)
        execution_time = time.time() - start_time
        
        print(f"✅ SAGA terminé en {execution_time:.2f}s")
        return True, execution_time
        
    except Exception as e:
        print(f"❌ Erreur benchmark SAGA: {e}")
        return False, 0

def main():
    """Fonction principale"""
    print("🏁 BENCHMARK PDAL vs SAGA")
    print("=" * 50)
    
    # Vérifier les installations
    pdal_ok, pdal_version = check_pdal()
    saga_ok, saga_version = check_saga()
    
    print(f"PDAL: {'✅' if pdal_ok else '❌'} (v{pdal_version if pdal_version else 'Non installé'})")
    print(f"SAGA: {'✅' if saga_ok else '❌'} (v{saga_version if saga_version else 'Non installé'})")
    
    if not pdal_ok or not saga_ok:
        print("\n⚠️  Impossible de faire le benchmark complet")
        return
    
    # Vérifier les données
    if not os.path.exists("data/MNS_IN.tif"):
        print("❌ Fichier data/MNS_IN.tif non trouvé")
        return
    
    # Benchmark
    pdal_ok, pdal_time = benchmark_pdal()
    saga_ok, saga_time = benchmark_saga()
    
    # Résultats
    if pdal_ok and saga_ok:
        print(f"\n📊 RÉSULTATS:")
        print(f"PDAL: {pdal_time:.2f}s")
        print(f"SAGA: {saga_time:.2f}s")
        
        if pdal_time < saga_time:
            improvement = (saga_time - pdal_time) / saga_time * 100
            print(f"\n🎉 PDAL est {improvement:.1f}% plus rapide que SAGA !")
        else:
            slowdown = (pdal_time - saga_time) / saga_time * 100
            print(f"\n⚠️  PDAL est {slowdown:.1f}% plus lent que SAGA")

if __name__ == "__main__":
    main() 