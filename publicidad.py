# -*- coding: utf-8 -*-
import streamlit as st
from common import inject_css, render_footer

inject_css()

st.title("ℹ️ Información")

st.markdown(
    """
    <div style="
        background:#ffffff;
        border:1px solid #e6e9ef;
        border-radius:16px;
        padding:1.1rem 1.25rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.05);
        margin: .25rem 0 1rem 0;
    ">
      <div style="font-size:1.15rem;font-weight:900;color:#1f2430;margin-bottom:.35rem;">
        Asesoramiento financiero gratuito
      </div>

      <div style="color:#5f6570;font-size:.98rem;line-height:1.55;">
        Somos asesores financieros y hemos desarrollado esta herramienta con el objetivo de ayudarte a conseguir
        la mejor hipoteca en las mejores condiciones, analizando cada detalle de forma clara y transparente.
        <br/><br/>

        Si necesitas asesoramiento financiero, no dudes en contactar con nuestro equipo. El asesoramiento es
        <strong>totalmente gratuito y sin compromiso</strong>. Podemos ayudarte a:
        <ul style="margin:.55rem 0 .55rem 1.2rem;">
          <li>Entender tu hipoteca y sus condiciones reales</li>
          <li>Optimizar amortizaciones y reducir costes</li>
          <li>Buscar la mejor hipoteca (incluso hasta el 100% de financiación, si aplica)</li>
          <li>Mejorar tus seguros vinculados o compararlos con alternativas</li>
        </ul>

        También estamos abiertos a sugerencias, mejoras y colaboraciones.
        <br/><br/>

        <strong>Para más información, contacta con:</strong>
        <a href="mailto:alejandro.gordo@nnespana.com">alejandro.gordo@nnespana.com</a>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

render_footer()
