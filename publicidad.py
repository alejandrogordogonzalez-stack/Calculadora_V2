# -*- coding: utf-8 -*-
import streamlit as st
from common import inject_css, render_footer

inject_css()

st.title("ℹ️ Información")

st.markdown(
    """
### Asesoramiento financiero gratuito

Somos asesores financieros y hemos desarrollado esta herramienta con el objetivo de ayudarte a conseguir la **mejor hipoteca** en las **mejores condiciones**, analizando cada detalle de forma clara y transparente.

Si necesitas asesoramiento financiero, no dudes en contactar con nuestro equipo. El asesoramiento es **totalmente gratuito y sin compromiso**. Podemos ayudarte a:

- Entender tu hipoteca y sus condiciones reales  
- Optimizar amortizaciones y reducir costes  
- Buscar la mejor hipoteca (incluso hasta el 100% de financiación, si aplica)  
- Mejorar tus seguros vinculados o compararlos con alternativas  

También estamos abiertos a sugerencias, mejoras y colaboraciones.

**Para más información, contacta con:**  
[alejandro.gordo@nnespana.com](mailto:alejandro.gordo@nnespana.com)
"""
)

render_footer()
