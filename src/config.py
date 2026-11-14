"""Global configuration and industrial taxonomy for Waste Classification System."""
from __future__ import annotations

from pathlib import Path
from typing import Any

# Directory paths
SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent
WEIGHTS_PATH = ROOT_DIR / "weights" / "waste_material_detector_best.pt"
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "waste_data.db"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"

# Ensure data directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Default detection thresholds
DEFAULT_CONF_THRESHOLD = 0.35
DEFAULT_IOU_THRESHOLD = 0.45

# Primary active production model
AVAILABLE_MODELS: dict[str, dict[str, Any]] = {
    "waste_material_detector_best.pt": {
        "name": "Detecteur d'Objets & Emballages (YOLO Localisation)",
        "description": "Boites de detection : Carton, Plastique, Metal, Verre, Papier, Biodegradable",
        "filename": "waste_material_detector_best.pt",
        "type": "detection",
    },
}

# Specific minimum thresholds per class to prevent false positives
CLASS_MIN_CONF_THRESHOLDS: dict[str, float] = {
    "medical_waste": 0.65,
    "e_waste": 0.60,
    "biodegradable": 0.68,  # Suppresses false alarms from human skin/faces in background
}

# Supported class codes
CLASS_NAMES_RAW = [
    "cardboard",
    "plastic",
    "metal",
    "paper",
    "glass",
    "biodegradable",
    "organic_waste",
    "trash",
]

# Primary active production classes detected by the optimal packaging model
ACTIVE_CLASSES = [
    "cardboard",
    "plastic",
    "metal",
    "paper",
    "glass",
    "biodegradable",
]


# Industrial Taxonomy & Metadata (Strictly Professional, No Emojis)
CLASS_METADATA: dict[str, dict[str, Any]] = {
    "cardboard": {
        "code": "CARD",
        "display_name": "Carton",
        "bin_label": "Bac Jaune (Recyclable)",
        "bin_color": "#D29922",       # Industrial amber/yellow
        "waste_nature": "Biodegradable / Recyclable",
        "icon": "",
        "description": "Emballages cartons, briques alimentaires, carton ondulé",
    },
    "plastic": {
        "code": "PLAS",
        "display_name": "Plastique",
        "bin_label": "Bac Jaune (Recyclable)",
        "bin_color": "#388BFD",       # Technical blue
        "waste_nature": "Recyclable",
        "icon": "",
        "description": "Flacons, bouteilles PET/PEHD, films et emballages propres",
    },
    "metal": {
        "code": "METL",
        "display_name": "Metal / Aluminium",
        "bin_label": "Bac Jaune (Recyclable)",
        "bin_color": "#79C0FF",       # Metallic light blue
        "waste_nature": "Recyclable",
        "icon": "",
        "description": "Canettes boissons, boites de conserve, opercules aluminium",
    },
    "paper": {
        "code": "PAPR",
        "display_name": "Papier",
        "bin_label": "Bac Jaune (Recyclable)",
        "bin_color": "#A371F7",       # Purple accent
        "waste_nature": "Biodegradable / Recyclable",
        "icon": "",
        "description": "Imprimes, magazines, enveloppes, feuilles de bureau",
    },
    "glass": {
        "code": "GLAS",
        "display_name": "Verre",
        "bin_label": "Bac Vert (Verre)",
        "bin_color": "#2EA043",       # Emerald green
        "waste_nature": "Recyclable",
        "icon": "",
        "description": "Bouteilles, flacons et bocaux en verre sans bouchon",
    },
    "biodegradable": {
        "code": "ORGA",
        "display_name": "Organique / Biodegradable",
        "bin_label": "Bac Marron (Compost)",
        "bin_color": "#8B949E",       # Organic stone
        "waste_nature": "Biodegradable",
        "icon": "",
        "description": "Dechets de cuisine, marc de cafe, epluchures et restes",
    },
    "organic_waste": {
        "code": "ORGA",
        "display_name": "Organique / Biodegradable",
        "bin_label": "Bac Marron (Compost)",
        "bin_color": "#8B949E",
        "waste_nature": "Biodegradable",
        "icon": "",
        "description": "Dechets organiques fermentescibles",
    },
    "trash": {
        "code": "RESID",
        "display_name": "Dechet Residuel / DIB",
        "bin_label": "Bac Gris (Tout-Venant)",
        "bin_color": "#484F58",       # Dark slate
        "waste_nature": "Residuel",
        "icon": "",
        "description": "Dechets non recyclables, materiaux souilles",
    },
    "e_waste": {
        "code": "DEEE",
        "display_name": "Dechet Electronique (DEEE)",
        "bin_label": "Filiere Specifique DEEE",
        "bin_color": "#58A6FF",
        "waste_nature": "Specifique",
        "icon": "",
        "description": "Composants electroniques, cables, circuits, batteries",
    },
    "medical_waste": {
        "code": "DASRI",
        "display_name": "Dechet Medical (DASRI)",
        "bin_label": "Filiere Securisee DASRI",
        "bin_color": "#F85149",       # Alert red
        "waste_nature": "Dangereux",
        "icon": "",
        "description": "Dechets de soins a risques infectieux",
    },
}

# Corporate Analytics Palette for Plotly Charts
NATURE_COLORS: dict[str, str] = {
    "Recyclable": "#388BFD",
    "Biodegradable": "#2EA043",
    "Biodegradable / Recyclable": "#238636",
    "Specifique": "#58A6FF",
    "Dangereux": "#F85149",
    "Residuel": "#6E7681",
    "Autre": "#484F58",
}


def get_class_info(class_key: str) -> dict[str, Any]:
    """Retrieve metadata dict for a given raw class name."""
    norm_key = str(class_key).strip().lower().replace("-", "_").replace(" ", "_")
    return CLASS_METADATA.get(
        norm_key,
        {
            "code": "UNKN",
            "display_name": norm_key.title(),
            "bin_label": "Bac Tout-Venant (Gris)",
            "bin_color": "#6E7681",
            "waste_nature": "Autre",
            "icon": "",
            "description": "Dechet non repertorie",
        },
    )
