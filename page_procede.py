import pandas as pd
import streamlit as st
from collections import Counter
import matplotlib.pyplot as plt


def page_procede(df_meta, df_impacts, df_cat):

    # Sélection du procédé
    st.title("Dashboard Empreinte – Visualisation des impacts environnementaux")
    procedes_dict = {
        row["Nom du flux"]: row["UUID"]
        for _, row in df_meta.dropna(subset=["Nom du flux", "UUID"]).iterrows()
    }
    procede_options = df_meta["Nom du flux"].dropna().unique()
    selected_nom = st.selectbox("Choisir un procédé", list(procedes_dict.keys()))
    selected_uuid = procedes_dict[selected_nom]

    # Affichage des métadonnées
    meta_info = df_meta[df_meta["UUID"] == selected_uuid]
    st.subheader("Métadonnées")
    st.write(meta_info)

    # Visualisation des impacts
    st.subheader("Impacts environnementaux")
    print("meta -", df_meta["UUID"][297], "-")
    print("impacts -", df_impacts["UUID_procede"][297], "-")
    print("cat -", df_impacts["UUID_cat"][0], "-")
    impacts = df_impacts[df_impacts["UUID_procede"] == selected_uuid]
    if not impacts.empty:
        impacts_merged = impacts.merge(df_cat, on="UUID_cat", how="left")
        fig, ax = plt.subplots()
        ax.barh(impacts_merged["Nom français"], impacts_merged["valeur"])
        ax.set_xlabel("Impact")
        ax.set_title("Indicateurs environnementaux")
        st.pyplot(fig)
    else:
        st.info("Aucun impact trouvé pour ce procédé.")
