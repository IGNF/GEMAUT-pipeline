# GEMAUT Pipeline - Version Refactorisée

## Vue d'ensemble

Cette version refactorisée du pipeline GEMAUT (Génération de Modèles Automatiques de Terrain) a été conçue pour améliorer la maintenabilité, la lisibilité et la modularité du code original.

## Structure du projet

```
GEMAUT-pipeline/
├── config.py                 # Configuration centralisée (constantes, paramètres)
├── gemaut_config.py          # Classe de configuration avec validation
├── image_utils.py            # Utilitaires pour le traitement d'images raster
├── tile_processor.py         # Découpage et assemblage des tuiles
├── gemo_executor.py          # Exécution de GEMO en parallèle
├── saga_integration.py       # Intégration avec SAGA
├── gemaut_pipeline.py        # Pipeline principal refactorisé
├── script_gemaut.py          # Script original (conservé pour référence)
└── README_REFACTORED.md      # Ce fichier
```

## Améliorations apportées

### 1. **Configuration centralisée**
- Toutes les constantes et paramètres par défaut dans `config.py`
- Classe `GEMAUTConfig` avec validation automatique des paramètres
- Gestion centralisée des chemins de fichiers temporaires

### 2. **Modularité**
- Séparation claire des responsabilités en modules spécialisés
- Classes dédiées pour chaque type d'opération
- Réutilisabilité des composants

### 3. **Gestion d'erreurs améliorée**
- Logging structuré avec différents niveaux
- Messages d'erreur centralisés et informatifs
- Validation des paramètres d'entrée

### 4. **Maintenabilité**
- Code auto-documenté avec docstrings
- Noms de variables et fonctions explicites
- Structure orientée objet claire

### 5. **Extensibilité**
- Architecture modulaire facilitant l'ajout de nouvelles fonctionnalités
- Interfaces claires entre les modules
- Configuration flexible

## Utilisation

### Installation des dépendances

```bash
pip install rasterio numpy scipy tqdm loguru
```

### Exécution

```bash
python gemaut_pipeline.py --mns /chemin/vers/MNS.tif --out /chemin/vers/MNT.tif --reso 4 --cpu 24 --RepTra /chemin/vers/RepTra
```

### Paramètres disponibles

#### Paramètres obligatoires
- `--mns`: Fichier MNS d'entrée
- `--out`: Fichier MNT de sortie
- `--reso`: Résolution du MNT en sortie (mètres)
- `--cpu`: Nombre de CPUs à utiliser
- `--RepTra`: Répertoire de travail

#### Paramètres optionnels
- `--masque`: Fichier masque sol/sursol (calculé automatiquement si non fourni)
- `--groundval`: Valeur du masque pour le sol (défaut: 0)
- `--init`: Fichier d'initialisation (défaut: MNS d'entrée)
- `--sigma`: Précision du Z MNS (défaut: 0.5)
- `--regul`: Rigidité de la nappe (défaut: 0.01)
- `--tile`: Taille des tuiles (défaut: 300)
- `--pad`: Recouvrement entre tuiles (défaut: 120)
- `--norme`: Norme de robustesse (défaut: hubertukey)
- `--nodata_ext`: Valeur NoData externe (défaut: -32768)
- `--nodata_int`: Valeur NoData interne (défaut: -32767)
- `--clean`: Supprimer les fichiers temporaires

## Modules détaillés

### `config.py`
Contient toutes les constantes et paramètres par défaut :
- Paramètres GEMO (sigma, regul, norme, etc.)
- Valeurs NoData
- Paramètres SAGA
- Messages de logging
- Extensions de fichiers

### `gemaut_config.py`
Classe `GEMAUTConfig` qui :
- Valide les paramètres d'entrée
- Configure les chemins de fichiers temporaires
- Fournit des méthodes utilitaires pour accéder aux paramètres

### `image_utils.py`
Utilitaires pour le traitement d'images :
- `RasterProcessor`: Opérations de base sur les rasters
- `HoleFiller`: Remplissage des trous dans les images
- `MaskProcessor`: Traitement des masques
- `DataReplacer`: Remplacement de valeurs dans les images

### `tile_processor.py`
Gestion des tuiles :
- `TileCalculator`: Calcul des dimensions et nombres de tuiles
- `TileCutter`: Découpage des images en tuiles
- `TileAssembler`: Assemblage des tuiles en image finale

### `gemo_executor.py`
Exécution de GEMO :
- `GEMOExecutor`: Exécution parallèle de GEMO sur les tuiles
- `GDALProcessor`: Opérations GDAL (rééchantillonnage)

### `saga_integration.py`
Intégration avec SAGA :
- `SAGAIntegration`: Calcul automatique du masque sol/sursol
- Validation de l'environnement SAGA
- Gestion des dépendances

### `gemaut_pipeline.py`
Pipeline principal qui :
- Orchestre toutes les étapes du traitement
- Gère le logging et la gestion d'erreurs
- Fournit une interface utilisateur claire

## Migration depuis l'ancienne version

### Avantages de la migration
1. **Code plus lisible** : Structure claire et documentation
2. **Maintenance facilitée** : Modules indépendants et réutilisables
3. **Débogage simplifié** : Logging structuré et messages d'erreur clairs
4. **Tests facilités** : Architecture modulaire permettant des tests unitaires
5. **Évolutivité** : Ajout facile de nouvelles fonctionnalités

### Compatibilité
- Interface de ligne de commande identique
- Même logique de traitement
- Résultats identiques à l'original

## Développement futur

### Ajouts possibles
1. **Tests unitaires** pour chaque module
2. **Interface graphique** basée sur la nouvelle architecture
3. **Configuration par fichier** (YAML/JSON)
4. **Monitoring en temps réel** du traitement
5. **Support de nouveaux formats** de données
6. **Optimisations de performance** supplémentaires

### Contribution
Pour contribuer au projet :
1. Respecter la structure modulaire existante
2. Ajouter des docstrings pour les nouvelles fonctions
3. Utiliser le système de logging centralisé
4. Tester les modifications sur des données d'exemple

## Support

Pour toute question ou problème :
1. Consulter les logs générés automatiquement
2. Vérifier la configuration des paramètres
3. S'assurer que toutes les dépendances sont installées
4. Consulter la documentation des modules individuels 