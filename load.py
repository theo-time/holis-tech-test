import pandas as pd
from scipy.cluster.hierarchy import linkage, leaves_list
import streamlit as st
from collections import Counter
import matplotlib.pyplot as plt
from io import BytesIO


def read_excel_with_dual_headers(path):
    df_raw = pd.read_excel(path, header=None).T

    # Extract the first two rows as potential headers
    row_fr = df_raw.iloc[0].astype(str).str.strip()
    row_en = df_raw.iloc[1].astype(str).str.strip()

    # Use French label if it's non-empty, otherwise fallback to English
    combined_headers = [fr if fr else en for fr, en in zip(row_fr, row_en)]

    duplicates = [col for col, count in Counter(combined_headers).items() if count > 1]
    print("Colonnes dupliquées :", duplicates)

    # Assign new headers and remove the first two rows
    df_clean = df_raw.iloc[2:].copy()
    df_clean.columns = combined_headers
    df_clean.reset_index(drop=True, inplace=True)

    return df_clean


def load_excel_transpose(file_path):
    """
    Charge un fichier Excel et le transpose.
    :param file_path: Chemin du fichier Excel
    :return: DataFrame transposé
    """
    df = pd.read_excel(file_path, header=None)
    df = df.T  # Transpose lignes <-> colonnes
    df.columns = df.iloc[0]  # Première ligne devient les noms de colonnes
    df = df[1:]  # Enlève la ligne des noms maintenant qu'elle est en colonnes
    df.reset_index(drop=True, inplace=True)

    # Nettoyage des noms de colonnes :
    df.columns = (
        df.columns.astype(str)  # Au cas où certaines colonnes ne sont pas des strings
        .str.strip()  # Supprime les espaces en début/fin
        .str.replace(r"\s+", " ", regex=True)  # Réduit les espaces multiples à un seul
    )
    return df


def load_impacts(file_path):
    """
    Charge un fichier CSV contenant des impacts environnementaux.
    :param file_path: Chemin du fichier CSV
    :return: DataFrame avec les impacts
    """
    df_raw = pd.read_csv(file_path, encoding="latin1", sep=";", header=None).T

    # Étape 1 : On récupère les metadonnées des catégories d'impacts (Lignes 0 à 3)
    column_metadata = df_raw.iloc[0:4, 2:]

    # Etape 2 : On set proprement les noms de colonnes
    cols = [str(col).strip() for col in df_raw.iloc[0].tolist()]
    cols[0] = "UUID_procede"
    cols[1] = "Nom_procede"
    df_raw.columns = cols

    # On garde créé la version large du dataframe
    # row 2 devient les noms de colonnes, et on supprime jusqu'à la ligne 3
    df_large = df_raw.copy()
    df_large.columns = [str(col).strip() for col in df_large.iloc[2].tolist()]
    df_large = df_large[
        4:
    ]  # Enlève la ligne des noms maintenant qu'elle est en colonnes
    df_large.reset_index(drop=True, inplace=True)

    # Etape 3 : On retire les metadonnées
    df_data = df_raw.iloc[4:, :]  # données des

    # Étape 4 : On melt les données
    df_melted = df_data.melt(
        id_vars=[
            "UUID_procede",
            "Nom_procede",
        ],  # UUID procédé et nom procédé (colonnes 0 et 1)
        var_name="UUID_cat",  # index de colonne (ex: 2, 3, 4...)
        value_name="valeur",
    )

    df_melted["valeur"] = pd.to_numeric(df_melted["valeur"], errors="coerce")
    # df.columns = df.iloc[1]  # Première ligne devient les noms de colonnes
    # df = df[4:]  # Enlève la ligne des noms maintenant qu'elle est en colonnes
    # df.reset_index(drop=True, inplace=True)
    return df_melted, df_large


# Configuration de la page
# Chargement des données
@st.cache_data
def load_data():
    """
    Charge les données nécessaires pour le tableau de bord.
    :return: DataFrames contenant les métadonnées, les impacts et les catégories d'impacts
    """
    # Metadonnées
    df_meta = read_excel_with_dual_headers("data/BI_2.02__02_Procedes_Details.xlsx")
    df_meta["UUID"] = df_meta["UUID"].str.strip()  # Supprime les espaces en début/fin
    df_meta.rename(
        columns={
            "Catégorisation (niveau 1)": "Categorie_niv_1",
            "Catégorisation (niveau 2)": "Categorie_niv_2",
            "Catégorisation (niveau 3)": "Categorie_niv_3",
            "Catégorisation (niveau 4)": "Categorie_niv_4",
        },
        inplace=True,
    )

    # Impacts
    df_impacts, df_impacts_large = load_impacts("data/BI_2.02__03_Procedes_Impacts.csv")

    st.write("df_impacts_large")
    st.write(df_impacts_large)

    # Catégories d'impacts
    df_cat = read_excel_with_dual_headers("data/BI_2.02__06_CatImpacts_Details.xlsx")
    df_cat.rename(columns={"UUID": "UUID_cat"}, inplace=True)
    df_cat["UUID_cat"] = df_cat[
        "UUID_cat"
    ].str.strip()  # Supprime les espaces en début/fin

    # Merge impacts with meta data
    df_impacts_merged = df_impacts.merge(
        df_meta[
            [
                "UUID",
                "Nom du flux",
                "Categorie_niv_1",
                "Categorie_niv_2",
                "Categorie_niv_3",
                "Categorie_niv_4",
                "Quantité de référence",
                "Unité",
                "Zone géographique",
            ]
        ],
        left_on="UUID_procede",
        right_on="UUID",
        how="left",
    )

    # merge with categorie to get 'Nom français' as Nom_categorie
    df_impacts_merged = df_impacts_merged.merge(
        df_cat[["UUID_cat", "Nom français", "Unité de référence"]],
        left_on="UUID_cat",
        right_on="UUID_cat",
        how="left",
    )
    df_impacts_merged.rename(
        columns={
            "Nom français": "category_name",
        },
        inplace=True,
    )
    st.write("df_impacts_merged")
    st.write(df_impacts_merged)

    # Trims des colonnes
    df_meta["Categorie_niv_1"] = df_meta["Categorie_niv_1"].str.strip()
    df_meta["Categorie_niv_2"] = df_meta["Categorie_niv_2"].str.strip()
    df_meta["Categorie_niv_3"] = df_meta["Categorie_niv_3"].str.strip()
    df_meta["Categorie_niv_4"] = df_meta["Categorie_niv_4"].str.strip()
    df_impacts_merged["category_name"] = df_impacts_merged["category_name"].str.strip()

    df_impacts_merged.to_json(
        "impacts_long_merged.json", orient="records", force_ascii=False
    )
    df_cat.to_json("categories_metadata.json", orient="records", force_ascii=False)
    # df_cat.to_json("categorie_impacts.json", orient="records", force_ascii=False)

    # Correlations de matrice -----------

    # On ne garde que les colonnes numériques
    df_value_only = df_impacts_large.drop(
        columns=[
            "Nom français",
            "French Name",
        ]
    )

    # Generation de la matrice de correlation
    correlation_matrix = df_value_only.corr(method="pearson")

    # Affichage de la matrice de correlation
    st.write("Matrice de corrélation :")
    st.write(correlation_matrix)

    # Clustering
    link = linkage(correlation_matrix, method="average")  # ou 'ward'
    idx = leaves_list(link)  # indices ordonnés

    # Réordonner la matrice
    corr_reordered = correlation_matrix.iloc[idx, idx]

    # Conversion pour export
    corr_reordered_long = corr_reordered.reset_index().melt(id_vars="index")
    corr_reordered_long.columns = ["x", "y", "value"]

    # Export JSON
    corr_reordered_long.to_json(
        "correlations.json", orient="records", force_ascii=False
    )

    return df_meta, df_impacts, df_cat
