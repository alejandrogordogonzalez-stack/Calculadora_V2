# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import streamlit as st

from common import (
    inject_css, euro_input, eur, fmt_number_es,
    amortization_schedule,
    prima_orientativa_bilineal, PRIMA_ING_DF,
    get_nn_dfs,
    sync_capital_from_source,
    render_footer
)

inject_css()

st.title("🎁 Estudio de Bonificaciones")

st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">Mi hipoteca</span>
      <span class="param-subtle">
        Estos parámetros son <strong>los de mi hipoteca</strong> (sin bonificaciones) y sirven como referencia.
      </span>
    </div>
    """,
    unsafe_allow_html=True
)

with st.form("params_form_bonif", clear_on_submit=False):
    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
    with c1:
        principal_b = euro_input(
            "Importe a financiar (Cantidad solicitada) (€)",
            key="p_bon_eur",
            default=150000.0,
            decimals=2,
            min_value=1000.0
        )
    with c2:
        years_b = st.slider("Plazo (años)", min_value=1, max_value=40, value=25, step=1, key="y_bon")
    with c3:
        annual_rate_pct_b = st.number_input(
            "Interés aplicado (% TIN anual)",
            min_value=0.0, max_value=30.0, value=3.0, step=0.05, format="%.2f", key="r_bon"
        )
    with c4:
        _ = st.selectbox(
            "Mes de inicio (agrupación anual)",
            options=list(range(1, 13)), index=0, format_func=lambda m: f"{m:02d}", key="m_bon"
        )
    _ = st.form_submit_button("✅ Aplicar parámetros")

n_months_b = years_b * 12
r_monthly_b = (annual_rate_pct_b / 100.0) / 12.0
df_base = amortization_schedule(principal_b, r_monthly_b, n_months_b)

if df_base.empty:
    st.warning("Introduce un importe y un plazo válidos.")
    st.stop()

monthly_payment_base = float(df_base["Cuota"].iloc[0])

m1c, m2c, m3c = st.columns(3)
m1c.metric("💳 Cuota mensual (sin bonificar)", eur(monthly_payment_base))
m2c.metric("📌 TIN anual (sin bonificar)", f"{annual_rate_pct_b:.2f} %")
m3c.metric("🗓️ Nº de cuotas (meses)", f"{n_months_b}")

st.divider()

st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">Bonificaciones</span>
      <span class="param-subtle">
        Introduce bonificaciones en <strong>puntos porcentuales</strong> sobre el TIN.
        Ejemplo: <strong>0,15</strong> significa que el TIN baja <strong>0,15%</strong>.
      </span>
    </div>
    """,
    unsafe_allow_html=True
)

with st.form("params_form_bonif_inputs", clear_on_submit=False):
    b1, b2, b3 = st.columns(3)
    with b1:
        bon_hogar = st.number_input(
            "Bonificación por seguro de hogar (%)",
            min_value=0.0, max_value=5.0, value=0.0, step=0.01, format="%.2f", key="bon_hogar"
        )
    with b2:
        bon_vida = st.number_input(
            "Bonificación por seguro de vida (%)",
            min_value=0.0, max_value=5.0, value=0.0, step=0.01, format="%.2f", key="bon_vida"
        )
    with b3:
        bon_otras = st.number_input(
            "Otras bonificaciones (%)",
            min_value=0.0, max_value=10.0, value=0.0, step=0.01, format="%.2f", key="bon_otras"
        )
    _ = st.form_submit_button("🧮 Calcular ahorro")

bon_total = float(bon_hogar + bon_vida + bon_otras)
annual_rate_bonif = max(float(annual_rate_pct_b - bon_total), 0.0)

if bon_total > annual_rate_pct_b:
    st.warning("La bonificación total supera el TIN: el TIN bonificado se ha limitado a 0,00%.")

r_monthly_bonif = (annual_rate_bonif / 100.0) / 12.0
df_bon = amortization_schedule(principal_b, r_monthly_bonif, n_months_b)
monthly_payment_bon = float(df_bon["Cuota"].iloc[0]) if not df_bon.empty else 0.0

ahorro_cuota_mes = monthly_payment_base - monthly_payment_bon
ahorro_anual = ahorro_cuota_mes * 12

st.markdown(
    f"""
    <div style="
        background:#e8f0fe;
        border:1px solid #4A90E2;
        border-radius:12px;
        padding:1rem 1.25rem;
        margin:.5rem 0 1rem 0;
    ">
      <div class="value-title">✅ TIN tras bonificaciones</div>
      <div class="value-big">{annual_rate_bonif:.2f} % <span style="font-size:.9rem;color:#5f6570;font-weight:600">
        (bonificación total: {bon_total:.2f} %)
      </span></div>
    </div>
    """,
    unsafe_allow_html=True
)

# ✅ CAMBIO PEDIDO: quitar el recuadro verde y dejarlo al nivel del resto
a1, a2, a3 = st.columns(3)
a1.metric("💳 Cuota mensual (bonificada)", eur(monthly_payment_bon), delta=eur(-ahorro_cuota_mes))
a2.metric("🧾 Ahorro mensual", eur(ahorro_cuota_mes))
a3.metric("📆 Ahorro anual", eur(ahorro_anual))

st.caption(
    "Nota: aquí medimos el ahorro como reducción de cuota por la bajada del TIN. "
    "No incluye el coste de los seguros/bonificaciones ni otros gastos/comisiones."
)

st.markdown(
    """
    <div style="
        background:#f5f7fa;
        border:1px solid #e6e9ef;
        border-radius:14px;
        padding:1rem 1.25rem;
        text-align:center;
        color:#2b2f36;
        box-shadow: 0 6px 18px rgba(0,0,0,0.05);
        margin: .75rem 0 1rem 0;
    ">
      <div style="font-weight:800; font-size:1.05rem; margin-bottom:.35rem;">
        💡 Antes de comparar bonificaciones…
      </div>
      <div style="font-size:.98rem; line-height:1.45; color:#5f6570;">
        ¿Sabía que los seguros que firma bonificados suelen ser entre un <strong>30%–40% más caros</strong>
        que los que no son contratados a través del banco?<br/><br/>
        Además, los seguros de vida <strong>suben con el paso del tiempo</strong>, pero la bonificación se mantiene
        <strong>estable</strong>. Por eso, esta diferencia puede hacer que merezca la pena contratar el seguro
        <strong>por fuera de la entidad bancaria</strong>.<br/><br/>
        A continuación, verá un ejemplo de <strong>prima orientativa</strong> de entidad bancaria (ING)
        y, a la derecha, una <strong>prima orientativa</strong> directamente en aseguradora.
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">Prima orientativa</span>
      <span class="param-subtle">
        Cálculo orientativo de prima en base a capital y edad (referencias a <strong>03/12/2025</strong>)
      </span>
    </div>
    """,
    unsafe_allow_html=True
)

# Defaults de capital (si no existía aún)
if "capital_ing_prima_eur" not in st.session_state and "capital_nn_prima_eur" not in st.session_state:
    st.session_state["capital_ing_prima_eur"] = "100.000"
    st.session_state["capital_nn_prima_eur"] = "100.000"

col_left, col_right = st.columns(2, gap="large")

# ===== IZQUIERDA: BANCO (ING) =====
with col_left:
    st.markdown(
        """
        <div class="prime-block">
          <div class="prime-title">🏦 Ejemplo primas — Seguro Entidad Bancaria</div>
          <div class="prime-sub">
            Prima orientativa calculada en base a <strong>capital</strong> y <strong>edad</strong>.
            Referencia: <strong>ING</strong> (03/12/2025).
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    cP1, cP2 = st.columns(2)
    with cP1:
        edad_ing = st.number_input(
            "Edad (años) — Banco",
            min_value=0, max_value=99, value=30, step=1, key="edad_ing_prima"
        )
    with cP2:
        # ✅ CAMBIO PEDIDO: al cambiar capital aquí, copiarlo al de Aseguradora
        def _sync_from_bank():
            sync_capital_from_source("capital_ing_prima_eur", ["capital_nn_prima_eur"], decimals=0)

        capital_ing = euro_input(
            "Capital a cubrir (€) — Banco",
            key="capital_ing_prima_eur",
            default=100000.0,
            decimals=0,
            min_value=0.0,
            max_value=1000000.0,
            on_change=_sync_from_bank
        )

    if capital_ing > 400000 or edad_ing > 65:
        st.warning("⚠️ Nota: cálculos orientativos; pueden no ser acordes a partir de 400.000 € y edades > 65.")

    if edad_ing <= 0 or capital_ing <= 0:
        st.info("Introduce una edad y un capital válidos para obtener la prima orientativa.")
        prima_ing = None
    else:
        prima_ing = prima_orientativa_bilineal(float(edad_ing), float(capital_ing), PRIMA_ING_DF)
        st.metric("🧾 Prima orientativa (mensual) — Banco", eur(prima_ing))

    st.caption(
        "Primas orientativas calculadas a 03/12/2025, como ejemplo real de primas de hipotecas con el seguro de ING."
    )

# ===== DERECHA: ASEGURADORA (NN) =====
with col_right:
    st.markdown(
        """
        <div class="prime-block">
          <div class="prime-title">🛡️ Ejemplo primas — Aseguradora</div>
          <div class="prime-sub">
            Cálculo orientativo (mismo esquema capital/edad) directamente en aseguradora.
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    r1, r2 = st.columns(2)
    with r1:
        edad_nn = st.number_input(
            "Edad (años) — Aseguradora",
            min_value=0, max_value=99, value=30, step=1, key="edad_nn_prima"
        )
    with r2:
        # ✅ CAMBIO PEDIDO: al cambiar capital aquí, copiarlo al de Banco
        def _sync_from_insurer():
            sync_capital_from_source("capital_nn_prima_eur", ["capital_ing_prima_eur"], decimals=0)

        capital_nn = euro_input(
            "Capital a cubrir (€) — Aseguradora",
            key="capital_nn_prima_eur",
            default=100000.0,
            decimals=0,
            min_value=0.0,
            max_value=1000000.0,
            on_change=_sync_from_insurer
        )

    cobertura = st.radio(
        "Cobertura",
        options=["Fallecimiento", "Fallecimiento + Invalidez Absoluta"],
        horizontal=True,
        key="cobertura_nn"
    )

    prima_nn = None
    if edad_nn <= 0 or capital_nn <= 0:
        st.info("Introduce una edad y un capital válidos para obtener la prima orientativa.")
    else:
        if cobertura == "Fallecimiento + Invalidez Absoluta" and edad_nn >= 60:
            st.warning("⚠️ Algunas aseguradoras no permiten Invalidez Absoluta a partir de 60 años.")
            st.info("Selecciona 'Fallecimiento' o reduce la edad para ver una prima orientativa con IA.")
        else:
            NN_FALLEC_DF, NN_FALL_IA_DF = get_nn_dfs()
            tabla_df = NN_FALL_IA_DF if cobertura == "Fallecimiento + Invalidez Absoluta" else NN_FALLEC_DF
            prima_nn = prima_orientativa_bilineal(float(edad_nn), float(capital_nn), tabla_df)
            st.metric("🧾 Prima orientativa (mensual) — Aseguradora", eur(prima_nn))

    st.caption(
        "Primas orientativas con cálculo del mismo seguro pero directamente en la aseguradora (Nationale Nederlanden). "
        "Ejemplo para una persona no fumadora, que no usa moto, no practica deporte de riesgo ni tiene trabajo de riesgo."
    )

st.divider()

# ---- Resumen (3 ahorros)
annual_rate_only_vida = max(float(annual_rate_pct_b - float(bon_vida)), 0.0)
r_only_vida_m = (annual_rate_only_vida / 100.0) / 12.0
df_only_vida = amortization_schedule(principal_b, r_only_vida_m, n_months_b)
monthly_payment_only_vida = float(df_only_vida["Cuota"].iloc[0]) if not df_only_vida.empty else monthly_payment_base

ahorro_vida_mes = monthly_payment_base - monthly_payment_only_vida
ahorro_vida_anual = ahorro_vida_mes * 12

prima_ing_comp = None
if edad_nn > 0 and capital_nn > 0:
    prima_ing_comp = prima_orientativa_bilineal(float(edad_nn), float(capital_nn), PRIMA_ING_DF)

ahorro_cambio_aseg_mes = None
ahorro_cambio_aseg_anual = None
if (prima_ing_comp is not None) and (prima_nn is not None):
    ahorro_cambio_aseg_mes = float(prima_ing_comp - prima_nn)
    ahorro_cambio_aseg_anual = ahorro_cambio_aseg_mes * 12

ahorro_neto_mes = None
ahorro_neto_anual = None
if ahorro_cambio_aseg_mes is not None:
    ahorro_neto_mes = float(ahorro_cambio_aseg_mes - ahorro_vida_mes)
    ahorro_neto_anual = ahorro_neto_mes * 12

st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">Resumen</span>
      <span class="param-subtle">Impacto orientativo (bonificación vs precio del seguro).</span>
    </div>
    """,
    unsafe_allow_html=True
)

s1, s2, s3 = st.columns([1, 1, 1])

with s1:
    st.markdown(
        f"""
        <div class="soft-box">
          <div class="value-title">💚 Ahorro por bonificación del seguro de vida (solo TIN)</div>
          <div class="value-big">{eur(ahorro_vida_mes)}/mes</div>
          <div class="prime-note">{eur(ahorro_vida_anual)}/año</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with s2:
    if ahorro_cambio_aseg_mes is None:
        st.markdown(
            """
            <div class="soft-box">
              <div class="value-title">🔁 Ahorro por cambio de aseguradora (prima)</div>
              <div class="value-big">—</div>
              <div class="prime-note">Introduce valores válidos en el bloque de Aseguradora.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="soft-box">
              <div class="value-title">🔁 Ahorro por cambio de aseguradora (prima)</div>
              <div class="value-big">{eur(ahorro_cambio_aseg_mes)}/mes</div>
              <div class="prime-note">{eur(ahorro_cambio_aseg_anual)}/año</div>
            </div>
            """,
            unsafe_allow_html=True
        )

with s3:
    if ahorro_neto_mes is None:
        st.markdown(
            """
            <div class="highlight-total">
              <div class="k">✨ Ahorro con cambio de aseguradora (restando bonificaciones)</div>
              <div class="v">—</div>
              <div class="prime-note">Pendiente de una prima válida en el bloque de Aseguradora.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="highlight-total">
              <div class="k">✨ Ahorro con cambio de aseguradora (restando bonificaciones)</div>
              <div class="v">{eur(ahorro_neto_mes)}/mes</div>
              <div class="prime-note">{eur(ahorro_neto_anual)}/año — <strong>este es el dato clave (colofón)</strong>.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

st.caption(
    "Lectura del resumen: el 'Ahorro neto' asume que si cambias el seguro de vida fuera del banco podrías perder "
    "la bonificación por vida (por eso se resta el ahorro del TIN atribuible a esa bonificación)."
)

render_footer()
