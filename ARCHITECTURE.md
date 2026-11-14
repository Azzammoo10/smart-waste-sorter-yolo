# Documentation d'Architecture — Système Intelligent de Gestion et Tri des Déchets (SWMS)

Ce document présente l'architecture logicielle, les spécifications techniques et le guide de maintenance du système.

---

## 1. Vue d'Ensemble du Système

Le système est conçu selon une architecture modulaire et découplée (Clean Architecture), séparant le traitement de vision par ordinateur, la logique métier de tri, la persistance locale et l'interface utilisateur.

```
                              ┌───────────────────────────────────┐
                              │     Webcam USB / Caméra PC        │
                              └─────────────────┬─────────────────┘
                                                │ Frame BGR (640x480)
                                                ▼
                              ┌───────────────────────────────────┐
                              │          src/camera.py            │
                              │ (Capture OpenCV DirectShow Win32) │
                              └─────────────────┬─────────────────┘
                                                │
                                                ▼
                              ┌───────────────────────────────────┐
                              │         src/detector.py           │
                              │    (YOLOv8m 8-classes Waste)      │
                              └─────────────────┬─────────────────┘
                                                │ Detections brutes
                                                ▼
                              ┌───────────────────────────────────┐
                              │          src/tracker.py           │
                              │  (Anti-spam, Vote temporel &      │
                              │    Stabilisation hystérésis)      │
                              └─────────┬───────────────────┬─────┘
                                        │                   │
         Événements confirmés (Novel)   │                   │ Detections temps réel
                                        ▼                   ▼
                     ┌──────────────────────┐    ┌──────────────────────┐
                     │   src/database.py    │    │        app.py        │
                     │  (Persistance SQLite)│    │(Interface Streamlit) │
                     └──────────┬───────────┘    └──────────┬───────────┘
                                │                           │
                                ▼                           ▼
                     ┌──────────────────────┐    ┌──────────────────────┐
                     │  data/waste_data.db  │    │pages/1_Statistiques  │
                     │ (Tables & Index SQL) │    │  (Tableaux Plotly)   │
                     └──────────────────────┘    └──────────────────────┘
```

---

## 2. Découpage des Modules (`src/`)

### 1. Configuration & Métadonnées (`src/config.py`)
Centralise les constantes du projet, chemins d'accès et la taxonomie des 8 classes :
* **Correspondance des bacs** : Bac Jaune (Recyclable), Bac Vert (Verre), Bac Marron (Organique), Point de Collecte DEEE (Électronique), Filière DASRI (Médical / Dangereux).
* **Nature du déchet** : *Recyclable*, *Biodégradable*, *Électronique / Spécifique*, *Dangereux*.
* **Code couleur HEX** et icônes pour le retour visuel immédiat.

### 2. Moteur de Détection IA (`src/detector.py`)
* Charge le modèle YOLOv8 (`weights/yolov8m_8classes_waste.pt`).
* Encapsulé dans un Singleton pour éviter de recharger les 52 Mo de poids à chaque image.
* Effectue l'inférence optimisée sur CPU (`device="cpu"`, format standardisé `imgsz=640`).
* Génère des boîtes englobantes avec étiquettes contrastées et recommandations de bac.

### 3. Module Caméra Vidéo (`src/camera.py`)
* Gère l'accès OpenCV avec le backend `cv2.CAP_DSHOW` (DirectShow) sous Windows, éliminant les lenteurs d'initialisation de DirectMedia.
* Résolution calibrée en 640x480 à 30 FPS pour une latence minimale sur processeur.
* Implémente le protocole de gestion de contexte (`with CameraManager(...) as cam:`) pour garantir la libération systématique de la caméra.

### 4. Suivi et Stabilisation (`src/tracker.py`)
* Résout le problème critique de la vidéo temps réel : éviter d'écrire des dizaines de lignes identiques en base de données par seconde lorsqu'un objet reste devant la caméra.
* Nécessite un vote d'au moins **3 frames consécutives** au-dessus du seuil de confiance.
* Applique un temps de refroidissement (*cooldown*) de **2,5 secondes** par classe avant de réautoriser un nouvel enregistrement du même type.

### 5. Persistance Relationnelle (`src/database.py`)
* Base de données relationnelle SQLite (`data/waste_data.db`).
* Schéma de la table `detections` :
  * `id` : Clé primaire auto-incrémentée.
  * `timestamp` : Date et heure ISO-8601 (`YYYY-MM-DD HH:MM:SS`).
  * `source` : Provenance (`webcam` ou `upload`).
  * `class_name` : Identifiant technique (`plastic`, `e_waste`, etc.).
  * `display_name` : Nom français convivial (`Plastique`, `Déchet Électronique`, etc.).
  * `confidence` : Score de certitude (entre 0.0 et 1.0).
  * `bin_label` : Consigne de bac recommandée.
  * `waste_nature` : Type de valorisation environnementale.
  * `snapshot_path` : Chemin vers la capture d'image (optionnel).
* Fonctions d'agrégation prêtes pour Pandas et Plotly.

---

## 3. Guide d'Exécution

### Lancement Rapide (Windows)
Double-cliquez simplement sur **`RUN_APP_WINDOWS.bat`**.  
L'application démarre et ouvre automatiquement votre navigateur sur `http://localhost:8501`.

### Lancement en Ligne de Commande (PowerShell)
```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

### Exécution des Tests Automatisés
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

---

## 4. Les 8 Classes de Déchets

| Classe Technique | Nom Français | Bac de Tri | Couleur | Nature |
| :--- | :--- | :--- | :--- | :--- |
| `plastic` | Plastique | Bac Jaune (Recyclable) | `#F1C40F` (Jaune) | Recyclable |
| `metal` | Métal & Canette | Bac Jaune (Recyclable) | `#F1C40F` (Jaune) | Recyclable |
| `cardboard` | Carton | Bac Jaune (Recyclable) | `#F1C40F` (Jaune) | Biodégradable / Recyclable |
| `paper` | Papier | Bac Jaune (Recyclable) | `#F1C40F` (Jaune) | Biodégradable / Recyclable |
| `glass` | Verre | Bac Vert (Verre) | `#2ECC71` (Vert) | Recyclable |
| `organic_waste` | Déchet Organique | Bac Marron (Compost) | `#A0522D` (Marron) | Biodégradable |
| `e_waste` | Déchet Électronique | Point Collecte DEEE / Déchèterie | `#3498DB` (Bleu) | Électronique / Spécifique |
| `medical_waste` | Déchet Médical | Filière DASRI Sécurisée | `#E74C3C` (Rouge) | Dangereux |

