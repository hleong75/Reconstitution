# Guide d'utilisation amélioré

Ce document explique les améliorations apportées au pipeline de reconstruction 3D.

## Résumé des modifications

### 1. Suppression de l'utilisation des API ✅

Le programme n'utilise plus d'API externe (Google Street View, etc.). Toutes les données doivent être téléchargées manuellement.

### 2. Nettoyage intelligent des textures ✅

Le programme retire automatiquement les éléments temporaires des images :
- Voitures (surfaces réfléchissantes)
- Personnes (objets verticaux au niveau du sol)
- Objets en mouvement (détection de flou)

### 3. Paramètres en ligne de commande ✅

Vous pouvez maintenant spécifier la ville et le rayon directement :

```bash
python main.py --city "Rambouillet" --radius 10
python main.py --city "Paris" --radius 5
```

### 4. Tests complets ✅

Deux fichiers de tests garantissent la robustesse du programme :
- `test_main.py` : Tests complets avec 12 cas de test
- `validate_changes.py` : Validation légère sans dépendances

## Utilisation

### Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/hleong75/Reconstitution.git
cd Reconstitution
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

### Préparation des données

**Important** : Les API étant désactivées, vous devez télécharger manuellement les données.

#### Données LiDAR
- Source : https://geoservices.ign.fr/lidarhd
- Format : fichiers `.copc.laz`
- Emplacement : `data/lidar/`

#### Images Street View
- Format : JPG ou PNG
- Résolution recommandée : 2048x1024
- Emplacement : `data/streetview/`

### Lancement du programme

#### Utilisation basique
```bash
# Avec configuration par défaut
python main.py

# Avec ville et rayon personnalisés
python main.py --city "Lyon" --radius 15

# Avec configuration personnalisée
python main.py --config ma_config.yaml --city "Marseille" --radius 20
```

#### Paramètres disponibles

- `--city <nom>` : Nom de la ville (remplace la configuration)
- `--radius <km>` : Rayon en kilomètres (remplace la configuration)
- `--config <fichier>` : Fichier de configuration personnalisé (défaut : config.yaml)

#### Aide
```bash
python main.py --help
```

### Lancement des tests

```bash
# Tests complets (nécessite toutes les dépendances)
python test_main.py

# Validation légère (sans dépendances lourdes)
python validate_changes.py
```

## Fonctionnalités de nettoyage intelligent

Le système de nettoyage des textures utilise plusieurs techniques :

### 1. Détection des surfaces réfléchissantes
- Analyse de l'espace colorimétrique HSV
- Détection de luminosité élevée + faible saturation
- Identification des reflets métalliques (voitures, vitres)

### 2. Détection des objets verticaux
- Filtres de Sobel pour détecter les bords verticaux
- Focus sur le niveau du sol (personnes, poteaux)
- Suppression des petites régions isolées

### 3. Détection du flou de mouvement
- Analyse de la variance laplacienne
- Identification des régions floues (objets en mouvement)
- Seuillage adaptatif

### 4. Remplissage intelligent (Inpainting)
- Algorithme TELEA d'OpenCV
- Remplissage basé sur les textures environnantes
- Résultat naturel sans artefacts

## Exemples

### Exemple 1 : Reconstruction de Rambouillet
```bash
python main.py --city "Rambouillet" --radius 10
```

### Exemple 2 : Reconstruction de Paris (petit rayon)
```bash
python main.py --city "Paris" --radius 3
```

### Exemple 3 : Configuration personnalisée
```bash
python main.py --config config_custom.yaml --city "Bordeaux" --radius 8
```

## Robustesse

Le programme est conçu pour être robuste :

- ✅ Gestion des entrées vides
- ✅ Validation des données d'image
- ✅ Couleurs par défaut si pas d'images
- ✅ Journalisation complète des erreurs
- ✅ Validation des paramètres

## Structure du pipeline

1. **Chargement des nuages de points LiDAR**
2. **Chargement des images Street View**
3. **Nettoyage intelligent des images** (nouveau)
4. **Segmentation du nuage de points**
5. **Extraction des bâtiments et du sol**
6. **Génération du maillage 3D**
7. **Application des textures nettoyées** (amélioré)
8. **Export au format .3ds**

## Avantages

### Sans API
- ❌ Pas de coûts d'API
- ❌ Pas de clés API nécessaires
- ❌ Pas de limites de quota
- ✅ Contrôle total des données

### Nettoyage intelligent
- ✅ Modèles 3D plus propres
- ✅ Pas de voitures ni de personnes
- ✅ Textures permanentes uniquement
- ✅ Résultat professionnel

### Facilité d'utilisation
- ✅ Paramètres en ligne de commande
- ✅ Pas besoin d'éditer les fichiers
- ✅ Tests automatisés
- ✅ Documentation complète

## Dépannage

### Problème : "ModuleNotFoundError"
**Solution** : Installer les dépendances
```bash
pip install -r requirements.txt
```

### Problème : "No LiDAR files found"
**Solution** : Placer les fichiers .copc.laz dans `data/lidar/`

### Problème : "No Street View images found"
**Solution** : Placer les images JPG/PNG dans `data/streetview/`

### Problème : Bus error lors du lancement
**Solution** : Vérifier que toutes les dépendances sont installées
```bash
pip install --upgrade -r requirements.txt
```

## Tests

### Validation rapide
```bash
python validate_changes.py
```

Résultat attendu :
```
✓ main.py structure is correct
✓ config.yaml has API disabled
✓ texture_mapper.py has all cleaning methods
✓ test_main.py has comprehensive tests
✓ Documentation is present

Passed: 5/5
🎉 All validation tests passed!
```

### Tests complets
```bash
python test_main.py
```

12 tests au total :
- Analyse syntaxique des arguments
- Initialisation du pipeline
- Vérification de suppression d'API
- Nettoyage de texture
- Détection de surfaces réfléchissantes
- Détection d'objets verticaux
- Détection de flou de mouvement
- Génération de couleurs
- Pipeline de nettoyage d'images
- Robustesse avec entrées vides
- Robustesse avec images invalides

## Support

Pour toute question ou problème :
- Ouvrir un ticket sur GitHub : https://github.com/hleong75/Reconstitution/issues
- Consulter la documentation : IMPROVEMENTS.md, README.md

## Licence

MIT License
