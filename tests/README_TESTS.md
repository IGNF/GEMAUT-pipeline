# Guide des Tests Unitaires - GEMAUT Pipeline

## Qu'est-ce qu'un test unitaire ?

Un **test unitaire** est un petit programme qui vérifie qu'une fonction ou une classe fait bien ce qu'elle doit faire. C'est comme un "contrôle qualité" automatique pour votre code.

## Structure d'un test unitaire

Chaque test suit le pattern **AAA** (Arrange-Act-Assert) :

```python
def test_ma_fonction(self):
    # Arrange (Préparer) - préparer les données de test
    input_data = [1, 2, 3]
    
    # Act (Agir) - appeler la fonction à tester
    result = ma_fonction(input_data)
    
    # Assert (Vérifier) - vérifier que le résultat est correct
    self.assertEqual(result, 6)
```

## Exemple concret : `test_raster_processor.py`

### 1. **setUp()** - Préparation
```python
def setUp(self):
    """Appelé avant chaque test - prépare les données"""
    # Créer un fichier raster temporaire pour les tests
    self.test_raster_path = "test_raster.tif"
    # Créer des données de test
    self.test_data = np.array([[1.0, 2.0], [3.0, 4.0]])
```

### 2. **tearDown()** - Nettoyage
```python
def tearDown(self):
    """Appelé après chaque test - nettoie"""
    # Supprimer les fichiers temporaires
    shutil.rmtree(self.temp_dir)
```

### 3. **Tests individuels**
```python
def test_get_image_dimensions(self):
    """Test de la méthode get_image_dimensions"""
    # Act - appeler la méthode
    height, width = RasterProcessor.get_image_dimensions(self.test_raster_path)
    
    # Assert - vérifier le résultat
    self.assertEqual(height, 4, "La hauteur devrait être 4")
    self.assertEqual(width, 4, "La largeur devrait être 4")
```

## Types de tests

### 1. **Tests unitaires** (tests simples)
- Testent une fonction isolée
- Vérifient un comportement spécifique
- Rapides à exécuter

### 2. **Tests d'intégration** (tests complexes)
- Testent plusieurs fonctions ensemble
- Vérifient un workflow complet
- Plus lents mais plus complets

### 3. **Tests de cas d'erreur**
```python
def test_file_not_found(self):
    """Test avec un fichier inexistant"""
    with self.assertRaises(Exception):
        RasterProcessor.get_image_dimensions("fichier_inexistant.tif")
```

## Comment exécuter les tests

### 1. **Exécuter tous les tests**
```bash
cd tests/
python -m unittest discover -v
```

### 2. **Exécuter un fichier de test spécifique**
```bash
python test_raster_processor.py
```

### 3. **Exécuter un test spécifique**
```bash
python -m unittest tests.test_raster_processor.TestRasterProcessor.test_get_image_dimensions
```

## Avantages des tests unitaires

1. **Détection d'erreurs rapide** - vous savez immédiatement si quelque chose ne marche plus
2. **Documentation vivante** - les tests montrent comment utiliser votre code
3. **Refactoring sécurisé** - vous pouvez modifier le code sans casser les fonctionnalités
4. **Confiance** - vous êtes sûr que votre code fonctionne
5. **Développement plus rapide** - moins de bugs à corriger

## Bonnes pratiques

### 1. **Nommage des tests**
```python
def test_get_image_dimensions_returns_correct_size(self):  # Nom descriptif
def test_contains_valid_data_with_only_nodata(self):       # Décrit le cas de test
```

### 2. **Un test = une vérification**
```python
# ❌ Mauvais - plusieurs vérifications dans un test
def test_image_processing(self):
    self.assertEqual(height, 4)
    self.assertEqual(width, 4)
    self.assertTrue(has_valid_data)
    self.assertEqual(info['crs'], 'EPSG:4326')

# ✅ Bon - un test par vérification
def test_image_height(self):
    self.assertEqual(height, 4)

def test_image_width(self):
    self.assertEqual(width, 4)
```

### 3. **Données de test isolées**
```python
# ❌ Mauvais - dépend d'un fichier externe
def test_process_real_file(self):
    result = process_file("real_data.tif")

# ✅ Bon - crée ses propres données de test
def test_process_test_data(self):
    test_data = create_test_data()
    result = process_data(test_data)
```

## Exemple d'utilisation dans votre workflow

1. **Écrire le test d'abord** (TDD - Test Driven Development)
2. **Exécuter le test** - il échoue (normal, le code n'existe pas encore)
3. **Écrire le code** pour faire passer le test
4. **Exécuter le test** - il passe ✅
5. **Refactoriser** si nécessaire
6. **Répéter** pour la prochaine fonctionnalité

## Prochaines étapes

1. **Exécutez le test d'exemple** pour voir comment ça marche
2. **Créez des tests** pour vos autres classes (`HoleFiller`, `MaskProcessor`, etc.)
3. **Intégrez les tests** dans votre workflow de développement
4. **Automatisez** l'exécution des tests (CI/CD)

---

**Conseil** : Commencez par tester les fonctions simples, puis progressez vers les plus complexes. Mieux vaut avoir quelques tests qui marchent que beaucoup qui échouent ! 