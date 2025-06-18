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
