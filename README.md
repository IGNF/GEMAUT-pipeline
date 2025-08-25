<p align="center">
  <img src="assets/logo.png" alt="GEMAUT" width="200" style="margin-right: 20px;"/>
  <img src="assets/Linux.png" alt="Linux" width="200"/>
</p>

# 🚀 GEMAUT - Génération de Modèles Automatiques de Terrain

**L'outil avancé pour le passage MNS > MNT sous Linux & Conda avec support intégré PDAL et SAGA**

## ✨ Nouvelles fonctionnalités

- **🔄 Calcul automatique de masques** avec `--auto-mask`
- **🎯 Choix de méthode** : SAGA ou PDAL avec `--mask-method`
- **⚡ Intégration native** de PDAL (Point Data Abstraction Library)
- **🛡️ Fallback automatique** vers SAGA si PDAL échoue
- **📊 Comparaison des méthodes** SAGA vs PDAL

---

## 🏗️ Installation

### Prérequis
- Conda (Miniconda ou Anaconda)
- Git

### Installation automatique
```bash
# Cloner le dépôt
git clone https://github.com/IGNF/GEMAUT-pipeline.git
cd GEMAUT-pipeline

# Créer l'environnement conda & l'activer
conda env create -n gemaut_env -f gemaut_env.yml
conda activate gemaut_env

# Rendre le script d'installation exécutable
chmod +x install_gemaut.sh

# Lancer l'installation
./install_gemaut.sh
```

---

## 🎯 Utilisation

### 1. Activer l'environnement
```bash
conda activate gemaut_env
```

### 2. Aide du script
```bash
python3 script_gemaut.py --help
```

### 3. Exemples d'utilisation

#### 🆕 **Calcul automatique de masque avec SAGA**
```bash
python3 script_gemaut.py \
    --mns /chemin/vers/MNS_in.tif \
    --out /chemin/vers/MNT_SAGA.tif \
    --reso 4 \
    --cpu 24 \
    --RepTra RepTra_SAGA \
    --auto-mask \
    --mask-method saga
```

#### 🆕 **Calcul automatique de masque avec PDAL**
```bash
python3 script_gemaut.py \
    --mns /chemin/vers/MNS_in.tif \
    --out /chemin/vers/MNT_PDAL.tif \
    --reso 4 \
    --cpu 24 \
    --RepTra RepTra_PDAL \
    --auto-mask \
    --mask-method pdal
```

#### 🆕 **Sélection automatique de la meilleure méthode**
```bash
python3 script_gemaut.py \
    --mns /chemin/vers/MNS_in.tif \
    --out /chemin/vers/MNT_AUTO.tif \
    --reso 4 \
    --cpu 24 \
    --RepTra RepTra_AUTO \
    --auto-mask \
    --mask-method auto
```

#### 📋 **Utilisation traditionnelle avec masque fourni**
```bash
python3 script_gemaut.py \
    --mns /chemin/vers/MNS_in.tif \
    --out /chemin/vers/MNT.tif \
    --reso 4 \
    --cpu 24 \
    --RepTra /chemin/vers/RepTra \
    --masque /chemin/vers/masque.tif \
    --nodata_ext -32768 \
    --nodata_int -32767
```

---

## 🔧 Paramètres

### Paramètres obligatoires
- `--mns` : MNS d'entrée
- `--out` : MNT de sortie
- `--reso` : Résolution du MNT en sortie
- `--cpu` : Nombre de CPUs à utiliser
- `--RepTra` : Répertoire de travail

### 🆕 **Nouveaux paramètres de masque automatique**
- `--auto-mask` : Activer le calcul automatique de masque
- `--mask-method` : Méthode de calcul (`saga`, `pdal`, ou `auto`)

### Paramètres optionnels
- `--masque` : Masque sol/sursol (ignoré si `--auto-mask` est activé)
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

---

## 🎯 Méthodes de calcul de masque

### **SAGA GIS** 🌍
- **Avantages** : Stable, éprouvé, bonnes performances
- **Utilisation** : `--mask-method saga`
- **Fichiers générés** : 
  - `MASQUE_compute.tif` (masque calculé)
  - `MASQUE_SAGA_CORRIGE_apres_correction.tif` (masque aligné géographiquement)

### **PDAL (Point Data Abstraction Library)** 🚀
- **Avantages** : Algorithmes avancés, optimisé pour les nuages de points
- **Utilisation** : `--mask-method pdal`
- **Fichiers générés** : 
  - `MASQUE_compute.tif` (masque calculé)
  - `pdal_pipeline_used.json` (pipeline PDAL utilisé)

### **Sélection automatique** 🤖
- **Utilisation** : `--mask-method auto`
- **Logique** : Teste PDAL en premier, fallback vers SAGA si échec

---

## 📁 Structure des données

### MNS d'entrée
Le MNS d'entrée doit avoir des valeurs de no_data différentes pour :
- **Bords de chantier** (`--nodata_ext`, défaut: -32768)
- **Trous intérieurs** (`--nodata_int`, défaut: -32767) où la corrélation a échoué

### Masques générés
- **Résolution** : Identique au MNS d'entrée
- **Format** : Binaire (0 = sol, 1 = sursol)
- **Alignement** : Automatiquement corrigé pour correspondre au MNS

---

## 🔍 Configuration avancée

### Fichier de configuration YAML
```yaml
# config_exemple_avec_masque_auto.yaml
mask_computation:
  auto_mask_computation: true
  mask_method: "auto"  # "saga", "pdal", ou "auto"

pdal:
  csf_max_iterations: 500
  csf_cloth_resolution: 0.5
  csf_class_threshold: 0.5
  csf_rigidness: 1
  csf_time_step: 0.65
  csf_iterations: 500
  csf_concave_hull: true
```

### Variables d'environnement
```bash
export GEMAUT_LOG_LEVEL=INFO
export GEMAUT_TEMP_DIR=/tmp/gemaut
```

---

## 🧪 Tests et validation

### Test de l'intégration
```bash
python3 test_mask_integration.py
```

### Démonstration des fonctionnalités
```bash
python3 demo_masque_auto.py
```

### Vérification de compatibilité
```bash
python3 test_compatibility_check.py
```

---

## 📚 Documentation

- **📖 [README Calcul Masque Auto](README_CALCUL_MASQUE_AUTO.md)** : Guide détaillé des nouvelles fonctionnalités
- **🔧 [Configuration](config_exemple_avec_masque_auto.yaml)** : Exemples de configuration
- **🧪 [Tests](tests/README_TESTS.md)** : Guide des tests et validation

---

## 🆘 Dépannage

### Problèmes courants

#### **PDAL non disponible**
```bash
# Vérifier l'installation
conda list pdal

# Réinstaller si nécessaire
conda install -c conda-forge pdal pdal-python
```

#### **SAGA non disponible**
```bash
# Vérifier l'installation
saga_cmd --version

# Réinstaller si nécessaire
conda install -c conda-forge saga
```

#### **Erreurs de compatibilité géographique**
- Les masques SAGA peuvent avoir des différences géographiques mineures
- Le pipeline corrige automatiquement ces différences
- Vérifiez les logs pour plus de détails

---

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📄 Licence

Ce projet est sous licence [LICENSE](LICENSE).

---

## 🆕 **Changelog récent**

### Version actuelle
- ✅ **Intégration complète PDAL** pour le calcul de masques
- ✅ **Calcul automatique de masques** avec `--auto-mask`
- ✅ **Sélection de méthode** SAGA/PDAL/Auto
- ✅ **Fallback automatique** vers SAGA si PDAL échoue
- ✅ **Documentation complète** des nouvelles fonctionnalités

---

**🎯 GEMAUT : Plus qu'un pipeline, une solution complète pour la génération de MNT !**
