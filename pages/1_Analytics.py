"""Tableau de bord analytique et métriques de tri industriel - EcoVision."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import NATURE_COLORS
from src.database import clear_database, get_detections_dataframe, get_statistics_summary

st.set_page_config(
    page_title="EcoVision - Analytique Industrielle",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .kpi-metric-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 18px 20px;
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
        font-size: 28px;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
    }
    .kpi-metric-sub {
        font-size: 12px;
        color: #059669;
        font-weight: 600;
        margin-top: 4px;
    }
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
        padding: 12px 16px;
        font-weight: 700;
        border-bottom: 2px solid #E2E8F0;
        text-transform: uppercase;
    }
    .clean-data-table td {
        padding: 12px 16px;
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

st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; margin-bottom: 24px;">
        <div>
            <h2 style="margin: 0; font-size: 20px; font-weight: 800; color: #0F172A;">TABLEAU DE BORD // ANALYTIQUE DE VALORISATION</h2>
            <p style="margin: 0; font-size: 13px; color: #64748B;">Registre des flux, repartition par matiere et historique d'inspection</p>
        </div>
        <div style="font-family: monospace; font-size: 12px; font-weight: 600; color: #64748B;">
            SQLITE DATABASE // ACTIVE
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

stats = get_statistics_summary()
df = get_detections_dataframe()

total_items = stats["total_detections"]
most_common = stats["most_common_waste"]
avg_conf = stats["avg_confidence"]

recyclable_count = sum(
    count for nature, count in stats["by_nature"].items() if "Recyclable" in nature
)
rate_recyclable = (recyclable_count / total_items * 100) if total_items > 0 else 0.0

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(
        f"""
        <div class="kpi-metric-box">
            <div class="kpi-metric-label">Total Unites Traitees</div>
            <div class="kpi-metric-value">{total_items}</div>
            <div class="kpi-metric-sub">Registre d'inspection SQL</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f"""
        <div class="kpi-metric-box">
            <div class="kpi-metric-label">Matiere Majoritaire</div>
            <div class="kpi-metric-value" style="font-size: 22px;">{most_common.upper()}</div>
            <div class="kpi-metric-sub">Frequence la plus elevee</div>
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
            <div class="kpi-metric-sub">Certitude de classification</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        f"""
        <div class="kpi-metric-box">
            <div class="kpi-metric-label">Taux Recyclabilite</div>
            <div class="kpi-metric-value">{rate_recyclable:.1f}%</div>
            <div class="kpi-metric-sub">Filiere valorisable</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

if df.empty:
    st.info("Le registre est actuellement vide. Lancez l'inspection video pour alimenter les donnees analytiques.")
else:
    chart_c1, chart_c2 = st.columns(2, gap="large")

    with chart_c1:
        st.markdown("<p style='font-family: monospace; font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase;'>Distribution par Type de Matiere</p>", unsafe_allow_html=True)
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
        st.markdown("<p style='font-family: monospace; font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase;'>Proportion des Filieres de Traitement</p>", unsafe_allow_html=True)
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
        filter_class = st.multiselect("Filtrer par matiere", options=df["display_name"].unique(), default=[])
    with f_col2:
        filter_nature = st.multiselect("Filtrer par filiere", options=df["waste_nature"].unique(), default=[])

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
            label="Telecharger le registre au format CSV",
            data=csv_bytes,
            file_name="ecovision_registre_tri.csv",
            mime="text/csv",
        )
    with purge_col:
        if st.button("Purger le registre SQL", type="secondary"):
            clear_database()
            st.rerun()
