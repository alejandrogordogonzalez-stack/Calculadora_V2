# -*- coding: utf-8 -*-
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import inject_css, euro_input, eur, amortization_schedule, render_footer

inject_css()

st.title("🏠 Simulador de Hipoteca")
st.caption(
    "Introduce el importe, el plazo y el interés anual. "
    "El cálculo asume capitalización mensual (interés nominal anual / 12)."
)

st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">Parámetros</span>
      <span class="param-subtle">Configura el simulador y pulsa “Aplicar parámetros”.</span>
    </div>
    """,
    unsafe_allow_html=True
)

with st.form("params_form_sim", clear_on_submit=False):
    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
    with c1:
        principal = euro_input(
            "Importe a financiar (Cantidad solicitada) (€)",
            key="p_sim_eur",
            default=150000.0,
            decimals=2,
            min_value=1000.0
        )
    with c2:
        years = st.slider("Plazo (años)", min_value=1, max_value=40, value=25, step=1, key="y_sim")
    with c3:
        annual_rate_pct = st.number_input(
            "Interés aplicado (% TIN anual)",
            min_value=0.0, max_value=30.0, value=3.0, step=0.05, format="%.2f", key="r_sim"
        )
    with c4:
        start_month = st.selectbox(
            "Mes de inicio (agrupación anual)",
            options=list(range(1, 13)), index=0, format_func=lambda m: f"{m:02d}", key="m_sim"
        )
    _ = st.form_submit_button("✅ Aplicar parámetros")

n_months = years * 12
r_monthly = (annual_rate_pct / 100.0) / 12.0
df = amortization_schedule(principal, r_monthly, n_months)

if df.empty:
    st.warning("Introduce un importe y un plazo válidos.")
    st.stop()

total_interest = float(df["Intereses"].sum())
monthly_payment = float(df["Cuota"].iloc[0])

m1c, m2c, m3c = st.columns(3)
m1c.metric("💳 Cuota mensual", eur(monthly_payment))
m2c.metric("💡 Intereses totales a pagar", eur(total_interest))
m3c.metric("🗓️ Nº de cuotas (meses)", f"{n_months}")

st.divider()

pie_fig = go.Figure(data=[go.Pie(labels=["Principal", "Intereses"], values=[principal, total_interest], hole=0.35)])
pie_fig.update_layout(
    title="Distribución total: principal vs intereses",
    legend=dict(orientation="h", yanchor="bottom", y=-0.05, xanchor="center", x=0.5),
)

df["Mes calendario"] = ((df["Mes"] - 1 + (start_month - 1)) % 12) + 1
df["Año"] = ((df["Mes"] - 1 + (start_month - 1)) // 12) + 1
annual = df.groupby("Año", as_index=False)[["Intereses", "Amortización"]].sum().round(2)

bar_fig = go.Figure()
bar_fig.add_trace(go.Bar(x=annual["Año"], y=annual["Intereses"], name="Intereses"))
bar_fig.add_trace(go.Bar(x=annual["Año"], y=annual["Amortización"], name="Amortización"))
bar_fig.update_layout(
    barmode="stack",
    title="Pago anual desglosado (apilado): amortización vs intereses",
    xaxis_title="Año",
    yaxis_title="€",
)

c1g, c2g = st.columns([1, 1])
with c1g:
    st.plotly_chart(pie_fig, use_container_width=True)
with c2g:
    st.plotly_chart(bar_fig, use_container_width=True)

with st.expander("Ver detalle de las primeras 12 cuotas"):
    st.dataframe(
        df.head(12).style.format(
            {"Cuota": eur, "Intereses": eur, "Amortización": eur, "Saldo final": eur}
        )
    )

st.caption("Notas: Este simulador no contempla comisiones, seguros ni variaciones de tipo de interés.")
render_footer()
