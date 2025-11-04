# Reconstitution - Pipeline de Reconstruction 3D de Ville

Reconstruction automatique 3D de la ville autour de Rambouillet (rayon de 10 km) utilisant les nuages de points LiDAR HD IGN et les images panoramiques Street View.

## Vue d'ensemble

Ce pipeline utilise la segmentation basée sur l'IA pour filtrer les bâtiments et le sol à partir de nuages de points LiDAR, génère des maillages 3D, applique des textures à partir d'images Street View et exporte le modèle final au format .3ds pour une utilisation dans Blender ou 3ds Max.

## Fonctionnalités

- **Traitement LiDAR** : Chargement et traitement des fichiers de nuages de points .copc.laz de l'IGN
- **Intégration Street View** : Utilisation d'images panoramiques pour le mappage de textures
- **Segmentation IA** : Segmentation de nuages de points basée sur l'apprentissage profond (sol, bâtiments, végétation)
- **Génération de Maillage 3D** : Plusieurs algorithmes de reconstruction (Poisson, Ball Pivoting, Alpha Shape)
- **Mappage de Textures** : Application de textures à partir d'images Street View sur les modèles 3D
- **Multiples Formats d'Export** : .3ds, .obj, .ply, .stl

## Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/hleong75/Reconstitution.git
cd Reconstitution
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

Ou utiliser le script de configuration :
```bash
python setup.py
```

## Préparation des Données

### Option 1: Téléchargement Automatique (Recommandé)

Configurez le téléchargement automatique des données :
```bash
python setup_download.py config
```

Cela vous guidera pour configurer :
- Clé API Google Street View pour le téléchargement automatique d'images
- Préférences de téléchargement (nombre d'images, résolution)

Ensuite, exécutez le pipeline - il téléchargera automatiquement les données :
```bash
python main.py
```

### Option 2: Téléchargement Manuel

#### Données LiDAR
Placez vos fichiers .copc.laz dans le répertoire `data/lidar/` :
```bash
mkdir -p data/lidar
# Copiez vos fichiers LiDAR ici
```

**Sources de données LiDAR HD IGN :**
- [IGN Géoportail - LiDAR HD](https://geoservices.ign.fr/lidarhd)
- Format : Cloud Optimized Point Cloud (COPC) .laz
- Système de coordonnées : Lambert 93

### Images Street View

**Option A: Téléchargement Automatique**
```bash
# Configurez d'abord la clé API
python setup_download.py config
# Puis exécutez main.py - il téléchargera automatiquement
```

**Option B: Téléchargement Manuel**
Placez vos images panoramiques dans le répertoire `data/streetview/` :
```bash
mkdir -p data/streetview
# Copiez vos images panoramiques ici
# Ou utilisez des outils comme streetget: https://www.di.ens.fr/willow/research/streetget/
```

**Recommandations pour les images :**
- Format : JPG ou PNG
- Résolution : 2048x1024 ou supérieure
- Avec données GPS EXIF si possible

## Configuration

Éditez `config.yaml` pour personnaliser :

```yaml
location:
  name: "Rambouillet"
  center_lat: 48.6439  # Latitude du centre
  center_lon: 1.8294   # Longitude du centre
  radius_km: 10        # Rayon en kilomètres
```

### Paramètres de Traitement LiDAR

```yaml
input:
  lidar:
    voxel_size: 0.05  # Résolution de sous-échantillonnage (mètres)
    min_points_per_voxel: 10
```

### Paramètres de Génération de Maillage

```yaml
mesh_generation:
  method: "poisson"     # ou "ball_pivoting", "alpha_shape"
  poisson_depth: 9      # 8-10 pour échelle urbaine
  simplification_ratio: 0.9  # Conserver 90% des triangles
```

## Utilisation

Exécuter le pipeline complet de reconstruction :
```bash
python main.py
```

Le pipeline va :
1. Charger et traiter les nuages de points LiDAR
2. Charger les images Street View
3. Segmenter le nuage de points avec l'IA
4. Extraire les bâtiments et le sol
5. Générer le maillage 3D
6. Appliquer les textures
7. Exporter au format .3ds (et autres formats)

## Sortie

Les modèles 3D finaux seront enregistrés dans le répertoire `output/` :
- `rambouillet_3d_model.3ds` - Sortie principale pour 3ds Max
- `rambouillet_3d_model.obj` - Format OBJ pour Blender
- `rambouillet_3d_model.ply` - Format PLY (préserve les couleurs)
- `rambouillet_3d_model.stl` - Format STL (impression 3D)

## Test avec Données de Démo

Vous n'avez pas de vraies données ? Testez avec des données synthétiques :

```bash
# Créer des données de démo
python demo.py create

# Exécuter le pipeline avec la démo
python demo.py run
```

Cela crée une ville synthétique simple avec des bâtiments et du sol.

## Architecture du Pipeline

```
Données LiDAR (.copc.laz) ──┐
                            ├─> Segmentation IA ─> Génération Maillage ─> Mappage Textures ─> Export (.3ds)
Images Street View ─────────┘
```

### Modules

- `lidar_processor.py` - Chargement et prétraitement des nuages de points LiDAR
- `streetview_processor.py` - Chargement et traitement des images Street View
- `segmentation.py` - Segmentation de nuages de points basée sur l'IA
- `mesh_generator.py` - Génération de maillages 3D à partir de nuages de points
- `texture_mapper.py` - Application de textures à partir d'images
- `exporter.py` - Export de modèles vers différents formats

## Modèle IA

Le pipeline utilise une architecture basée sur PointNet pour la segmentation sémantique avec les classes :
- Sol (ground)
- Bâtiment (building)
- Végétation (vegetation)
- Autre (other)

Les poids pré-entraînés peuvent être placés dans `models/segmentation_weights.pth`.

## Optimisation des Performances

### Pour Grandes Zones (>10 GB)

1. **Augmenter la taille du voxel :**
   ```yaml
   voxel_size: 0.2  # ou plus
   ```

2. **Traiter par morceaux :**
   - Diviser la zone en régions plus petites
   - Traiter séparément et fusionner

3. **Utiliser l'accélération GPU :**
   - PyTorch utilisera automatiquement CUDA si disponible
   - Vérifier avec : `python -c "import torch; print(torch.cuda.is_available())"`

### Gestion de la Mémoire

- Traitement nuage de points : 8 GB RAM minimum
- Segmentation IA : 4 GB mémoire GPU recommandée
- Génération de maillage : 16 GB RAM pour grandes zones

## Dépannage

### Problème : "No .copc.laz files found"
**Solution :** Vérifiez le format de fichier, assurez-vous que les fichiers sont dans `data/lidar/`

### Problème : "CUDA out of memory"
**Solution :** 
- Réduire `voxel_size` pour sous-échantillonner davantage
- Traiter des zones plus petites
- Utiliser CPU : définir `CUDA_VISIBLE_DEVICES=-1`

### Problème : "Le maillage a des trous"
**Solution :**
- Passer à `method: "poisson"` 
- Augmenter `poisson_depth`
- Vérifier la densité du nuage de points

### Problème : "Mauvaise qualité de texture"
**Solution :**
- Augmenter `resolution` dans texture_mapping
- Utiliser des images Street View de meilleure qualité
- S'assurer que les images ont des métadonnées GPS

## Documentation Supplémentaire

- **USAGE.md** - Guide d'utilisation détaillé (en anglais)
- **ARCHITECTURE.md** - Vue d'ensemble de l'architecture (en anglais)
- **EXAMPLES.md** - Exemples de configurations (en anglais)

## Exigences Système

- Python 3.8+
- 8 GB RAM minimum (16 GB recommandé)
- GPU avec support CUDA recommandé (optionnel)
- Espace disque : ~20 GB pour données et sorties

### Dépendances Principales

- Open3D - Manipulation de nuages de points et maillages
- PyTorch - Apprentissage profond pour segmentation
- NumPy - Opérations numériques
- OpenCV - Traitement d'images
- Trimesh - Conversion de formats de maillage
- laspy - Support de fichiers LAZ

Voir `requirements.txt` pour la liste complète.

## Prochaines Étapes

1. **Affiner la configuration** pour votre zone spécifique
2. **Entraîner un modèle IA personnalisé** sur vos données LiDAR
3. **Ajuster la qualité du maillage** vs. compromis de performance
4. **Importer dans Blender/3ds Max** pour l'édition finale

## Support

Pour les problèmes ou questions, ouvrez un ticket sur GitHub :
https://github.com/hleong75/Reconstitution/issues

## Licence

MIT License

## Auteur

hleong75
