# Calcul Automatique de Masque Sol/Sursol dans GEMAUT

## Vue d'ensemble

GEMAUT intègre maintenant **deux méthodes** pour calculer automatiquement les masques binaires sol/sursol à partir d'un MNS :

1. **SAGA** : Méthode traditionnelle, mature et testée
2. **PDAL** : Méthode moderne, plus rapide avec l'algorithme CSF

## Avantages de l'intégration

- ✅ **Choix flexible** : SAGA ou PDAL selon vos besoins
- ✅ **Calcul automatique** : Plus besoin de préparer manuellement les masques
- ✅ **Fallback intelligent** : Retour automatique vers SAGA si PDAL échoue
- ✅ **Paramètres optimisés** : Configuration automatique selon la méthode
- ✅ **Rétrocompatibilité** : Fonctionne avec les configurations existantes

## Utilisation

### 1. Ligne de commande

#### Calcul automatique avec choix de méthode
```bash
# Choix automatique (recommandé)
python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 24 --RepTra /tmp --mask-method auto

# Méthode SAGA (traditionnelle)
python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 24 --RepTra /tmp --mask-method saga

# Méthode PDAL (rapide)
python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 24 --RepTra /tmp --mask-method pdal
```

#### Désactiver le calcul automatique
```bash
# Utiliser un masque fourni
python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 24 --RepTra /tmp --masque /chemin/vers/masque.tif
```

### 2. Fichier de configuration YAML

```yaml
# Configuration avec calcul automatique
mask_computation:
  auto_computation: true
  method: "auto"  # ou "saga", "pdal"

# Paramètres SAGA
saga:
  radius: 100.0
  tile: 100
  pente: 15.0

# Paramètres PDAL
pdal:
  csf:
    max_iterations: 500
    class_threshold: 0.6
    rigidness: 4
```

## Comparaison des méthodes

### SAGA (Méthode traditionnelle)
- **Avantages** :
  - Mature et testée dans GEMAUT
  - Paramètres optimisés
  - Intégration complète
- **Inconvénients** :
  - Plus lente
  - Dépendance externe

### PDAL (Méthode moderne)
- **Avantages** :
  - Plus rapide (algorithme CSF)
  - Moins de dépendances
  - Paramètres avancés configurables
- **Inconvénients** :
  - Plus récent
  - Paramètres à optimiser

## Paramètres configurables

### Paramètres SAGA
```yaml
saga:
  radius: 100.0        # Rayon de recherche
  tile: 100            # Taille des dalles
  pente: 15.0          # Pente maximale
```

### Paramètres PDAL
```yaml
pdal:
  # Paramètres de base
  radius: 100.0
  tile: 100
  pente: 15.0
  
  # Paramètres CSF
  csf:
    max_iterations: 500      # Itérations (plus = meilleure précision)
    class_threshold: 0.6     # Seuil de classification (0.6 = strict)
    cell_size: 1.0          # Résolution de grille
    time_step: 0.65         # Pas de temps
    rigidness: 4            # Rigidité (plus = strict)
  
  # Filtres de prétraitement
  outlier:
    multiplier: 2.5         # Détection d'outliers
    max_neighbors: 50       # Voisins pour analyse
```

## Optimisation des performances

### Pour la précision (PDAL)
```yaml
pdal:
  csf:
    max_iterations: 1000
    class_threshold: 0.7
    rigidness: 6
```

### Pour la vitesse (PDAL)
```yaml
pdal:
  csf:
    max_iterations: 200
    class_threshold: 0.5
    rigidness: 2
```

## Dépannage

### Vérifier l'installation
```bash
# Tester l'intégration
python test_mask_integration.py
```

### Problèmes courants

#### Module PDAL non disponible
```
⚠️ Module PDAL non disponible
```
**Solution** : Vérifiez que le dossier `/home/NChampion/DATADRIVE1/DEVELOPPEMENT/test_pdal/` existe et contient les modules nécessaires.

#### SAGA non fonctionnel
```
⚠️ SAGA détecté mais non fonctionnel
```
**Solution** : Vérifiez l'installation de SAGA avec `saga_cmd --version`

#### Fallback automatique
Si PDAL échoue, GEMAUT bascule automatiquement vers SAGA :
```
❌ Erreur lors du calcul automatique du masque
🔧 Fallback vers la méthode SAGA traditionnelle...
```

## Exemples complets

### Exemple 1 : Pipeline complet avec PDAL
```bash
python script_gemaut.py \
  --mns /data/MNS.tif \
  --out /data/MNT.tif \
  --reso 4 \
  --cpu 24 \
  --RepTra /tmp/work \
  --mask-method pdal \
  --sigma 0.5 \
  --regul 0.01 \
  --tile 300 \
  --pad 120 \
  --clean
```

### Exemple 2 : Configuration YAML
```yaml
input:
  mns_file: "/data/MNS.tif"
  output_mnt: "/data/MNT.tif"
  resolution: 4.0
  cpu_count: 24
  work_directory: "/tmp/work"

mask_computation:
  auto_computation: true
  method: "pdal"

gemo:
  sigma: 0.5
  regul: 0.01
  tile_size: 300
  pad_size: 120
  norme: "hubertukey"
```

## Support et développement

### Structure des fichiers
```
GEMAUT-pipeline/
├── mask_computer.py              # Module principal de calcul
├── script_gemaut.py             # Script principal modifié
├── gemaut_config.py             # Configuration étendue
├── config.py                    # Constantes ajoutées
├── test_mask_integration.py     # Tests d'intégration
└── config_exemple_avec_masque_auto.yaml  # Configuration d'exemple
```

### Tests
```bash
# Test complet de l'intégration
python test_mask_integration.py

# Test du script principal
python script_gemaut.py --help
```

### Logs
Les logs détaillent le processus de calcul :
```
🚀 Calcul du masque avec PDAL
📁 MNS: /tmp/MNS4SAGA_nodata_max.tif
📁 Sortie: /tmp/work/MASQUE_compute.tif
⚙️ Paramètres: {'radius': 100.0, 'tile': 100, ...}
✅ Masque calculé avec succès en 45.23s
```

## Migration depuis l'ancienne version

### Avant (SAGA uniquement)
```bash
python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 24 --RepTra /tmp
```

### Après (avec choix de méthode)
```bash
# Comportement identique (SAGA par défaut)
python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 24 --RepTra /tmp

# Ou explicitement SAGA
python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 24 --RepTra /tmp --mask-method saga

# Ou PDAL pour plus de vitesse
python script_gemaut.py --mns MNS.tif --out MNT.tif --reso 4 --cpu 24 --RepTra /tmp --mask-method pdal
```

## Conclusion

L'intégration du calcul automatique de masque avec SAGA et PDAL offre :
- **Flexibilité** : Choix entre précision (SAGA) et vitesse (PDAL)
- **Robustesse** : Fallback automatique en cas de problème
- **Simplicité** : Plus besoin de préparer manuellement les masques
- **Performance** : Optimisation possible selon vos besoins

Commencez par tester avec `--mask-method auto` pour laisser GEMAUT choisir la meilleure méthode disponible !

