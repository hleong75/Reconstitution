# Guide d'Utilisation - Reconstitution 3D

## Aperçu Rapide

Ce programme reconstruit automatiquement des modèles 3D de villes en utilisant:
- **Données LiDAR HD** de l'IGN (gratuit, public)
- **Images Street View** de Mapillary (gratuit, nécessite un token)

**AUCUNE API Google payante n'est utilisée!**

## Installation Rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Voir les informations sur les sources de données
python download.py info

# 3. Configurer Mapillary (optionnel, pour les images)
python download.py setup-mapillary

# 4. Télécharger les données automatiquement
python download.py now

# 5. Lancer la reconstruction
python main.py --city "Rambouillet" --radius 10
```

## Étape 1: Comprendre les Sources de Données

### LiDAR HD IGN (Gratuit)

- **Source**: Institut National de l'Information Géographique
- **Couverture**: Tout le territoire français
- **Format**: Fichiers COPC LAZ (nuages de points)
- **Résolution**: Haute densité (10+ points/m²)
- **Coût**: GRATUIT - données publiques
- **Site**: https://geoservices.ign.fr/lidarhd

### Images Mapillary (Gratuit avec token)

- **Source**: Images contributives de Mapillary
- **Couverture**: Monde entier
- **Format**: Images panoramiques JPEG
- **Résolution**: Jusqu'à 2048x1024
- **Coût**: GRATUIT - nécessite un token API gratuit
- **Site**: https://www.mapillary.com/
- **Token**: https://www.mapillary.com/developer

## Étape 2: Configuration

### Option A: Configuration Automatique

```bash
# Tester la configuration actuelle
python download.py test

# Configurer le token Mapillary
python download.py setup-mapillary
```

### Option B: Configuration Manuelle

Éditez `config.yaml`:

```yaml
location:
  name: "Rambouillet"  # Votre ville
  center_lat: 48.6439  # Latitude
  center_lon: 1.8294   # Longitude
  radius_km: 10        # Rayon en km

download:
  enable_lidar: true       # Télécharger LiDAR
  enable_streetview: true  # Télécharger images
  max_images: 50          # Nombre max d'images
  mapillary_token: ""     # Votre token Mapillary
```

## Étape 3: Téléchargement des Données

### Téléchargement Automatique

```bash
# Télécharger tout automatiquement
python download.py now
```

Le programme va:
1. Télécharger les tuiles LiDAR HD de l'IGN pour votre zone
2. Télécharger des images Mapillary (si token configuré)
3. Sauvegarder dans `data/lidar/` et `data/streetview/`

### Téléchargement Manuel

Si le téléchargement automatique ne fonctionne pas:

```bash
# Voir les instructions manuelles
python download.py manual
```

**Pour LiDAR:**
1. Visitez https://geoservices.ign.fr/lidarhd
2. Cherchez votre ville
3. Téléchargez les fichiers .copc.laz
4. Placez-les dans `data/lidar/`

**Pour Images:**
1. Obtenez un token: https://www.mapillary.com/developer
2. Exécutez: `python download.py setup-mapillary`
3. Exécutez: `python download.py now`

## Étape 4: Lancer la Reconstruction

### Utilisation Basique

```bash
# Reconstruction complète avec téléchargement automatique
python main.py --city "Rambouillet" --radius 10
```

### Options Avancées

```bash
# Utiliser un fichier de configuration personnalisé
python main.py --config ma_config.yaml

# Désactiver le téléchargement automatique
python main.py --city "Paris" --radius 5  # avec données existantes

# Différentes villes et rayons
python main.py --city "Lyon" --radius 15
python main.py --city "Marseille" --radius 8
```

## Étape 5: Résultats

Le programme génère plusieurs fichiers dans `output/`:

- `rambouillet_3d_model.obj` - Format principal (OBJ)
- `rambouillet_3d_model.ply` - Avec couleurs
- `rambouillet_3d_model.stl` - Pour impression 3D

Ces fichiers peuvent être ouverts dans:
- **Blender** (gratuit) - https://www.blender.org/
- **3ds Max**
- **MeshLab** (gratuit)
- **CloudCompare** (gratuit)

## Test avec Données de Démo

Si vous voulez tester sans télécharger de vraies données:

```bash
# Créer des données synthétiques
python demo.py create

# Lancer avec les données de démo
python demo.py run
```

## Dépannage

### "No LiDAR files found"

**Cause**: Pas de données LiDAR téléchargées

**Solution**:
```bash
# Télécharger automatiquement
python download.py now

# Ou télécharger manuellement
python download.py manual
```

### "No Mapillary images found"

**Cause**: Token Mapillary non configuré ou zone sans images

**Solutions**:
```bash
# Configurer le token
python download.py setup-mapillary

# Ou utiliser des images locales
# Placez vos images JPG dans data/streetview/
```

### "Download failed"

**Causes possibles**:
- Pas de connexion internet
- Zone hors couverture
- Token invalide

**Solutions**:
```bash
# Vérifier la configuration
python download.py test

# Téléchargement manuel
python download.py manual
```

### Le fichier de sortie est petit ou vide

**Cause**: Pas assez de données d'entrée

**Solution**:
- Vérifiez que les données LiDAR sont présentes
- Augmentez le rayon de recherche
- Téléchargez plus d'images

## Exemples Complets

### Exemple 1: Première Utilisation

```bash
# Installation
git clone https://github.com/hleong75/Reconstitution.git
cd Reconstitution
pip install -r requirements.txt

# Configuration
python download.py setup-mapillary
# Entrez votre token quand demandé

# Téléchargement
python download.py now

# Reconstruction
python main.py --city "Rambouillet" --radius 10

# Le résultat est dans output/rambouillet_3d_model.obj
```

### Exemple 2: Plusieurs Villes

```bash
# Paris
python main.py --city "Paris" --radius 5

# Lyon  
python main.py --city "Lyon" --radius 10

# Marseille
python main.py --city "Marseille" --radius 8
```

### Exemple 3: Configuration Personnalisée

```bash
# Créer une config personnalisée
cp config.yaml ma_ville.yaml

# Éditer ma_ville.yaml avec vos paramètres

# Utiliser
python main.py --config ma_ville.yaml
```

## Performance

### Tailles Typiques

- **Rayon 5 km**: ~2-5 GB de données, 10-30 minutes
- **Rayon 10 km**: ~5-15 GB de données, 30-90 minutes
- **Rayon 20 km**: ~15-50 GB de données, 1-3 heures

### Optimisation

Pour de grandes zones, dans `config.yaml`:

```yaml
input:
  lidar:
    voxel_size: 0.1  # Plus grand = plus rapide (défaut: 0.05)

download:
  max_images: 30  # Moins d'images = plus rapide (défaut: 50)
```

## Questions Fréquentes

**Q: C'est vraiment gratuit?**
R: Oui! Aucune API payante n'est utilisée. Les données IGN sont publiques et Mapillary est gratuit.

**Q: Ça marche hors de France?**
R: Le LiDAR IGN ne couvre que la France. Pour d'autres pays, utilisez des données LiDAR locales.

**Q: Quelle est la qualité des résultats?**
R: Très bonne pour les zones avec couverture LiDAR HD. La qualité dépend de la densité du LiDAR et du nombre d'images.

**Q: Puis-je utiliser mes propres images?**
R: Oui! Placez vos images JPG dans `data/streetview/`.

**Q: Combien de temps ça prend?**
R: 10-90 minutes selon la taille de la zone et votre connexion internet.

**Q: Quel format de sortie?**
R: OBJ (principal), PLY, STL. Compatible Blender, 3ds Max, etc.

## Support

Pour des problèmes:
1. Vérifiez la configuration: `python download.py test`
2. Consultez les logs: `reconstruction.log`
3. Ouvrez une issue sur GitHub

## Licence

MIT License - Utilisation libre

## Auteur

hleong75

---

**Note Importante**: Ce programme n'utilise AUCUNE API Google payante. Toutes les données proviennent de sources publiques gratuites!
