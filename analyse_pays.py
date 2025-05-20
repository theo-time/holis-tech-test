import pandas as pd
from scipy.cluster.hierarchy import linkage, leaves_list
import streamlit as st
from collections import Counter
import matplotlib.pyplot as plt
from io import BytesIO


def generate_tables_pays(df_impacts):
    """ """
    # remove trailing semicolon on Zone geo
    df_impacts["Zone géographique"] = df_impacts["Zone géographique"].str.rstrip(";")

    # Données mix electrique
    st.write(df_impacts)
    df_impacts["Categorie_niv_3"] = df_impacts["Categorie_niv_3"].str.strip()
    df_mix_electrique = df_impacts[df_impacts["Categorie_niv_2"] == "Electricité"]
    df_mix_electrique = df_mix_electrique[
        df_mix_electrique["Categorie_niv_3"] == "Mix moyen"
    ]

    # Données transport ferroviaire
    df_transport_ferro = df_impacts[df_impacts["Categorie_niv_2"] == "Ferroviaire"]
    df_transport_ferro = df_transport_ferro[
        df_transport_ferro["Categorie_niv_3"] == "Flotte moyenne nationale européenne"
    ]

    # Données transport routier
    df_transport_routier = df_impacts[df_impacts["Categorie_niv_2"] == "Routier"]
    df_transport_routier = df_transport_routier[
        df_transport_routier["Categorie_niv_3"] == "Transport à température ambiante"
    ]
    df_transport_routier = df_transport_routier[
        df_transport_routier["Categorie_niv_4"] == "Flotte moyenne nationale européenne"
    ]
    df_transport_routier = df_transport_routier[
        ~df_transport_routier["Nom_procede"].str.contains("100%", na=False)
    ]

    # display le tableau
    st.subheader("Tableau des pays")
    st.write(df_mix_electrique)
    st.write(df_transport_ferro)
    st.write(df_transport_routier)

    # Exporter le tableau en json
    df_mix_electrique.to_json(
        "export/mix_electriques.json", orient="records", force_ascii=False
    )
    df_transport_ferro.to_json(
        "export/transport_ferro.json", orient="records", force_ascii=False
    )
    df_transport_routier.to_json(
        "export/transport_routier.json", orient="records", force_ascii=False
    )

    return
