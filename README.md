<p align="center">
  <img src="assets/logo.png" alt="GEMAUT" width="200" style="margin-right: 20px;"/>
  <img src="assets/Linux.png" alt="Linux" width="200"/>
</p>

#########################################################################################
# GEMAUT - Génération de Modèles Automatiques de Terrain
#########################################################################################

L'outil pour le passage MNS > MNT sous Linux & Conda

#########################################################################################
###### Installation
#########################################################################################

###### Prérequis
- Conda (Miniconda ou Anaconda)
- Git

###### Méthode d'installation automatique
```bash
# Cloner le dépôt
git clone https://github.com/IGNF/GEMAUT-pipeline.git
cd GEMAUT-pipeline

# créer un environnement conda & l'activer
conda env create -n gemaut_env -f  gemaut_env.yml

conda activate gemaut_env

# Rendre le script d'installation exécutable
chmod +x install_gemaut.sh

# Lancer l'installation
./install_gemaut.sh
```

#########################################################################################
###### Utilisation
#########################################################################################
1. Si ce n'est pas déjà fait, activer l'environnement :
```bash
conda activate gemaut_env
```

2. Voir l'aide du script :
```bash
script_gemaut --help
```

3. Exemple d'utilisation :
```bash
script_gemaut --mns /chemin/vers/MNS_in.tif \
              --out /chemin/vers/MNT.tif \
              --reso 4 \
              --cpu 24 \
              --RepTra /chemin/vers/RepTra \
              --nodata_ext -32768 \
              --nodata_int -32767
```

## Structure des données

Le MNS d'entrée doit avoir des valeurs de no_data différentes pour :
- Les bords de chantier (`--nodata_ext`, défaut: -32768)
- Les trous à l'intérieur du chantier (`--nodata_int`, défaut: -32767) où la corrélation a échoué par exemple

## Paramètres

### Paramètres obligatoires
- `--mns` : MNS d'entrée
- `--out` : MNT de sortie
- `--reso` : Résolution du MNT en sortie
- `--cpu` : Nombre de CPUs à utiliser
- `--RepTra` : Répertoire de travail

### Paramètres optionnels
- `--masque` : Masque sol/sursol
- `--groundval` : Valeur du masque pour le sol (défaut: 0)
- `--init` : Initialisation (par défaut le MNS)
- `--nodata_ext` : Valeur du no_data sur les bords de chantier (défaut: -32768)
- `--nodata_int` : Valeur du no_data pour les trous intérieurs (défaut: -32767)
- `--sigma` : Précision du Z MNS (défaut: 0.5)
- `--regul` : Rigidité de la nappe (défaut: 0.01)
- `--tile` : Taille de la tuile (défaut: 300)
- `--pad` : Recouvrement entre tuiles (défaut: 120)
- `--norme` : Choix de la norme (défaut: hubertukey)
- `--clean` : Supprimer les fichiers temporaires

# 🧪 Environnement de Test PDAL

Cet environnement permet de tester **PDAL** (Point Data Abstraction Library) en isolation, en comparaison avec **SAGA**, avant d'entreprendre la migration dans le pipeline GEMAUT.

## 📁 Structure

```
test_pdal/
├── data/                    # Données de test (MNS_IN.tif)
├── scripts/                 # Scripts de test
│   ├── test_pdal_basic.py      # Tests de base PDAL
│   ├── test_pdal_morphology.py # Tests des opérations morphologiques
│   └── benchmark_pdal_vs_saga.py # Comparaison performance
├── output/                  # Résultats des tests
│   ├── pdal_results/        # Sorties PDAL
│   └── saga_results/        # Sorties SAGA
└── README.md               # Ce fichier
```

## 🚀 Installation

### 1. Créer l'environnement conda
```bash
conda create -n pdal_test python=3.11
conda activate pdal_test
```

### 2. Installer PDAL
```bash
conda install -c conda-forge pdal pdal-python
```

### 3. Vérifier l'installation
```bash
python3 -c "import pdal; print(pdal.__version__)"
```

### 4. Préparer les données de test
```bash
# Copier votre fichier MNS de test
cp /path/to/your/MNS_IN.tif data/
```

## 🧪 Exécution des tests

### Test de base PDAL
```bash
python3 scripts/test_pdal_basic.py
```

### Test des opérations morphologiques
```bash
python3 scripts/test_pdal_morphology.py
```

### Benchmark PDAL vs SAGA
```bash
python3 scripts/benchmark_pdal_vs_saga.py
```

## 🎯 Objectifs

- **Tester PDAL** en isolation
- **Comparer les performances** avec SAGA
- **Valider la compatibilité** des résultats
- **Prendre une décision** sur la migration

## 📚 Ressources

- [Site officiel PDAL](https://pdal.io/)
- [Documentation Python](https://pdal.io/python.html)
- [Filtres morphologiques](https://pdal.io/stages/filters.morphology.html)

---

**Cet environnement vous permettra de faire un choix éclairé sur la migration vers PDAL !** 🎯
