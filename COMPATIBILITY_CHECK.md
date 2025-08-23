# Vérification de Compatibilité MNS/Masque

## Vue d'ensemble

Cette fonctionnalité ajoute une vérification automatique au début du pipeline GEMAUT pour s'assurer que le MNS (Modèle Numérique de Surface) et le masque sont compatibles avant de commencer le traitement.

## Fonctionnalités

### 1. Vérification Automatique
- **Dimensions** : Vérifie que le MNS et le masque ont la même hauteur et largeur
- **CRS** : Vérifie que les deux fichiers utilisent le même système de coordonnées
- **Transformation géographique** : Vérifie que les transformations sont identiques
- **Bornes géographiques** : Vérifie que les étendues spatiales correspondent

### 2. Intégration dans le Pipeline
- **Vérification précoce** : Effectuée dès le début du pipeline
- **Double vérification** : Vérification initiale + vérification après calcul du masque (si applicable)
- **Arrêt automatique** : Le pipeline s'arrête si une incompatibilité est détectée

### 3. Messages d'Information
- ✅ **Succès** : Affichage des informations de compatibilité
- ❌ **Erreur** : Détail des problèmes détectés avec arrêt du pipeline
- 📊 **Détails** : Affichage des dimensions et CRS des deux fichiers

## Utilisation

### Dans le Code
```python
from image_utils import RasterProcessor

# Vérification de compatibilité
compatible, details = RasterProcessor.validate_raster_compatibility(
    mns_path, 
    mask_path
)

if not compatible:
    print("Incompatibilité détectée:")
    for issue in details['issues']:
        print(f"  - {issue}")
```

### Dans le Pipeline GEMAUT
La vérification est automatiquement effectuée :
1. **Au début** : Si un fichier masque est fourni
2. **Après calcul** : Si le masque est calculé par SAGA

## Messages de Sortie

### Compatibilité Validée
```
✅ Compatibilité MNS/Masque validée
  Dimensions: 1000x1000
  CRS: EPSG:2154
```

### Incompatibilité Détectée
```
❌ INCOMPATIBILITÉ DÉTECTÉE entre le MNS et le masque!
Problèmes identifiés:
  - Hauteur différente: MNS=1000, Masque=800
  - CRS différent: MNS=EPSG:2154, Masque=EPSG:4326

Informations détaillées:
  MNS: 1000x1000, CRS: EPSG:2154
  Masque: 800x800, CRS: EPSG:4326
```

## Gestion des Erreurs

### Types d'Erreurs Détectées
1. **Dimensions différentes** : Hauteur ou largeur non correspondantes
2. **CRS différent** : Systèmes de coordonnées incompatibles
3. **Transformation différente** : Paramètres géographiques non alignés
4. **Bornes différentes** : Étendues spatiales non correspondantes

### Actions Automatiques
- **Arrêt du pipeline** : Évite les erreurs de traitement
- **Logs détaillés** : Facilite le diagnostic des problèmes
- **Messages informatifs** : Guide l'utilisateur vers la résolution

## Résolution des Problèmes

### Problèmes Courants
1. **Dimensions différentes** : Rééchantillonner le masque à la résolution du MNS
2. **CRS différent** : Reprojeter le masque dans le CRS du MNS
3. **Bornes différentes** : Recadrer le masque sur l'étendue du MNS

### Outils Recommandés
- **GDAL** : Pour la reprojection et le rééchantillonnage
- **QGIS** : Interface graphique pour la vérification et correction
- **Python** : Scripts de correction automatisés

## Tests

### Script de Test
Un script de test est fourni : `test_compatibility_check.py`

```bash
python test_compatibility_check.py
```

### Tests Inclus
- Vérification avec fichiers existants
- Gestion des fichiers inexistants
- Affichage des informations des fichiers

## Avantages

1. **Détection précoce** : Évite les erreurs en cours de traitement
2. **Gain de temps** : Arrêt immédiat en cas de problème
3. **Diagnostic clair** : Messages d'erreur informatifs
4. **Intégration transparente** : Aucune modification de l'interface utilisateur
5. **Robustesse** : Améliore la fiabilité du pipeline

## Maintenance

### Ajout de Nouvelles Vérifications
Pour ajouter de nouvelles vérifications, modifier la méthode `validate_raster_compatibility` dans `image_utils.py`.

### Personnalisation des Messages
Les messages peuvent être personnalisés en modifiant les chaînes dans le pipeline principal. 