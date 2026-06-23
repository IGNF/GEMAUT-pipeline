# 📦 Installation de GEMAUT

GEMAUT peut être installé de deux façons : via pip (recommandé) ou avec le script bash d'installation complet.

## 🚀 Installation rapide (pip)

### Étape 1 : Installer les dépendances externes (SAGA + GEMO)

Les dépendances C++ (SAGA-GIS et GEMO) doivent être installées une seule fois :

```bash
# Créer et activer un environnement conda (avec outils de compilation inclus)
conda env create -f gemaut_env.yml
conda activate gemaut_env

# Installer les dépendances système (SAGA + GEMO)
./scripts/install_deps.sh

# Recharger l'environnement
conda deactivate && conda activate gemaut_env
```

### Étape 2 : Installer GEMAUT avec pip

```bash
# Installation standard
pip install .

# OU installation depuis PyPI (quand disponible)
# pip install gemaut
```

### Étape 3 : Vérifier l'installation

```bash
gemaut --help
```

---

## 🔧 Installation complète (script bash)

Si vous préférez l'ancienne méthode avec un seul script :

```bash
# Créer et activer un environnement conda
conda env create -f gemaut_env.yml
conda activate gemaut_env

# Installer GEMAUT et toutes ses dépendances
./scripts/install_gemaut.sh

# Recharger l'environnement
conda deactivate && conda activate gemaut_env
```

---

## 📋 Prérequis

### Environnement conda
Le fichier `gemaut_env.yml` inclut automatiquement :
- **CMake** : pour compiler SAGA et GEMO
- **Make** : pour l'installation
- **cxx-compiler** : Compilateur C++ (pas besoin de sudo !)
- **Python** et toutes les dépendances Python

Tout est installé automatiquement avec `conda env create -f gemaut_env.yml` !

### Dépendances Python
Les dépendances Python sont automatiquement installées avec pip :
- rasterio >= 1.3.0
- numpy >= 1.21.0
- scipy >= 1.7.0
- tqdm >= 4.62.0
- loguru >= 0.6.0
- PyYAML >= 6.0

---

## 🗑️ Désinstallation

### Désinstaller GEMAUT (pip)
```bash
pip uninstall gemaut
```

### Désinstaller les dépendances externes
```bash
./uninstall_deps.sh
```

### Désinstallation complète (ancienne méthode)
```bash
./uninstall_gemaut.sh
```

---

## 🐛 Problèmes courants

### `gemaut: command not found`
Vérifiez que vous êtes dans le bon environnement conda :
```bash
conda activate gemaut_env
```

### Erreur lors de la compilation de SAGA
Assurez-vous d'avoir un compilateur C++ installé :
```bash
# Vérifier g++
g++ --version

# Ou vérifier le compilateur conda
x86_64-conda-linux-gnu-g++ --version
```

### `opencv2/core/types_c.h: No such file or directory` (SAGA)
Ce message apparaît si OpenCV 4+ est détecté lors de la compilation de SAGA : le module
`imagery_opencv` de SAGA utilise l'ancienne API C d'OpenCV, supprimée depuis OpenCV 4.

GEMAUT n'utilise pas ce module (seulement `grid_filter` pour le masque). Le script
`install_deps.sh` désactive donc sa compilation avec `-DWITH_TOOLS_OPENCV=OFF`.

Si vous compilez SAGA manuellement, ajoutez cette option à `cmake`. Pour corriger un
environnement conda déjà créé avec OpenCV 5 :
```bash
conda install -c conda-forge "libopencv>=4.5,<5" "opencv>=4.5,<5" "py-opencv>=4.5,<5"
```
Puis relancez `./scripts/install_deps.sh`.

### `undefined reference to wxImage` (SAGA, module io_webservices)
En mode headless (`-DWITH_GUI=OFF`), le module `io_webservices` de SAGA lie seulement
`wxWidgets html` alors qu'il utilise `wxImage` (composant `core`). Le script
`install_deps.sh` applique automatiquement le correctif après le clonage.

Pour un build manuel déjà en cours :
```bash
sed -i 's/COMPONENTS html/COMPONENTS core html/' \
  saga-gis-code/saga-gis/src/tools/io/io_webservices/CMakeLists.txt
cd saga-gis-code/saga-gis/build && cmake .. && make -j$(nproc)
```

### `ModuleNotFoundError: No module named 'SAGA'`
Réinstallez GEMAUT :
```bash
pip install -e . --force-reinstall
```

---

## 📚 Utilisation

Après l'installation, consultez le README principal pour les exemples d'utilisation :
```bash
# Afficher l'aide
gemaut --help

# Exemple simple
gemaut --mns input.tif --out output.tif --reso 4 --cpu 24
```

---

## 🔄 Mise à jour

### Avec pip (mode développement)
```bash
cd /path/to/GEMAUT-pipeline
git pull
pip install -e . --force-reinstall
```

### Avec le script bash
```bash
./install_gemaut.sh
```

---

## ✉️ Support

Pour toute question ou problème :
- **Auteur** : Nicolas Champion
- **Email** : nicolas.champion@ign.fr
- **Issues** : https://github.com/IGNF/GEMAUT-pipeline/issues
