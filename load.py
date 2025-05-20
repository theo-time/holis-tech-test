import pandas as pd
from scipy.cluster.hierarchy import linkage, leaves_list
import streamlit as st
from collections import Counter
import matplotlib.pyplot as plt
from io import BytesIO
from analyse_pays import generate_tables_pays


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


def create_group_tables(df):
    # 1. Répartition catégorie + unité + quantité de référence
    unit_table = (
        df.groupby(
            [
                "Categorie_niv_1",
                "Categorie_niv_2",
                "Categorie_niv_3",
                "Categorie_niv_4",
                "Unité",
                "Quantité de référence",
            ]
        )
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    # 2. Répartition catégorie + zone géographique
    geo_table = (
        df.groupby(
            [
                "Categorie_niv_1",
                "Categorie_niv_2",
                "Categorie_niv_3",
                "Categorie_niv_4",
                "Zone géographique",
            ]
        )
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    # 3. Répartition catégorie + Type de dataset
    dataset_table = (
        df.groupby(
            [
                "Categorie_niv_1",
                "Categorie_niv_2",
                "Categorie_niv_3",
                "Categorie_niv_4",
                "Type de dataset",
            ]
        )
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    return unit_table, geo_table, dataset_table


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

    # Trims de toutes les colonnes de type string
    for col in df_meta.select_dtypes(include=["object"]).columns:
        df_meta[col] = df_meta[col].str.strip()

    df_meta.rename(
        columns={
            "Catégorisation (niveau 1)": "Categorie_niv_1",
            "Catégorisation (niveau 2)": "Categorie_niv_2",
            "Catégorisation (niveau 3)": "Categorie_niv_3",
            "Catégorisation (niveau 4)": "Categorie_niv_4",
        },
        inplace=True,
    )

    # Export de la liste des colonnes en json

    with open("export/columns_meta_procedes.txt", "w", encoding="utf-8") as f:
        for col in df_meta.columns:
            f.write(col + "\n")

    # Impacts
    df_impacts, df_impacts_large = load_impacts("data/BI_2.02__03_Procedes_Impacts.csv")

    st.write("df_impacts_large")
    st.write(df_impacts_large)

    # Catégories d'impacts
    df_cat = read_excel_with_dual_headers("data/BI_2.02__06_CatImpacts_Details.xlsx")
    df_cat.rename(columns={"UUID": "UUID_cat"}, inplace=True)

    # Trims de toutes les colonnes de type string
    for col in df_cat.select_dtypes(include=["object"]).columns:
        df_cat[col] = df_cat[col].str.strip()

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
                "Type de dataset",
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

    # Trims de toutes les colonnes de type string
    for col in df_impacts_merged.select_dtypes(include=["object"]).columns:
        df_impacts_merged[col] = df_impacts_merged[col].str.strip()

    # Ajout de données statistiques --------------------------------------

    df_im = df_impacts_merged.copy()

    # 1. Normalisation globale par catégorie d’impact
    df_im["valeur_norm_median"] = df_im.groupby("category_name")["valeur"].transform(
        lambda x: x / x.median()
    )
    df_im["valeur_norm_q3"] = df_im.groupby("category_name")["valeur"].transform(
        lambda x: x / x.quantile(0.75)
    )

    # 2. Calcul des moyennes, médianes, et Q3 par combinaison de catégories niv1 à niv4
    group_cols = [
        "Categorie_niv_1",
        "Categorie_niv_2",
        "Categorie_niv_3",
        "Categorie_niv_4",
        "category_name",
    ]

    # Moyenne de la valeur brute par catégorie
    agg_df = (
        df_im.groupby(group_cols)["valeur"]
        .agg(moyenne_cat="mean", median_cat="median", q3_cat=lambda x: x.quantile(0.75))
        .reset_index()
    )

    # 3. Merge pour rattacher les stats agrégées au dataframe original
    df_im = df_im.merge(agg_df, on=group_cols, how="left")

    st.write("df_im")
    st.write(df_im)

    # Insertion d'un score d'impact global qui est la somme des impacts normalisés q3
    # l'impact global est considéré comme une catégorie d'impact
    global_impacts = (
        df_im.groupby(
            [
                "UUID_procede",
                "Nom_procede",
                "Categorie_niv_1",
                "Categorie_niv_2",
                "Categorie_niv_3",
                "Categorie_niv_4",
            ]
        )["valeur_norm_q3"]
        .sum()
        .reset_index()
    )
    global_impacts["category_name"] = "Impact global"
    global_impacts["valeur"] = global_impacts["valeur_norm_q3"]

    # Remove first column
    # global_impacts = global_impacts.drop(columns=["valeur_norm_q3"])
    st.write("global_impacts")
    st.write(global_impacts)

    # Insertion de l'impact global dans le dataframe
    # df_im = pd.concat([df_im, global_impacts], ignore_index=True)
    st.write("df_im")
    st.write(df_im)
    # df_cat.to_json("categorie_impacts.json", orient="records", force_ascii=False)

    # Correlations de matrice -----------------------------------------

    # On ne garde que les colonnes numériques
    df_value_only = df_impacts_large.drop(
        columns=[
            "Nom français",
            "French Name",
        ]
    )

    # Génération de la Matrice de corrélation
    corr = df_value_only.corr()

    # Affichage de la matrice de correlation
    st.write("Matrice de corrélation :")
    st.write(corr)

    # Clustering
    link = linkage(corr, method="average")  # ou 'ward'
    idx = leaves_list(link)  # indices ordonnés

    # Réordonner la matrice
    corr_reordered = corr.iloc[idx, idx]

    # Conversion pour export
    corr_reordered_long = corr_reordered.reset_index().melt(id_vars="index")
    corr_reordered_long.columns = ["x", "y", "value"]

    # Export JSON
    corr_reordered_long.to_json(
        "correlations.json", orient="records", force_ascii=False
    )

    # Analyse Zones géo / unités --------------------------------

    unit_table, geo_table, dataset_table = create_group_tables(df_meta)

    # Liste des unités distinctes (sans doublons, triée)
    unit_list = df_meta["Unité"].dropna().unique()
    unit_list = sorted(set(unit_list))
    unit_list = pd.DataFrame(unit_list, columns=["Unité"])

    # Liste des types de datasets distincts (sans doublons, triée)
    datasets_list = df_meta["Type de dataset"].dropna().unique()
    datasets_list = sorted(set(datasets_list))
    datasets_list = pd.DataFrame(datasets_list, columns=["Type de dataset"])

    # display tables
    st.write("datasets_list")
    st.write(datasets_list)
    st.write("Tableau de répartition par catégorie + zone géographique")
    st.write(geo_table)
    st.write("Tableau de répartition par catégorie + unité + quantité de référence")
    st.write(unit_table)
    st.write("Tableau de répartition par catégorie + Type de dataset")
    st.write(dataset_table)

    # Export des tables
    df_im.to_json(
        "export/impacts_long_merged.json", orient="records", force_ascii=False
    )
    df_cat.to_json(
        "export/categories_metadata.json", orient="records", force_ascii=False
    )
    unit_list.to_json("export/unit_list.json", orient="records", force_ascii=False)
    unit_table.to_json("export/unit_table.json", orient="records", force_ascii=False)
    datasets_list.to_json(
        "export/datasets_list.json", orient="records", force_ascii=False
    )
    geo_table.to_json("export/geo_table.json", orient="records", force_ascii=False)

    return df_meta, df_impacts, df_cat
