import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from load import (
    load_data,
)

# Imports internes
from page_procede import page_procede
from page_comparatif import page_comparatif


st.set_page_config(
    page_title="Dashboard Empreinte",  # layout="wide"  # 👈 ceci active le mode large
)

df_meta, df_impacts, df_cat = load_data()

# Menu de navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Aller à :", ["Accueil", "Impacts par procédé", "Comparatif procédé", "À propos"]
)

page_comparatif(df_meta, df_impacts, df_cat)

# # Page: Accueil
# if page == "Accueil":
#     st.title("Bienvenue dans le Dashboard Empreinte")
#     st.markdown(
#         """
#     Ce tableau de bord vous permet d'explorer les impacts environnementaux issus de la Base Impacts 2.02.
#     """
#     )

# if page == "Impacts par procédé":
#     st.title("Visualisation des impacts environnementaux par procédé")

#     page_procede(df_meta, df_impacts, df_cat)

# if page == "Comparatif procédé":
#     st.title("Comparatif des impacts environnementaux entre procédés")
#     st.markdown(
#         """
#     Cette page vous permet de comparer les impacts environnementaux entre différents procédés.
#     """
#     )

#     page_comparatif(df_meta, df_impacts, df_cat)


# st.write(df_impacts.dtypes)
# st.write(df_meta.columns.tolist())
# st.write(df_impacts.columns.tolist())
# st.write(df_impacts)
# st.write(df_cat)
