# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import streamlit as st

from common import inject_css, euro_input, eur, fmt_number_es, amortization_schedule, render_footer

inject_css()

st.title("💹 Analiza Inversión")

# ============================
# ✅ TIR (como Excel) — IRR anual con flujos [-aportación, cashflow...]
# ============================
def tir_excel(cashflows, tol=1e-10, max_iter=200):
    """
    TIR anual estilo Excel (IRR):
    - cashflows[0] suele ser la inversión inicial (negativa)
    - cashflows[1:] los flujos posteriores (anuales)
    Devuelve la tasa r tal que NPV(r)=0.
    Si no existe (p.ej. no hay cambio de signo), devuelve np.nan.
    """
    cfs = [float(x) for x in cashflows if x is not None]

    # Excel devuelve error si no hay cambio de signo (no hay TIR)
    if not (any(x < 0 for x in cfs) and any(x > 0 for x in cfs)):
        return np.nan

    def npv(r):
        return sum(cf / ((1.0 + r) ** i) for i, cf in enumerate(cfs))

    # Búsqueda por bisección (robusta)
    lo = -0.999999  # cercano a -100% (sin llegar)
    hi = 0.10       # 10% inicial
    f_lo = npv(lo)
    f_hi = npv(hi)

    # Expandimos hi hasta encontrar cambio de signo o límite
    attempts = 0
    while f_lo * f_hi > 0 and attempts < 60:
        hi = hi * 2 + 0.05
        f_hi = npv(hi)
        attempts += 1

    if f_lo * f_hi > 0:
        return np.nan

    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        f_mid = npv(mid)
        if abs(f_mid) < tol:
            return mid
        if f_lo * f_mid <= 0:
            hi = mid
        else:
            lo = mid
            f_lo = f_mid

    return (lo + hi) / 2.0


st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">Hipoteca de la Inversión</span>
      <span class="param-subtle">Configura el precio, financiación y condiciones para ver tu cuota mensual.</span>
    </div>
    """,
    unsafe_allow_html=True
)

with st.form("params_form_inversion", clear_on_submit=False):
    c1, c2 = st.columns([1.2, 1])
    with c1:
        precio_vivienda = euro_input(
            "Precio de la vivienda (€)",
            key="precio_inv_eur",
            default=200000.0,
            decimals=2,
            min_value=10000.0
        )
    with c2:
        pct_financiacion = st.slider(
            "Porcentaje de financiación (%)",
            min_value=0, max_value=100, value=90, step=5, key="pct_finan_inv"
        )

    c3, c4 = st.columns([1, 1])
    with c3:
        plazo_inv = st.slider(
            "Plazo de la hipoteca (años)",
            min_value=1, max_value=40, value=30, step=1, key="plazo_inv"
        )
    with c4:
        interes_inv = st.number_input(
            "Interés aplicado (% TIN anual)",
            min_value=0.0, max_value=30.0, value=2.7, step=0.05, format="%.2f", key="interes_inv"
        )
    _ = st.form_submit_button("✅ Calcular cuota")

importe_financiado = precio_vivienda * pct_financiacion / 100
n_meses_inv = plazo_inv * 12
r_mensual_inv = (interes_inv / 100.0) / 12.0
df_inv = amortization_schedule(importe_financiado, r_mensual_inv, n_meses_inv)

cuota_mensual_inv = 0.0
if not df_inv.empty:
    cuota_mensual_inv = float(df_inv["Cuota"].iloc[0])

    st.markdown(
        f"""
        <div style="
            background:#e8f0fe;
            border:1px solid #4A90E2;
            border-radius:12px;
            padding:1rem 1.25rem;
            margin:.5rem 0 1rem 0;
        ">
          <div class="value-title">💳 Cuota mensual hipoteca</div>
          <div class="value-big">{eur(cuota_mensual_inv)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">Aportación Inicial</span>
      <span class="param-subtle">Entrada + impuestos + gastos fijos + comisión de apertura (+ extra opcional).</span>
    </div>
    """,
    unsafe_allow_html=True
)

comunidades = {
    "IVA (Vivienda nueva)": (0.10, 0.012),
    "Andalucía": (0.07, 0.015),
    "Aragón": (0.085, 0.012),
    "Asturias": (0.08, 0.015),
    "Baleares": (0.08, 0.0075),
    "Canarias": (0.065, 0.015),
    "Cantabria": (0.08, 0.015),
    "Castilla León": (0.08, 0.015),
    "Castilla la Mancha": (0.09, 0.015),
    "Cataluña": (0.10, 0.015),
    "Comunidad Valenciana": (0.10, 0.015),
    "Extremadura": (0.08, 0.015),
    "Galicia": (0.10, 0.015),
    "Comunidad de Madrid": (0.06, 0.0075),
    "Murcia": (0.08, 0.015),
    "Navarra": (0.06, 0.005),
    "País Vasco": (0.07, 0.005),
    "La Rioja": (0.07, 0.01)
}

comunidad = st.selectbox("Comunidad Autónoma", list(comunidades.keys()), key="comunidad_inv")
itp, ajd = comunidades[comunidad]

entrada_pct = 100 - pct_financiacion
entrada_eur = precio_vivienda * entrada_pct / 100
impuestos = precio_vivienda * (itp + ajd)

def _fmt_pct(x: float) -> str:
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")

itp_text = _fmt_pct(itp * 100)
ajd_text = _fmt_pct(ajd * 100)

registro_notaria = 1500.0
tasacion = 400.0
gestoria = 400.0
comision_apertura = importe_financiado * 0.02

aportacion_extra = euro_input(
    "Aportación extra (reforma / otro concepto) (€)",
    key="aport_extra_eur",
    default=0.0,
    decimals=2,
    min_value=0.0
)

gastos_fijos = registro_notaria + tasacion + gestoria
aportacion_total = entrada_eur + impuestos + gastos_fijos + comision_apertura + aportacion_extra

cA, cB, cC = st.columns(3)
cA.metric("💰 Entrada", f"{fmt_number_es(entrada_pct, 1)}% = {eur(entrada_eur)}")

with cB:
    st.markdown(
        f"""
        <div class='value-title'>
            📑 Impuestos (ITP/IVA + AJD)
            <span style="font-size:0.85em;color:#5f6570;margin-left:.35rem">
                ITP/IVA {itp_text}% + AJD {ajd_text}%
            </span>
        </div>
        <div class='value-big'>{eur(impuestos)}</div>
        """,
        unsafe_allow_html=True
    )

cC.metric("🧾 Gastos fijos (Reg.+Not.+Tas.+Gest.)", eur(gastos_fijos))
st.metric("💸 Comisión de apertura (2%)", eur(comision_apertura))

st.markdown(
    f"""
    <div style="
        background:#e8f0fe;
        border:1px solid #4A90E2;
        border-radius:12px;
        padding:1rem 1.25rem;
        margin:.5rem 0 1rem 0;
    ">
      <div class="value-title">📊 Aportación inicial total</div>
      <div class="value-big">{eur(aportacion_total)}</div>
    </div>
    """,
    unsafe_allow_html=True
)

resumen_df = pd.DataFrame({
    "Concepto": [
        "Entrada (no financiado)",
        "Impuestos (ITP/IVA + AJD)",
        "Registro y Notaría",
        "Tasación inmueble",
        "Gestoría",
        "Comisión apertura (2%)",
        "Aportación extra (reforma / otros)",
        "TOTAL APORTACIÓN INICIAL"
    ],
    "Importe": [
        entrada_eur,
        impuestos,
        registro_notaria,
        tasacion,
        gestoria,
        comision_apertura,
        aportacion_extra,
        aportacion_total
    ]
})

with st.expander("📘 Resumen — Aportación Inicial", expanded=False):
    st.dataframe(resumen_df.style.format({"Importe": eur}), use_container_width=True)

st.caption(
    "Nota: Gastos fijos asumidos: Registro y Notaría = 1.500 €, Tasación = 400 €, Gestoría = 400 €. "
    "La comisión de apertura es el 2% del importe financiado."
)

st.divider()

st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">Ingresos de Alquiler</span>
      <span class="param-subtle">Define ingresos y gastos para calcular el cashflow anual.</span>
    </div>
    """,
    unsafe_allow_html=True
)

with st.form("params_form_alquiler", clear_on_submit=False):
    c1, c2 = st.columns([1, 1])
    with c1:
        alquiler_mensual = euro_input("Alquiler mensual estimado (€)", key="alq_mensual_eur", default=1000.0, decimals=2, min_value=0.0)
        comunidad_mensual = euro_input("Comunidad (mensual) (€)", key="comunidad_mensual_eur", default=40.0, decimals=2, min_value=0.0)
        seguros_mensual = euro_input("Seguros (mensual) (€)", key="seguros_mensual_eur", default=60.0, decimals=2, min_value=0.0)
    with c2:
        ibi_anual = euro_input("IBI (anual) (€)", key="ibi_anual_eur", default=150.0, decimals=2, min_value=0.0)
        mantenimiento_anual = euro_input("Mantenimiento (anual) (€)", key="mnt_anual_eur", default=0.0, decimals=2, min_value=0.0)
    _ = st.form_submit_button("✅ Calcular cashflow")

ingresos_anuales = alquiler_mensual * 12
hipoteca_anual = float(cuota_mensual_inv) * 12
otros_gastos_anuales = ibi_anual + comunidad_mensual * 12 + mantenimiento_anual + seguros_mensual * 12
gastos_anuales_totales = otros_gastos_anuales + hipoteca_anual
cashflow_anual = ingresos_anuales - gastos_anuales_totales

cA, cB, cC = st.columns(3)
cA.metric("📈 Ingresos anuales por alquiler", eur(ingresos_anuales))
cB.metric("🏦 Gastos de hipoteca anuales", eur(hipoteca_anual))
cC.metric("📉 Otros gastos anuales (IBI + comunidad + mantenimiento + seguros)", eur(otros_gastos_anuales))

st.markdown(
    f"""
    <div style="
        background:#e8f0fe;
        border:1px solid #4A90E2;
        border-radius:12px;
        padding:1rem 1.25rem;
        margin:.5rem 0 1rem 0;
    ">
      <div class="value-title">💧 Cashflow anual</div>
      <div class="value-big">{eur(cashflow_anual)}</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption("El cashflow anual mostrado **incluye** hipoteca. No incluye vacancias, IRPF ni otros posibles ajustes.")

st.divider()

# ==========================
# Rentabilidad
# ==========================
st.markdown("<h2 style='margin:0 0 .5rem 0'>📈 Rentabilidad</h2>", unsafe_allow_html=True)
st.markdown(
    """
    <div class="param-subtle" style="margin-bottom:.5rem">
      Ratios clave de la inversión. Valores destacados en verde y una breve descripción bajo cada uno.
    </div>
    """,
    unsafe_allow_html=True
)

horizonte_anios = st.number_input(
    "Horizonte (años) para comparar el interés compuesto / TIR",
    min_value=1, max_value=40, value=int(plazo_inv), step=1, key="horizonte_comp"
)

r_simple = 0.0 if (aportacion_total <= 0) else (cashflow_anual / aportacion_total)
r_comp = ((1 + horizonte_anios * r_simple) ** (1 / horizonte_anios)) - 1

def fmt_pct(x: float) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{fmt_number_es(x * 100, 2)} %"

# --- TIR anual (como Excel) ---
n_h = int(horizonte_anios)
tir = np.nan
if aportacion_total > 0:
    tir = tir_excel([-float(aportacion_total)] + [float(cashflow_anual)] * n_h)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        f"""
        <div style="
            background:#e8f5e9;
            border:1px solid #4caf50;
            border-radius:12px;
            padding:1rem 1.25rem;
            margin:.5rem 0 1rem 0;
        ">
          <div class="value-title">💶 Rentabilidad sobre aportación (Cash-on-Cash)</div>
          <div class="value-big">{fmt_pct(r_simple)}</div>
          <div style="font-size:0.9em;color:#5f6570;margin-top:.35rem">
            <em>Cashflow anual / Aportación inicial</em>. También llamado <strong>Cash-on-Cash Return (CoC)</strong>.
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f"""
        <div style="
            background:#e8f5e9;
            border:1px solid #4caf50;
            border-radius:12px;
            padding:1rem 1.25rem;
            margin:.5rem 0 1rem 0;
        ">
          <div class="value-title">📈 Interés compuesto equivalente</div>
          <div class="value-big">{fmt_pct(r_comp)}</div>
          <div style="font-size:0.9em;color:#5f6570;margin-top:.35rem">
            Tasa anual constante que, durante {int(horizonte_anios)} año(s), genera el mismo beneficio que una
            rentabilidad simple de {fmt_pct(r_simple)}. (Fórmula: <em>((1 + n·r)<sup>1/n</sup> − 1)</em>).<br/>
            También conocida como <strong>Tasa Anual Equivalente (TAE) de la inversión</strong>.
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f"""
        <div style="
            background:#e8f5e9;
            border:1px solid #4caf50;
            border-radius:12px;
            padding:1rem 1.25rem;
            margin:.5rem 0 1rem 0;
        ">
          <div class="value-title">📌 TIR (como Excel)</div>
          <div class="value-big">{fmt_pct(tir)}</div>
          <div style="font-size:0.9em;color:#5f6570;margin-top:.35rem">
            Calculada como <strong>TIR/IRR</strong> con flujos anuales:
            <em>[-aportación inicial, cashflow, cashflow, ...]</em> durante {int(horizonte_anios)} año(s).
            Si no hay cambio de signo (p.ej. cashflow negativo), la TIR no está definida.
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==========================
# Tabla comparativa por año
# ==========================
years_list = list(range(1, n_h + 1))

def comp_equiv(r: float, n: int) -> float:
    base = 1 + n * r
    return (base ** (1 / n) - 1) if base > 0 else np.nan

tir_por_anio = []
if aportacion_total > 0:
    for n in years_list:
        tir_por_anio.append(tir_excel([-float(aportacion_total)] + [float(cashflow_anual)] * n))
else:
    tir_por_anio = [np.nan] * n_h

df_ratios = pd.DataFrame({
    "Año": years_list,
    "Rentabilidad sobre aportación (Cash-on-Cash)": [r_simple] * n_h,
    "Interés compuesto equivalente": [comp_equiv(r_simple, n) for n in years_list],
    "TIR (como Excel)": tir_por_anio
})

df_display = df_ratios.copy()
df_display["Rentabilidad sobre aportación (Cash-on-Cash)"] = df_display["Rentabilidad sobre aportación (Cash-on-Cash)"].map(fmt_pct)
df_display["Interés compuesto equivalente"] = df_display["Interés compuesto equivalente"].map(fmt_pct)
df_display["TIR (como Excel)"] = df_display["TIR (como Excel)"].map(fmt_pct)

with st.expander("🔍 Comparativa por año (CoC vs compuesto vs TIR)", expanded=False):
    st.dataframe(df_display, use_container_width=True, hide_index=True)

render_footer()
