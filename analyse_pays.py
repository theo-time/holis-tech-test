import pandas as pd
from scipy.cluster.hierarchy import linkage, leaves_list
import streamlit as st
from collections import Counter
import matplotlib.pyplot as plt
from io import BytesIO


def generate_tables_pays(df_impacts):
    """ """
    st.write(df_impacts)
    df_impacts["Categorie_niv_3"] = df_impacts["Categorie_niv_3"].str.strip()
    df_mix_electrique = df_impacts[df_impacts["Categorie_niv_3"] == "Mix moyen"]

    # display le tableau
    st.subheader("Tableau des pays")
    st.write(df_mix_electrique)
    return
