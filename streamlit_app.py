# -*- coding: utf-8 -*-
import streamlit as st

st.set_page_config(page_title="Simulador de Hipoteca", layout="wide")

# Menú con URLs por pestaña (requiere Streamlit reciente: st.navigation + url_path)
pages = [
    st.Page("simulador.py", title="Simulador Hipoteca Fija", icon="📊", url_path="simulador"),
    st.Page("simulador_mixta.py", title="Simulador Hipoteca Mixta", icon="📊", url_path="simulador_mixta"),
    st.Page("bonificaciones.py", title="Estudio Bonificaciones", icon="🎁", url_path="bonificaciones"),
    st.Page("comparador.py", title="Comparador: Fija vs Mixta", icon="📐", url_path="comparador"),
    st.Page("inversion.py", title="Analiza Inversión", icon="💹", url_path="inversion"),
    st.Page("publicidad.py", title="Quienes Somos", icon="🖼️", url_path="publicidad"),
]

pg = st.navigation(pages, position="sidebar")
pg.run()
