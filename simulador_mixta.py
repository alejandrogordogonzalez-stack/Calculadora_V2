# -*- coding: utf-8 -*-
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import inject_css, euro_input, eur, amortization_schedule, render_footer

inject_css()

st.title("🏠 Simulador de Hipoteca Mixta")
st.caption(
    "Introduce el importe, el plazo y el interés del periodo fijo. "
    "Añade el año de cambio y el tipo estimado del periodo variable (Euríbor + diferencial). "
    "El cálculo asume capitalización mensual (TIN anual / 12)."
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

with st.form("params_form_mixta", clear_on_submit=False):
    r1c1, r1c2, r1c3, r1c4 = st.columns([1.2, 1, 1, 1])
    with r1c1:
        principal = euro_input(
            "Importe a financiar (Cantidad solicitada) (€)",
            key="p_mix_eur",
            default=150000.0,
            decimals=2,
            min_value=1000.0
        )
    with r1c2:
        years = st.slider("Plazo total (años)", min_value=1, max_value=40, value=25, step=1, key="y_mix")
    with r1c3:
        annual_rate_pct_1 = st.number_input(
            "Interés aplicado periodo 1 (fijo) — % TIN anual",
            min_value=0.0, max_value=30.0, value=3.0, step=0.05, format="%.2f", key="r1_mix"
        )
    with r1c4:
        start_month = st.selectbox(
            "Mes de inicio (agrupación anual)",
            options=list(range(1, 13)), index=0, format_func=lambda m: f"{m:02d}", key="m_mix"
        )

    r2c1, r2c2, r2c3 = st.columns([1, 1, 1.2])
    with r2c1:
        change_year = st.slider(
            "Año en que cambia de fijo a variable",
            min_value=0, max_value=years, value=min(5, years), step=1, key="change_year_mix"
        )
    with r2c2:
        annual_rate_pct_2 = st.number_input(
            "Interés aplicado periodo 2 (variable estimado) — % TIN anual",
            min_value=0.0, max_value=30.0, value=4.0, step=0.05, format="%.2f", key="r2_mix"
        )
        st.caption("Periodo 2: **estimación de Euríbor + diferencial** (puedes ajustar el valor).")
    with r2c3:
        _ = st.form_submit_button("✅ Aplicar parámetros")

n_months = int(years * 12)
m1_months = int(change_year * 12)
m1_months = max(0, min(m1_months, n_months))
n2_months = int(max(n_months - m1_months, 0))

r1_monthly = (annual_rate_pct_1 / 100.0) / 12.0
r2_monthly = (annual_rate_pct_2 / 100.0) / 12.0

# --- Periodo 1 (fijo): cuota calculada sobre el plazo total ---
df_full_r1 = amortization_schedule(principal, r1_monthly, n_months)
if df_full_r1.empty:
    st.warning("Introduce un importe y un plazo válidos.")
    st.stop()

monthly_payment_p1 = float(df_full_r1["Cuota"].iloc[0])

if m1_months > 0:
    df_p1 = df_full_r1.head(m1_months).copy()
    interest_p1 = float(df_p1["Intereses"].sum())
    balance_after_p1 = float(df_p1["Saldo final"].iloc[-1])
else:
    # periodo 1 inexistente
    df_p1 = df_full_r1.iloc[0:0].copy()
    interest_p1 = 0.0
    balance_after_p1 = float(principal)

# --- Periodo 2 (variable): se recalcula cuota con saldo y plazo restante ---
if n2_months > 0:
    df_p2 = amortization_schedule(balance_after_p1, r2_monthly, n2_months).copy()
    if df_p2.empty:
        df_p2 = df_full_r1.iloc[0:0].copy()
        monthly_payment_p2 = 0.0
        interest_p2 = 0.0
    else:
        monthly_payment_p2 = float(df_p2["Cuota"].iloc[0])
        interest_p2 = float(df_p2["Intereses"].sum())
        # Ajusta el contador de mes para concatenar
        df_p2["Mes"] = df_p2["Mes"] + m1_months
else:
    df_p2 = df_full_r1.iloc[0:0].copy()
    monthly_payment_p2 = 0.0
    interest_p2 = 0.0

# --- Tabla final mixta ---
df_mix = pd.concat([df_p1, df_p2], ignore_index=True)

total_interest = float(interest_p1 + interest_p2)

# Métricas
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("💳 Cuota mensual periodo 1 (fijo)", eur(monthly_payment_p1) if m1_months > 0 else "—")
m2.metric("💳 Cuota mensual periodo 2 (variable)", eur(monthly_payment_p2) if n2_months > 0 else "—")
m3.metric("💡 Intereses periodo 1", eur(interest_p1))
m4.metric("💡 Intereses periodo 2", eur(interest_p2))
m5.metric("📌 Intereses totales", eur(total_interest))

st.caption(
    f"Periodo 1: **{m1_months}** meses · Periodo 2: **{n2_months}** meses · "
    f"Cambio en el mes **{m1_months}** (año {change_year})."
)

st.divider()

# Gráficas (igual estilo que la fija)
pie_fig = go.Figure(
    data=[go.Pie(labels=["Principal", "Intereses"], values=[principal, total_interest], hole=0.35)]
)
pie_fig.update_layout(
    title="Distribución total: principal vs intereses (mixta)",
    legend=dict(orientation="h", yanchor="bottom", y=-0.05, xanchor="center", x=0.5),
)

df_mix["Mes calendario"] = ((df_mix["Mes"] - 1 + (start_month - 1)) % 12) + 1
df_mix["Año"] = ((df_mix["Mes"] - 1 + (start_month - 1)) // 12) + 1
annual = df_mix.groupby("Año", as_index=False)[["Intereses", "Amortización"]].sum().round(2)

bar_fig = go.Figure()
bar_fig.add_trace(go.Bar(x=annual["Año"], y=annual["Intereses"], name="Intereses"))
bar_fig.add_trace(go.Bar(x=annual["Año"], y=annual["Amortización"], name="Amortización"))
bar_fig.update_layout(
    barmode="stack",
    title="Pago anual desglosado (apilado): amortización vs intereses (mixta)",
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
        df_mix.head(12).style.format(
            {"Cuota": eur, "Intereses": eur, "Amortización": eur, "Saldo final": eur}
        ),
        use_container_width=True
    )

with st.expander("Ver detalle alrededor del cambio (últimas 6 antes y primeras 6 después)"):
    if m1_months == 0:
        st.info("No hay periodo 1 (cambio en año 0).")
        st.dataframe(
            df_mix.head(12).style.format(
                {"Cuota": eur, "Intereses": eur, "Amortización": eur, "Saldo final": eur}
            ),
            use_container_width=True
        )
    elif n2_months == 0:
        st.info("No hay periodo 2 (cambio al final del plazo).")
        st.dataframe(
            df_mix.tail(12).style.format(
                {"Cuota": eur, "Intereses": eur, "Amortización": eur, "Saldo final": eur}
            ),
            use_container_width=True
        )
    else:
        i0 = max(m1_months - 6, 0)
        i1 = min(m1_months + 6, len(df_mix))
        st.dataframe(
            df_mix.iloc[i0:i1].style.format(
                {"Cuota": eur, "Intereses": eur, "Amortización": eur, "Saldo final": eur}
            ),
            use_container_width=True
        )

st.caption(
    "Notas: Este simulador no contempla comisiones, seguros ni variaciones del tipo real en el periodo variable. "
    "El tipo del periodo 2 es una estimación (Euríbor + diferencial) que puedes ajustar."
)

render_footer()
