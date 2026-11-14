"""EcoVision - Système Industriel de Contrôle Optique et Tri des Déchets.

Mode Temps Réel Haute Cadence (En Direct Amélioré) :
- Flux vidéo direct avec stabilisation temporelle anti-saccades (EMA).
- Réactivité instantanée sans aucun blocage lors des changements d'objets (papier -> carton).
- Détection basée sur le modèle optimal unique (waste_material_detector_best.pt).
- Design épuré, haute lisibilité industrielle, strictement sans emoji.
"""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from PIL import Image
import plotly.express as px
import streamlit as st

from src.camera import CameraManager
from src.config import (
    ACTIVE_CLASSES,
    CLASS_METADATA,
    DEFAULT_CONF_THRESHOLD,
    NATURE_COLORS,
    ROOT_DIR,
    SNAPSHOTS_DIR,
    WEIGHTS_PATH,
)
from src.database import (
    clear_database,
    get_detections_dataframe,
    get_recent_detections,
    get_statistics_summary,
    init_db,
    log_detection,
)
from src.detector import WasteDetector
from src.tracker import WasteTracker

# ─────────────────────────────────────────────────────────────────────────────
# Initialisation Système & Configuration de Page
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EcoVision - Contrôle Optique & Tri des Déchets",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ─────────────────────────────────────────────────────────────────────────────
# Design System CSS (Garantie Pleine Cohérence Clair/Sombre, Zéro Conflit)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    :root {
        --bg-main: #F8FAFC;
        --surface-card: #FFFFFF;
        --border-subtle: #E2E8F0;
        --border-strong: #CBD5E1;
        --text-primary: #0F172A;
        --text-secondary: #475569;
        --text-muted: #94A3B8;
        --accent-blue: #2563EB;
        --accent-emerald: #059669;
        --accent-amber: #D97706;
    }

    /* Base Canvas */
    .stApp {
        background-color: var(--bg-main);
        color: var(--text-primary);
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Force Light & High-Contrast Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #0F172A !important;
    }

    /* Top Brand Navigation Header */
    .brand-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 24px;
        background: #FFFFFF;
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 4px 12px -2px rgba(0, 0, 0, 0.02);
        margin-bottom: 20px;
    }
    .brand-logo-group {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .brand-badge {
        background: #0F172A;
        color: #FFFFFF;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 700;
        padding: 6px 12px;
        border-radius: 6px;
        letter-spacing: 1.5px;
    }
    .brand-title-wrap h1 {
        font-size: 19px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.4px;
        margin: 0;
        line-height: 1.2;
    }
    .brand-title-wrap p {
        font-size: 12px;
        color: #64748B;
        margin: 2px 0 0 0;
        font-weight: 500;
    }
    .system-status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        padding: 6px 14px;
        background: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        border-radius: 20px;
        letter-spacing: 0.5px;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10B981;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.25);
    }

    /* Tabs Bar Restyling (Eliminates Default Red Line) */
    div[data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #EEF2F6;
        padding: 6px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid var(--border-subtle);
    }
    button[data-baseweb="tab"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 12.5px !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        color: #64748B !important;
        background-color: transparent !important;
        border: none !important;
        letter-spacing: 0.3px;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #2563EB !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08) !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #2563EB !important;
    }

    /* Decision Banner Card */
    .decision-banner {
        border-radius: 14px;
        padding: 22px;
        border-left: 8px solid #94A3B8;
        background: #FFFFFF;
        border-top: 1px solid var(--border-subtle);
        border-right: 1px solid var(--border-subtle);
        border-bottom: 1px solid var(--border-subtle);
        box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.04);
        margin-bottom: 16px;
        transition: all 0.2s ease-in-out;
    }
    .decision-state-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #64748B;
        margin-bottom: 6px;
    }
    .decision-title {
        font-size: 26px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.4px;
        margin: 0 0 10px 0;
    }
    .decision-bin-pill {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12.5px;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 6px;
        color: #FFFFFF;
        background: #64748B;
        margin-bottom: 12px;
        letter-spacing: 0.5px;
    }
    .decision-instruction-box {
        background: #F8FAFC;
        border-left: 3px solid #CBD5E1;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        font-size: 13px;
        color: #334155;
        font-weight: 500;
        margin-top: 10px;
    }

    /* KPI Mini Cards */
    .kpi-metric-box {
        background: #FFFFFF;
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .kpi-metric-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .kpi-metric-value {
        font-size: 24px;
        font-weight: 800;
        color: #0F172A;
        font-family: 'Plus Jakarta Sans', sans-serif;
        line-height: 1.1;
    }

    /* Table HTML styling */
    .clean-data-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        text-align: left;
    }
    .clean-data-table th {
        background-color: #F8FAFC;
        color: #475569;
        padding: 10px 14px;
        font-weight: 700;
        border-bottom: 2px solid #E2E8F0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .clean-data-table td {
        padding: 10px 14px;
        border-bottom: 1px solid #F1F5F9;
        color: #1E293B;
    }
    .clean-data-table tr:hover {
        background-color: #F8FAFC;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Initialisation du Tracker Réactif Temps Réel (Zéro Freeze)
# ─────────────────────────────────────────────────────────────────────────────
if "tracker" not in st.session_state:
    st.session_state.tracker = WasteTracker(window_size=5, min_stable_seconds=0.8, cooldown_seconds=2.5)

# ─────────────────────────────────────────────────────────────────────────────
# En-tête Principal de Marque
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="brand-navbar">
        <div class="brand-logo-group">
            <span class="brand-badge">ECOVISION ST-04</span>
            <div class="brand-title-wrap">
                <h1>Système Industriel de Tri & Contrôle Optique</h1>
                <p>Acquisition vidéo directe, lissage dynamique anti-saccades et enregistrement SQL</p>
            </div>
        </div>
        <div class="system-status-indicator">
            <span class="pulse-dot"></span>
            POSTE FLUIDE DIRECT // ULTRA HAUTE REACTIVITE
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Volet Latéral de Contrôle (Thème Blanc Net, Lisibilité Totale)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("#### MOTEUR D'INSPECTION IA")
    st.markdown(
        """
        <div style="background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 8px; padding: 10px 12px; margin-bottom: 14px;">
            <div style="font-family: monospace; font-size: 11px; font-weight: 700; color: #2563EB;">MODELE OPTIMAL CHARGE</div>
            <div style="font-size: 12.5px; font-weight: 700; color: #0F172A; margin-top: 2px;">Détecteur Packaging 6 Classes</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 2px;">YOLO Localisation & Tri Matériau</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### REGLAGES CAPTEUR")

    camera_idx = st.selectbox("Index Caméra", options=[0, 1, 2], index=0)

    conf_threshold = st.slider(
        "Seuil de Sensibilité Détection",
        min_value=0.20,
        max_value=0.85,
        value=float(DEFAULT_CONF_THRESHOLD),
        step=0.05,
        help="Ajuste la tolérance de reconnaissance des matières.",
    )

    st.markdown("---")
    st.markdown("#### JOURNALISATION SQL")
    auto_log = st.checkbox("Enregistrer automatiquement sur stabilisation", value=True)
    save_snapshots = st.checkbox("Archiver les captures optiques (.jpg)", value=False)

    st.markdown("---")
    st.markdown("#### NOMENCLATURE DES BACS")
    for key in ACTIVE_CLASSES:
        meta = CLASS_METADATA.get(key)
        if not meta:
            continue
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #F1F5F9;">
                <span style="font-family: monospace; font-size: 11.5px; font-weight: 700; color: #0F172A;">
                    [{meta['code']}] {meta['display_name']}
                </span>
                <span style="font-family: monospace; font-size: 10.5px; font-weight: 700; color: #FFFFFF; background: {meta['bin_color']}; padding: 3px 8px; border-radius: 4px;">
                    {meta['bin_label'].replace(' (Recyclable)', '').replace(' (Verre)', '').replace(' (Compost)', '').upper()}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Chargement du modèle unique optimal
detector = WasteDetector.get_instance(WEIGHTS_PATH)

# Consignes pratiques de tri
INSPECTION_DIRECTIVES: dict[str, str] = {
    "cardboard": "Aplatir la boîte ou brique d'emballage. Déposer dans le Bac Jaune (Recyclable Sec).",
    "plastic": "Vider le liquide. Maintenir le bouchon vissé. Déposer dans le Bac Jaune (Recyclable Sec).",
    "metal": "Vider la canette ou conserve métallique. Déposer directement dans le Bac Jaune.",
    "glass": "Déposer dans le Bac Vert. Retirer les couvercles métalliques (à placer dans le bac jaune).",
    "paper": "Déposer propre et sec sans film plastique dans le Bac Jaune / Bleu.",
    "biodegradable": "Déposer dans le Bac Marron / Composteur organique.",
}

# ─────────────────────────────────────────────────────────────────────────────
# Navigation Supérieure par Onglets
# ─────────────────────────────────────────────────────────────────────────────
tab_live, tab_upload, tab_analytics = st.tabs(
    ["POSTE D'INSPECTION DIRECT", "ANALYSE D'IMAGE FIXE", "TABLEAU DE BORD & ANALYTIQUE"]
)

# ═════════════════════════════════════════════════════════════════════════════
# Onglet 1 : Poste d'Inspection Vidéo Direct (Mode Réactif Temps Réel)
# ═════════════════════════════════════════════════════════════════════════════
with tab_live:
    col_view, col_diag = st.columns([13, 9], gap="large")

    with col_view:
        ctrl_c1, ctrl_c2 = st.columns([3, 1])
        with ctrl_c1:
            run_cam = st.toggle("Activer l'acquisition vidéo en direct", value=False)
        with ctrl_c2:
            fps_badge = st.empty()

        video_frame_placeholder = st.empty()

    with col_diag:
        decision_container = st.empty()
        decision_container.markdown(
            """
            <div class="decision-banner" style="border-left-color: #94A3B8;">
                <div class="decision-state-tag">STATUT : CAPTEUR EN ATTENTE</div>
                <h2 class="decision-title" style="color: #64748B;">POSTE DE TRI OPERATIONNEL</h2>
                <div class="decision-bin-pill" style="background: #64748B;">ZONE LIBRE</div>
                <div class="decision-instruction-box">
                    Présentez un emballage devant l'objectif pour une reconnaissance immédiate et fluide.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            metric_target = st.empty()
            metric_target.markdown(
                """
                <div class="kpi-metric-box">
                    <div class="kpi-metric-label">Matière Active</div>
                    <div class="kpi-metric-value" style="font-size: 20px;">--</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_m2:
            metric_confidence = st.empty()
            metric_confidence.markdown(
                """
                <div class="kpi-metric-box">
                    <div class="kpi-metric-label">Certitude & Stabilité</div>
                    <div class="kpi-metric-value" style="font-size: 20px;">-- %</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<p style='font-family: monospace; font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase;'>Journal des Dépôts Validés</p>", unsafe_allow_html=True)
        recent_log_placeholder = st.empty()

    if run_cam:
        cam = CameraManager(camera_index=camera_idx, width=640, height=480)
        if not cam.start():
            st.error(f"Périphérique caméra introuvable à l'index {camera_idx}. Vérifiez le branchement.")
        else:
            prev_t = time.time()
            f_count = 0
            try:
                while run_cam:
                    ok, frame = cam.read_frame()
                    if not ok or frame is None:
                        st.warning("Signal vidéo momentanément indisponible.")
                        break

                    f_count += 1
                    now_t = time.time()
                    dt = now_t - prev_t
                    if dt >= 1.0:
                        fps = f_count / dt
                        fps_badge.markdown(
                            f"<div style='text-align: right; font-family: monospace; font-size: 12px; font-weight: 700; color: #059669; padding-top: 8px;'>{fps:.1f} FPS</div>",
                            unsafe_allow_html=True,
                        )
                        f_count = 0
                        prev_t = now_t

                    # Inférence IA directe
                    detections = detector.predict(frame, conf_threshold=conf_threshold)

                    # Mise à jour réactive du tracker
                    state, stability, active_object, events_to_log = st.session_state.tracker.update(detections)

                    # Journalisation unique SQLite lors d'une détection stabilisée
                    if auto_log and events_to_log:
                        for evt in events_to_log:
                            s_path = None
                            if save_snapshots:
                                s_name = f"snap_{int(time.time())}_{evt['class_name']}.jpg"
                                full_s = SNAPSHOTS_DIR / s_name
                                cv2.imwrite(str(full_s), frame)
                                s_path = str(full_s)
                            log_detection(
                                class_name=evt["class_name"],
                                confidence=evt["confidence"],
                                source="webcam",
                                snapshot_path=s_path,
                            )

                    # ── Affichage Télémesure Instantané et Réactif ───────────
                    if state == "TRACKING" and active_object:
                        bin_col = active_object.get("bin_color", "#2563EB")
                        disp_name = active_object.get("display_name", "DECHET").upper()
                        bin_lbl = active_object.get("bin_label", "BAC DE TRI").upper()
                        conf_val = active_object.get("confidence", 0.0)
                        stab_pct = int(stability * 100)
                        instr = INSPECTION_DIRECTIVES.get(
                            active_object.get("class_name", ""),
                            "Déposer dans le bac de tri prescrit."
                        )

                        decision_container.markdown(
                            f"""
                            <div class="decision-banner" style="border-left-color: {bin_col}; box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.08);">
                                <div class="decision-state-tag" style="color: {bin_col};">DETECTION IMMEDIATE // STABILITE {stab_pct}%</div>
                                <h2 class="decision-title" style="color: #0F172A;">{disp_name}</h2>
                                <div class="decision-bin-pill" style="background: {bin_col};">DESTINATION : {bin_lbl}</div>
                                <div class="decision-instruction-box" style="border-left-color: {bin_col};">
                                    <b>Consigne :</b> {instr}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        metric_target.markdown(
                            f"""
                            <div class="kpi-metric-box" style="border-color: {bin_col};">
                                <div class="kpi-metric-label">Matière Détectée</div>
                                <div class="kpi-metric-value" style="font-size: 20px; color: {bin_col};">{disp_name}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        metric_confidence.markdown(
                            f"""
                            <div class="kpi-metric-box" style="border-color: {bin_col};">
                                <div class="kpi-metric-label">Certitude IA</div>
                                <div class="kpi-metric-value" style="font-size: 20px; color: {bin_col};">{conf_val:.1%}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    else:
                        decision_container.markdown(
                            """
                            <div class="decision-banner" style="border-left-color: #94A3B8;">
                                <div class="decision-state-tag">STATUT : CAPTEUR EN ATTENTE</div>
                                <h2 class="decision-title" style="color: #64748B;">POSTE DE TRI OPERATIONNEL</h2>
                                <div class="decision-bin-pill" style="background: #64748B;">ZONE LIBRE</div>
                                <div class="decision-instruction-box">
                                    Présentez un emballage devant l'objectif pour une reconnaissance immédiate et fluide.
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        metric_target.markdown(
                            """
                            <div class="kpi-metric-box">
                                <div class="kpi-metric-label">Matière Active</div>
                                <div class="kpi-metric-value" style="font-size: 20px;">--</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        metric_confidence.markdown(
                            """
                            <div class="kpi-metric-box">
                                <div class="kpi-metric-label">Certitude & Stabilité</div>
                                <div class="kpi-metric-value" style="font-size: 20px;">-- %</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # Rendu du HUD optique dynamique sur le flux vidéo
                    annotated = detector.draw_live_hud(frame, state, stability, active_object, detections)
                    frame_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                    video_frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

                    # Journal récent
                    recents = get_recent_detections(limit=5)
                    if recents:
                        html_log = "<div style='background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden;'>"
                        for r in recents:
                            html_log += (
                                f"<div style='display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-bottom: 1px solid #F1F5F9; font-family: monospace; font-size: 12px;'>"
                                f"<span><b style='color: #0F172A;'>{r['display_name']}</b> <span style='color: #2563EB;'>[{r['confidence']:.0%}]</span></span>"
                                f"<span style='color: #64748B; font-weight: 600;'>{r['bin_label'].replace(' (Recyclable)', '').replace(' (Verre)', '').replace(' (Compost)', '')}</span>"
                                f"<span style='color: #94A3B8;'>{r['timestamp'][-8:]}</span>"
                                f"</div>"
                            )
                        html_log += "</div>"
                        recent_log_placeholder.markdown(html_log, unsafe_allow_html=True)
                    else:
                        recent_log_placeholder.caption("Aucune entrée enregistrée pour le moment.")

                    time.sleep(0.01)
            finally:
                cam.release()
                st.session_state.tracker.reset()

# ═════════════════════════════════════════════════════════════════════════════
# Onglet 2 : Analyse d'Image Fixe
# ═════════════════════════════════════════════════════════════════════════════
with tab_upload:
    st.markdown("#### ANALYSE OPTIQUE D'UN CLICHE FIXE")
    uploaded = st.file_uploader("Importer une photo d'emballage", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    if uploaded is not None:
        pil_img = Image.open(uploaded).convert("RGB")
        img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        up_dets = detector.predict(img_bgr, conf_threshold=conf_threshold)
        up_annotated = detector.draw_detections(img_bgr, up_dets)
        up_rgb = cv2.cvtColor(up_annotated, cv2.COLOR_BGR2RGB)

        col_u1, col_u2 = st.columns([13, 9], gap="large")
        with col_u1:
            st.image(up_rgb, use_container_width=True)
        with col_u2:
            st.markdown("#### RESULTAT DE L'INSPECTION")
            if not up_dets:
                st.warning("Aucune matière résolue au seuil actuel.")
            else:
                for d in up_dets:
                    bin_col = d.get("bin_color", "#2563EB")
                    disp_name = d.get("display_name", "").upper()
                    bin_lbl = d.get("bin_label", "").upper()
                    conf_val = d.get("confidence", 0.0)
                    nature = d.get("waste_nature", "")
                    instr = INSPECTION_DIRECTIVES.get(d.get("class_name", ""), "Déposer dans le bac de tri prescrit.")

                    st.markdown(
                        f"""
                        <div class="decision-banner" style="border-left-color: {bin_col};">
                            <div class="decision-state-tag" style="color: {bin_col}; font-weight: 700;">ANALYSE STATIC VALIDEE</div>
                            <h2 class="decision-title">{disp_name}</h2>
                            <div class="decision-bin-pill" style="background: {bin_col};">DESTINATION : {bin_lbl}</div>
                            <div class="decision-instruction-box" style="border-left-color: {bin_col};">
                                <b>Consigne :</b> {instr}<br/>
                                <span style="font-size: 11.5px; color: #64748B;">Certitude : {conf_val:.1%} | Filière : {nature}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                if st.button("Enregistrer cette inspection dans le registre SQL", type="primary"):
                    for d in up_dets:
                        log_detection(
                            class_name=d["class_name"],
                            confidence=d["confidence"],
                            source="upload",
                        )
                    st.success("Inspection enregistrée avec succès dans la base SQLite.")

# ═════════════════════════════════════════════════════════════════════════════
# Onglet 3 : Tableau de Bord & Analytique
# ═════════════════════════════════════════════════════════════════════════════
with tab_analytics:
    stats = get_statistics_summary()
    df = get_detections_dataframe()

    total_items = stats["total_detections"]
    most_common = stats["most_common_waste"]
    avg_conf = stats["avg_confidence"]

    recyclable_count = sum(
        count for nature, count in stats["by_nature"].items() if "Recyclable" in nature
    )
    rate_recyclable = (recyclable_count / total_items * 100) if total_items > 0 else 0.0

    # 4 KPI Cards Modernes
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"""
            <div class="kpi-metric-box">
                <div class="kpi-metric-label">Total Unités Traitées</div>
                <div class="kpi-metric-value">{total_items}</div>
                <div class="kpi-metric-sub" style="font-size: 11.5px; color: #059669; font-weight: 600; margin-top: 4px;">Registre d'inspection SQL</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="kpi-metric-box">
                <div class="kpi-metric-label">Matière Majoritaire</div>
                <div class="kpi-metric-value" style="font-size: 22px;">{most_common.upper()}</div>
                <div class="kpi-metric-sub" style="font-size: 11.5px; color: #059669; font-weight: 600; margin-top: 4px;">Fréquence la plus élevée</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="kpi-metric-box">
                <div class="kpi-metric-label">Score Moyen IA</div>
                <div class="kpi-metric-value">{avg_conf:.1%}</div>
                <div class="kpi-metric-sub" style="font-size: 11.5px; color: #059669; font-weight: 600; margin-top: 4px;">Certitude de classification</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"""
            <div class="kpi-metric-box">
                <div class="kpi-metric-label">Taux Recyclabilité</div>
                <div class="kpi-metric-value">{rate_recyclable:.1f}%</div>
                <div class="kpi-metric-sub" style="font-size: 11.5px; color: #059669; font-weight: 600; margin-top: 4px;">Filière valorisable</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    if df.empty:
        st.info("Le registre est actuellement vide. Lancez l'inspection vidéo pour alimenter les données analytiques.")
    else:
        chart_c1, chart_c2 = st.columns(2, gap="large")

        with chart_c1:
            st.markdown("<p style='font-family: monospace; font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase;'>Distribution par Type de Matière</p>", unsafe_allow_html=True)
            df_counts = df["display_name"].value_counts().reset_index()
            df_counts.columns = ["Matiere", "Unites"]

            fig_bar = px.bar(
                df_counts,
                x="Matiere",
                y="Unites",
                color="Matiere",
                text="Unites",
                color_discrete_sequence=["#2563EB", "#059669", "#D97706", "#7C3AED", "#0284C7"],
            )
            fig_bar.update_layout(
                showlegend=False,
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                margin={"l": 10, "r": 10, "t": 10, "b": 10},
                xaxis={"gridcolor": "#F1F5F9", "title": ""},
                yaxis={"gridcolor": "#F1F5F9", "title": "Quantite"},
                font={"family": "Plus Jakarta Sans", "size": 12, "color": "#475569"},
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with chart_c2:
            st.markdown("<p style='font-family: monospace; font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase;'>Proportion des Filières de Traitement</p>", unsafe_allow_html=True)
            df_nature = df["waste_nature"].value_counts().reset_index()
            df_nature.columns = ["Filiere", "Total"]

            fig_donut = px.pie(
                df_nature,
                values="Total",
                names="Filiere",
                hole=0.6,
                color="Filiere",
                color_discrete_map=NATURE_COLORS,
            )
            fig_donut.update_layout(
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                margin={"l": 10, "r": 10, "t": 10, "b": 10},
                font={"family": "Plus Jakarta Sans", "size": 12, "color": "#475569"},
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        # Tableau Détaillé du Registre
        st.markdown("---")
        st.markdown("#### REGISTRE DES EVENEMENTS D'INSPECTION")

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            filter_class = st.multiselect("Filtrer par matière", options=df["display_name"].unique(), default=[])
        with f_col2:
            filter_nature = st.multiselect("Filtrer par filière", options=df["waste_nature"].unique(), default=[])

        df_filtered = df.copy()
        if filter_class:
            df_filtered = df_filtered[df_filtered["display_name"].isin(filter_class)]
        if filter_nature:
            df_filtered = df_filtered[df_filtered["waste_nature"].isin(filter_nature)]

        table_view = df_filtered[
            ["id", "timestamp", "source", "display_name", "confidence", "bin_label", "waste_nature"]
        ].copy()
        table_view["confidence"] = table_view["confidence"].apply(lambda v: f"{v:.1%}")
        table_view = table_view.rename(
            columns={
                "id": "ID",
                "timestamp": "HORODATAGE",
                "source": "CANAL",
                "display_name": "MATIERE",
                "confidence": "CERTITUDE",
                "bin_label": "BAC DE DESTINATION",
                "waste_nature": "FILIERE",
            }
        )

        table_html = table_view.to_html(classes="clean-data-table", index=False, escape=False)
        st.markdown(
            f"""
            <div style="max-height: 400px; overflow-y: auto; border: 1px solid #E2E8F0; border-radius: 12px; background: #FFFFFF; margin-bottom: 16px;">
                {table_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

        dl_col, purge_col = st.columns([3, 1])
        with dl_col:
            csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Télécharger le registre au format CSV",
                data=csv_bytes,
                file_name="ecovision_registre_tri.csv",
                mime="text/csv",
            )
        with purge_col:
            if st.button("Purger le registre SQL", type="secondary"):
                clear_database()
                st.rerun()
