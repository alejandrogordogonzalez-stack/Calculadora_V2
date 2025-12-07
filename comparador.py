# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import streamlit as st

from common import (
    inject_css, euro_input, eur, amortization_schedule,
    mixed_total_interest, solve_r2_for_equal_interest,
    render_footer
)

inject_css()

st.title("📐 Comparador: Hipoteca Fija vs Mixta")

st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">Parámetros — Hipoteca Fija (referencia)</span>
      <span class="param-subtle">Estos definen la hipoteca fija con la que igualaremos intereses.</span>
    </div>
    """,
    unsafe_allow_html=True
)

with st.form("params_form_cmp_base", clear_on_submit=False):
    c1b, c2b, c3b, c4b = st.columns([1.2, 1, 1, 1])
    with c1b:
        P_cmp = euro_input(
            "Importe a financiar (Cantidad solicitada) (€)",
            key="p_cmp_eur",
            default=100000.0,
            decimals=2,
            min_value=1000.0
        )
    with c2b:
        Y_cmp = st.slider("Plazo (años)", min_value=1, max_value=40, value=20, step=1, key="y_cmp")
    with c3b:
        Rfix_cmp = st.number_input(
            "Interés fijo de referencia (% TIN anual)",
            min_value=0.0, max_value=30.0, value=3.0, step=0.05, format="%.2f", key="rfix_cmp"
        )
    with c4b:
        _ = st.selectbox(
            "Mes de inicio (opcional, para agrupación anual)",
            options=list(range(1, 13)), index=0, format_func=lambda m: f"{m:02d}", key="m_cmp"
        )
    _ = st.form_submit_button("✅ Aplicar parámetros de FIJA")

n_cmp = Y_cmp * 12
rfix_m = (Rfix_cmp / 100.0) / 12.0

st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">Parámetros — Hipoteca Mixta</span>
      <span class="param-subtle">Periodo 1 fijo y cálculo del tipo necesario en el periodo 2 (variable).</span>
    </div>
    """,
    unsafe_allow_html=True
)

with st.form("params_form_cmp_mixed", clear_on_submit=False):
    c1m, c2m = st.columns([1, 1])
    with c1m:
        Y_change = st.slider(
            "Año donde cambias de fijo a variable",
            min_value=0, max_value=Y_cmp, value=min(5, Y_cmp), step=1, key="y_change"
        )
    with c2m:
        R1_mixed = st.number_input(
            "Interés aplicado en el periodo 1 (fijo de la mixta) — % TIN anual",
            min_value=0.0, max_value=30.0, value=2.5, step=0.05, format="%.2f", key="r1_mixed"
        )
    _ = st.form_submit_button("🧮 Calcular interés necesario del periodo 2 (variable)")

if P_cmp <= 0 or n_cmp <= 0:
    st.warning("Introduce un importe y un plazo válidos.")
    st.stop()

df_fix_cmp = amortization_schedule(P_cmp, rfix_m, n_cmp)
monthly_payment_fixed = float(df_fix_cmp["Cuota"].iloc[0])

m1_months = Y_change * 12
r1_m = (R1_mixed / 100.0) / 12.0
r2_m_solution, tgt_fixed, _, _, _ = solve_r2_for_equal_interest(P_cmp, n_cmp, rfix_m, r1_m, m1_months)

colA, colB, colC = st.columns(3)
colA.metric("💡 Intereses totales FIJA (objetivo)", eur(tgt_fixed))
colB.metric("💳 Cuota mensual FIJA", eur(monthly_payment_fixed))
colC.metric("⏱️ Meses totales", f"{n_cmp}")

st.divider()

n2 = max(n_cmp - m1_months, 0)

if r1_m == 0:
    cuota_p1 = P_cmp / n_cmp
else:
    cuota_p1 = P_cmp * r1_m / (1 - (1 + r1_m) ** (-n_cmp))

if n2 > 0:
    r2_for_calc = r2_m_solution if r2_m_solution is not None else 0.0
    _, _, _, saldo_p1_tmp = mixed_total_interest(P_cmp, n_cmp, r1_m, m1_months, r2_for_calc)
    if r2_for_calc == 0:
        cuota_p2 = saldo_p1_tmp / n2
    else:
        cuota_p2 = saldo_p1_tmp * r2_for_calc / (1 - (1 + r2_for_calc) ** (-n2))
else:
    cuota_p2 = 0.0

cI1, cI2, cI3, cI4 = st.columns(4)

with cI1:
    st.markdown(
        f"<div class='value-title'>Interés periodo 1 (mixta)</div>"
        f"<div class='value-big'>{R1_mixed:.3f} % TIN</div>",
        unsafe_allow_html=True
    )

with cI2:
    if m1_months >= n_cmp:
        st.markdown(
            "<div class='soft-box'>"
            "<div class='value-title'>Interés necesario periodo 2 (mixta)</div>"
            "<div class='value-big'>—</div>"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        if r2_m_solution is None:
            st.markdown(
                "<div class='soft-box'>"
                "<div class='value-title'>Interés necesario periodo 2 (mixta)</div>"
                "<div class='value-big'>No encontrado</div>"
                "</div>",
                unsafe_allow_html=True
            )
        else:
            r2_annual_pct = r2_m_solution * 12 * 100.0
            st.markdown(
                f"<div class='soft-box'>"
                f"<div class='value-title'>Interés necesario periodo 2 (mixta)</div>"
                f"<div class='value-big'>{r2_annual_pct:.3f} % TIN</div>"
                f"</div>",
                unsafe_allow_html=True
            )

with cI3:
    st.markdown(
        f"<div class='value-title'>Cuota mensual periodo 1</div>"
        f"<div class='value-big'>{eur(cuota_p1)}</div>",
        unsafe_allow_html=True
    )

with cI4:
    if n2 > 0 and r2_m_solution is not None:
        st.markdown(
            f"<div class='value-title'>Cuota mensual periodo 2</div>"
            f"<div class='value-big'>{eur(cuota_p2)}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='value-title'>Cuota mensual periodo 2</div>"
            f"<div class='value-big'>—</div>",
            unsafe_allow_html=True
        )

st.markdown("### 📘 Resumen — Hipoteca Fija")
fija_df = pd.DataFrame({
    "Concepto": ["Cuota mensual a pagar", "Valor Hipoteca", "Intereses Totales", "Suma Capital+Intereses"],
    "Valor": [monthly_payment_fixed, P_cmp, tgt_fixed, P_cmp + tgt_fixed]
})
st.dataframe(fija_df.style.format({"Valor": eur}), use_container_width=True)

st.markdown("### 🧩 Resumen — Hipoteca Mixta")
r2_for_table = r2_m_solution if r2_m_solution is not None else 0.0
mixed_total_chk, ip1_chk, ip2_chk, _ = mixed_total_interest(P_cmp, n_cmp, r1_m, m1_months, r2_for_table)
mixta_df = pd.DataFrame({
    "Concepto": [
        "Cuota a pagar periodo 1", "Cuota a pagar periodo 2",
        "Intereses periodo 1", "Intereses periodo 2",
        "Valor Hipoteca", "Intereses Totales", "Suma Capital+Intereses"
    ],
    "Valor": [
        cuota_p1,
        cuota_p2 if r2_m_solution is not None else np.nan,
        ip1_chk,
        ip2_chk if r2_m_solution is not None else np.nan,
        P_cmp,
        mixed_total_chk,
        P_cmp + mixed_total_chk
    ]
})
st.dataframe(
    mixta_df.style.format({"Valor": lambda x: "—" if (isinstance(x, float) and np.isnan(x)) else eur(x)}),
    use_container_width=True
)

diff = mixed_total_chk - tgt_fixed
st.caption(f"Diferencia (mixta - fija): {eur(diff)} (≈ 0 si la solución iguala los intereses).")

render_footer()
