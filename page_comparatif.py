import pandas as pd
import streamlit as st
import json
from collections import Counter
import matplotlib.pyplot as plt


def build_category_tree(df):
    tree = {}
    for _, row in df.iterrows():
        levels = [
            row.get("Categorie_niv_1"),
            row.get("Categorie_niv_2"),
            row.get("Categorie_niv_3"),
            row.get("Categorie_niv_4"),
        ]
        current = tree
        for level in levels:
            if pd.isna(level):
                break
            current = current.setdefault(level, {})
        # Feuille = Nom du flux
        nom_flux = row.get("Nom du flux")
        if isinstance(nom_flux, str):
            current[nom_flux] = None
    return tree


def display_tree(tree, indent=0):
    for key, subtree in tree.items():
        st.markdown(" " * indent + f"- {key}")
        if isinstance(subtree, dict):
            display_tree(subtree, indent + 1)


def page_comparatif(df_meta, df_impacts, df_cat):

    st.write(df_meta)

    category_tree = build_category_tree(df_meta)

    # with open("arbre_categories.json", "w", encoding="utf-8") as f:
    #     json.dump(category_tree, f, ensure_ascii=False, indent=2)
    df_export = df_meta[
        [
            "Categorie_niv_1",
            "Categorie_niv_2",
            "Categorie_niv_3",
            "Categorie_niv_4",
            "Nom du flux",
            "UUID",
        ]
    ].dropna(subset=["Nom du flux"])

    df_export.to_json("hiérarchie_plate.json", orient="records", force_ascii=False)

    st.title("Hiérarchie des catégories de flux")
    tree = build_category_tree(df_meta)
    with st.expander("Afficher la hiérarchie des catégories"):
        display_tree(tree)
    col1, col2 = st.columns(2)

    # Sélection
    level1 = st.selectbox("Niveau 1", list(category_tree.keys()))
    level2 = st.selectbox(
        "Niveau 2",
        list(category_tree[level1].keys()) if level1 in category_tree else [],
    )
    level3 = st.selectbox(
        "Niveau 3",
        (
            list(category_tree[level1][level2].keys())
            if level2 and level2 in category_tree[level1]
            else []
        ),
    )
    level4 = st.selectbox(
        "Niveau 4",
        (
            list(category_tree[level1][level2][level3].keys())
            if level3 and level3 in category_tree[level1][level2]
            else []
        ),
    )

    # Selecteur de catégorie d'impact
    categories = df_cat["Nom français"].dropna().unique()
    selected_categories = st.multiselect(
        "Sélectionner les catégories d'impact",
        categories,
        default=categories[:3],  # Valeur par défaut : les 3 premières catégories
    )

    mask = (
        (df_meta["Categorie_niv_1"] == level1)
        & (df_meta["Categorie_niv_2"] == level2)
        & (df_meta["Categorie_niv_3"] == level3)
        & (df_meta["Categorie_niv_4"] == level4)
        & (df_meta["Nom du flux"].notna())
    )

    df_filtered = df_meta[mask]

    st.write(df_filtered)
    uuid_flux = df_filtered["UUID"].dropna().unique()

    impacts_merged = df_impacts.merge(df_cat, on="UUID_cat", how="left")
    impacts_merged.to_json("impacts__long.json", orient="records", force_ascii=False)

    impacts = impacts_merged[
        impacts_merged["UUID_procede"].isin(uuid_flux)
        & impacts_merged["Nom français"].isin(selected_categories)
    ]

    impacts_filtered_cat = impacts_merged[
        (impacts_merged["Nom français"].isin(selected_categories))
    ]

    st.write("Flux sélectionnés :")
    st.write("Type de la colonne 'valeur':", impacts["valeur"].dtype)
    st.write(impacts)
    # for _, row in df_filtered.iterrows():
    #     st.write(f"- {row['Nom du flux']}")

    # Visualisation des impacts
    st.subheader("Impacts environnementaux")
    if not impacts.empty:

        df_plot = impacts.sort_values("valeur", ascending=True)

        fig, ax = plt.subplots(figsize=(6, max(4, len(df_plot) * 0.4)))
        ax.barh(df_plot["Nom_procede"], df_plot["valeur"])
        ax.set_xlabel(selected_categories)
        ax.set_title(f"{selected_categories} pour chaque procédé")
        st.pyplot(fig)
    else:
        st.info("Aucun impact trouvé pour ce procédé.")

    # Histogramme des impacts de la catégorie sélectionnée
    st.subheader("Histogramme des impacts environnementaux")
    st.write(impacts_filtered_cat)
    if not impacts_filtered_cat.empty:
        fig, ax = plt.subplots(figsize=(6, max(4, len(impacts_filtered_cat) * 0.4)))
        ax.hist(
            impacts_filtered_cat["valeur"],
            bins=20,
            color="blue",
            alpha=0.7,
            edgecolor="black",
        )
        ax.set_xlabel("Valeur")
        ax.set_ylabel("Fréquence")
        ax.set_title(f"Histogramme des impacts environnementaux pour {level1}")
        st.pyplot(fig)
    else:
        st.info("Aucun impact trouvé pour cette catégorie.")
