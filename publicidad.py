# -*- coding: utf-8 -*-
import streamlit as st
from common import inject_css, render_footer

inject_css()

st.title("🖼️ Publicidad")

st.markdown("<div style='text-align:center'>", unsafe_allow_html=True)
st.image("publi.jpg", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

render_footer()
