# Reconstitution 3D - NOUVELLE VERSION FONCTIONNELLE

## 🎉 Modifications Majeures

Cette version est **complètement fonctionnelle** et télécharge automatiquement les données **SANS utiliser d'API Google payantes!**

### ✅ Ce qui Fonctionne Maintenant

1. **Téléchargement Automatique LiDAR**
   - Source: IGN Géoportail (GRATUIT)
   - Données HD publiques
   - Aucun coût, aucune authentification

2. **Téléchargement Automatique Images**
   - Source: Mapillary (GRATUIT)
   - Alternative à Google Street View
   - Nécessite token gratuit

3. **Pipeline Complet**
   - ✅ Chargement multi-formats (LAZ, LAS, PLY, PCD)
   - ✅ Segmentation avec fallback intelligent
   - ✅ Génération de maillage 3D
   - ✅ Application de textures
   - ✅ Export multi-formats (OBJ, PLY, STL)

4. **Sortie Fonctionnelle**
   - Fichiers 3D complets
   - Compatible Blender, 3ds Max
   - Prêt à l'emploi

## 🚀 Démarrage Rapide

```bash
# 1. Installer
pip install -r requirements.txt

# 2. Configurer (optionnel, pour images Mapillary)
python download.py setup-mapillary

# 3. Télécharger et reconstruire
python main.py --city "Rambouillet" --radius 10
```

C'est tout! Le programme va:
- Télécharger les données LiDAR de l'IGN
- Télécharger les images Mapillary (si configuré)
- Créer un modèle 3D dans `output/`

## 📋 Guide Complet

Voir [GUIDE_COMPLET.md](GUIDE_COMPLET.md) pour:
- Instructions détaillées
- Configuration avancée
- Dépannage
- Exemples

## 🔧 Utilitaire de Téléchargement

```bash
python download.py info              # Informations sur les sources
python download.py setup-mapillary   # Configurer Mapillary
python download.py test              # Tester la configuration
python download.py now               # Télécharger maintenant
python download.py manual            # Instructions manuelles
```

## 📝 Changements Techniques

### Processeur LiDAR (`src/lidar_processor.py`)
- Support multi-formats: LAZ, LAS, PLY, PCD
- Gestion d'erreurs améliorée
- Fallback pour données manquantes

### Segmentation (`src/segmentation.py`)
- Fallback height-based intelligent
- Fonctionne sans modèle IA
- Résultats fiables

### Téléchargement (`src/auto_downloader.py`)
- IGN LiDAR HD automatique
- Mapillary pour images
- Aucune API payante

### Utilitaires
- `download.py` - Outil de téléchargement interactif
- Configuration simplifiée
- Messages d'aide clairs

## 🌟 Fonctionnalités

- ✅ **Aucune API payante** - Tout est gratuit
- ✅ **Téléchargement automatique** - Des données LiDAR et images
- ✅ **Multi-formats** - LAZ, PLY, PCD supportés
- ✅ **Robuste** - Fallbacks intelligents
- ✅ **Sortie fonctionnelle** - Fichiers 3D utilisables
- ✅ **Documentation complète** - En français et anglais

## 🎯 Sources de Données

### LiDAR HD IGN
- **Gratuit**: Données publiques
- **Couverture**: France entière
- **Qualité**: Haute densité
- **Téléchargement**: Automatique

### Mapillary
- **Gratuit**: Nécessite token gratuit
- **Couverture**: Mondiale
- **Qualité**: Images communautaires
- **Téléchargement**: Automatique

## 💻 Exemples

### Exemple Basique
```bash
python main.py --city "Rambouillet" --radius 10
```

### Avec Données de Démo
```bash
python demo.py create  # Créer données synthétiques
python demo.py run     # Tester le pipeline
```

### Téléchargement Manuel
```bash
python download.py manual  # Voir les instructions
```

## 📊 Résultats

Le programme génère:
- `output/nom_ville_3d_model.obj` - Format principal
- `output/nom_ville_3d_model.ply` - Avec couleurs
- `output/nom_ville_3d_model.stl` - Pour impression 3D

## ⚙️ Configuration

Tout est dans `config.yaml`:

```yaml
location:
  name: "Votre Ville"
  center_lat: 48.6439  # Latitude
  center_lon: 1.8294   # Longitude
  radius_km: 10        # Rayon

download:
  enable_lidar: true        # Télécharger LiDAR
  enable_streetview: true   # Télécharger images
  mapillary_token: ""       # Token gratuit
```

## 🐛 Dépannage

### Pas de données téléchargées
```bash
python download.py test  # Vérifier config
python download.py now   # Télécharger
```

### Erreur de téléchargement
```bash
python download.py manual  # Instructions manuelles
```

### Fichier de sortie vide
- Vérifiez que les données sont présentes dans `data/`
- Augmentez le rayon
- Consultez `reconstruction.log`

## 📚 Documentation

- [GUIDE_COMPLET.md](GUIDE_COMPLET.md) - Guide utilisateur complet
- [README.md](README.md) - Documentation générale
- [config.yaml](config.yaml) - Configuration avec commentaires

## 🎓 Support

- GitHub Issues: https://github.com/hleong75/Reconstitution/issues
- Logs: Voir `reconstruction.log`
- Configuration: `python download.py test`

## 📜 Licence

MIT License - Utilisation libre

---

## 🔥 IMPORTANT

**AUCUNE API GOOGLE N'EST UTILISÉE!**

Toutes les données proviennent de sources publiques gratuites:
- IGN Géoportail (France)
- Mapillary (Mondial)

Le programme est maintenant **complètement fonctionnel** et **gratuit**!

---

**Auteur**: hleong75  
**Version**: 2.0 - Fonctionnelle avec téléchargement automatique gratuit
