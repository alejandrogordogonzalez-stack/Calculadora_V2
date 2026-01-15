# -*- coding: utf-8 -*-
import math
import numpy as np
import pandas as pd
import streamlit as st

from common import (
    inject_css, euro_input, eur, amortization_schedule, render_footer
)

inject_css()

st.title("🔁 Trae tu hipoteca fija")
st.caption("Compara tu hipoteca fija actual (lo que te queda por pagar) frente a una nueva oferta del banco.")

# -----------------------------
# Helpers (robusto a nombres de columnas)
# -----------------------------
def _pick_col(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    cols = list(df.columns)
    for cand in candidates:
        cl = str(cand).lower()
        for c in cols:
            if cl in str(c).lower():
                return c
    return None

def safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default

# -----------------------------
# 1) Hipoteca actual
# -----------------------------
st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">1) Tu hipoteca fija actual</span>
      <span class="param-subtle">Introduce los datos originales y cuántos meses llevas pagando.</span>
    </div>
    """,
    unsafe_allow_html=True
)

with st.form("form_old_fixed", clear_on_submit=False):
    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
    with c1:
        P_old = euro_input(
            "Importe inicial financiado (€)",
            key="ttf_p_old_eur",
            default=200000.0,
            decimals=2,
            min_value=1000.0
        )
    with c2:
        Y_old = st.slider("Plazo original (años)", 1, 40, 30, 1, key="ttf_y_old")
    with c3:
        R_old = st.number_input(
            "Tipo fijo actual (% TIN anual)",
            min_value=0.0, max_value=30.0, value=3.00, step=0.05, format="%.2f", key="ttf_r_old"
        )
    with c4:
        n_old_tmp = safe_int(Y_old) * 12
        months_paid_in = st.number_input(
            "Meses ya pagados",
            min_value=0,
            max_value=max(n_old_tmp, 0),
            value=min(safe_int(st.session_state.get("ttf_months_paid", 0)), max(n_old_tmp, 0)),
            step=1,
            key="ttf_months_paid",
            help="Ojo: al estar en un formulario, este valor solo se aplica al pulsar 'Calcular hipoteca actual'."
        )

    submitted_old = st.form_submit_button("✅ Calcular hipoteca actual")

n_old = safe_int(Y_old) * 12
months_paid = min(max(safe_int(months_paid_in), 0), n_old)
meses_restantes_old = max(n_old - months_paid, 0)

if P_old <= 0 or n_old <= 0:
    st.warning("Introduce un importe y plazo válidos.")
    st.stop()

r_old_m = (R_old / 100.0) / 12.0
df_old = amortization_schedule(P_old, r_old_m, n_old)

col_cuota = _pick_col(df_old, ["Cuota", "cuota", "Payment"])
col_int   = _pick_col(df_old, ["Interés", "Interes", "Interest"])
col_saldo = _pick_col(df_old, ["Saldo", "saldo", "Balance", "Outstanding"])

if col_cuota is None or col_int is None:
    st.error("Tu amortization_schedule no devuelve columnas esperadas (Cuota/Interés). Revisa common.py.")
    st.stop()

cuota_old = float(df_old[col_cuota].iloc[0]) if len(df_old) else 0.0
interes_total_old = float(df_old[col_int].sum()) if len(df_old) else 0.0

# Saldo pendiente (después de 'months_paid' pagos)
if months_paid == 0:
    saldo_pendiente_old = float(P_old)
elif col_saldo is None:
    saldo_pendiente_old = np.nan
else:
    # months_paid=1 -> fila 0 (tras el primer pago)
    idx = min(months_paid - 1, len(df_old) - 1)
    saldo_pendiente_old = float(df_old[col_saldo].iloc[idx])

# Interés restante desde hoy
if months_paid >= n_old:
    interes_restante_old = 0.0
else:
    interes_restante_old = float(df_old[col_int].iloc[months_paid:].sum())

# Métricas hipoteca actual (incluyo meses pagados usados para que se vea claro)
mA, mB, mC, mD, mE = st.columns(5)
mA.metric("💳 Cuota mensual actual", eur(cuota_old))
mB.metric("🧾 Intereses restantes", eur(interes_restante_old))
mC.metric("⏱️ Meses restantes", f"{meses_restantes_old}")
mD.metric("✅ Meses pagados (usados)", f"{months_paid}")
mE.metric("🏠 Saldo pendiente", "—" if (isinstance(saldo_pendiente_old, float) and np.isnan(saldo_pendiente_old)) else eur(saldo_pendiente_old))

with st.expander("Ver resumen de tu hipoteca actual (detalle)"):
    old_summary = pd.DataFrame({
        "Concepto": [
            "Importe inicial financiado",
            "Plazo original (meses)",
            "Meses ya pagados",
            "Meses restantes",
            "Cuota mensual",
            "Intereses totales (desde el inicio)",
            "Intereses restantes (desde hoy)",
            "Saldo pendiente (aprox.)"
        ],
        "Valor": [
            P_old,
            n_old,
            months_paid,
            meses_restantes_old,
            cuota_old,
            interes_total_old,
            interes_restante_old,
            saldo_pendiente_old if not (isinstance(saldo_pendiente_old, float) and np.isnan(saldo_pendiente_old)) else np.nan
        ]
    })
    st.dataframe(
        old_summary.style.format({"Valor": lambda x: "—" if (isinstance(x, float) and np.isnan(x)) else eur(x)}),
        use_container_width=True
    )

st.divider()

# -----------------------------
# 2) Nueva oferta del banco
# -----------------------------
st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">2) Oferta nueva del banco</span>
      <span class="param-subtle">Introduce la oferta y calculamos cuota e intereses totales.</span>
    </div>
    """,
    unsafe_allow_html=True
)

def _autofill_new_offer():
    # Rellena importe con saldo pendiente (si lo tenemos) y plazo sugerido con los meses restantes
    if not (isinstance(saldo_pendiente_old, float) and np.isnan(saldo_pendiente_old)):
        st.session_state["ttf_p_new_eur"] = float(saldo_pendiente_old)
    # plazo sugerido: lo que queda, redondeado hacia arriba a años
    suggested_years = max(1, int(math.ceil(meses_restantes_old / 12))) if meses_restantes_old > 0 else 1
    st.session_state["ttf_y_new"] = suggested_years

cbtn1, cbtn2 = st.columns([1, 3])
with cbtn1:
    st.button(
        "✨ Autocompletar con saldo pendiente",
        use_container_width=True,
        on_click=_autofill_new_offer
    )
with cbtn2:
    if isinstance(saldo_pendiente_old, float) and np.isnan(saldo_pendiente_old):
        st.info("No puedo autocompletar el saldo pendiente porque tu amortization_schedule no devuelve la columna de saldo. (Aun así puedes introducir el importe manualmente).")

with st.form("form_new_offer", clear_on_submit=False):
    c1n, c2n, c3n = st.columns([1.2, 1, 1])
    with c1n:
        P_new = euro_input(
            "Importe a financiar en la nueva hipoteca (€)",
            key="ttf_p_new_eur",
            default=float(saldo_pendiente_old) if not (isinstance(saldo_pendiente_old, float) and np.isnan(saldo_pendiente_old)) else 150000.0,
            decimals=2,
            min_value=1000.0
        )
    with c2n:
        Y_new = st.slider(
            "Plazo de la nueva hipoteca (años)",
            min_value=1, max_value=40,
            value=max(1, int(math.ceil(meses_restantes_old / 12))) if meses_restantes_old > 0 else 20,
            step=1,
            key="ttf_y_new"
        )
    with c3n:
        R_new = st.number_input(
            "Tipo fijo de la oferta (% TIN anual)",
            min_value=0.0, max_value=30.0, value=2.50, step=0.05, format="%.2f", key="ttf_r_new"
        )

    submitted_new = st.form_submit_button("🧮 Calcular nueva oferta")

n_new = safe_int(Y_new) * 12
r_new_m = (R_new / 100.0) / 12.0

df_new = amortization_schedule(P_new, r_new_m, n_new)
col_cuota_n = _pick_col(df_new, ["Cuota", "cuota", "Payment"])
col_int_n   = _pick_col(df_new, ["Interés", "Interes", "Interest"])

if col_cuota_n is None or col_int_n is None:
    st.error("Tu amortization_schedule no devuelve columnas esperadas (Cuota/Interés) para la nueva oferta.")
    st.stop()

cuota_new = float(df_new[col_cuota_n].iloc[0]) if len(df_new) else 0.0
interes_total_new = float(df_new[col_int_n].sum()) if len(df_new) else 0.0

m1, m2, m3 = st.columns(3)
m1.metric("💳 Cuota mensual nueva", eur(cuota_new))
m2.metric("🧾 Intereses totales nueva", eur(interes_total_new))
m3.metric("⏱️ Meses totales nueva", f"{n_new}")

st.divider()

# -----------------------------
# 3) Comparación visual
# -----------------------------
st.markdown("## 🔥 Comparación rápida")

ref_interest = interes_restante_old
diff_interest = interes_total_new - ref_interest
diff_cuota = cuota_new - cuota_old

if ref_interest <= 0:
    st.info("Tu hipoteca actual no tiene intereses restantes (o está finalizada). La comparación principal se centra en la nueva oferta.")
else:
    ahorro = ref_interest - interes_total_new  # + => ahorro
    ratio = 0.0 if ref_interest == 0 else max(0.0, min(1.0, ahorro / ref_interest))

    if ahorro >= 0:
        st.markdown(
            f"""
            <div class="soft-box" style="padding:18px;border-radius:18px;">
              <div class="value-title">✅ Ahorro estimado en intereses (nueva vs lo que te queda)</div>
              <div class="value-big">{eur(ahorro)}</div>
              <div class="param-subtle">Comparo <b>intereses restantes</b> de tu hipoteca actual con <b>intereses totales</b> de la nueva oferta.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="soft-box" style="padding:18px;border-radius:18px;">
              <div class="value-title">⚠️ Sobrecoste estimado en intereses (nueva vs lo que te queda)</div>
              <div class="value-big">{eur(abs(ahorro))}</div>
              <div class="param-subtle">La nueva oferta implica más intereses que los que te quedan en tu hipoteca actual.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.progress(ratio)

cX, cY, cZ, cW = st.columns(4)
cX.metric("Intereses restantes (actual)", eur(ref_interest))
cY.metric("Intereses totales (nueva)", eur(interes_total_new), delta=eur(diff_interest))
cZ.metric("Cuota mensual (actual)", eur(cuota_old))
cW.metric("Cuota mensual (nueva)", eur(cuota_new), delta=eur(diff_cuota))

cmp_df = pd.DataFrame({
    "Concepto": ["Cuota mensual", "Intereses (referencia)", "Meses", "Importe financiado"],
    "Hipoteca actual (desde hoy)": [
        cuota_old,
        ref_interest,
        meses_restantes_old,
        saldo_pendiente_old if not (isinstance(saldo_pendiente_old, float) and np.isnan(saldo_pendiente_old)) else np.nan
    ],
    "Nueva oferta": [cuota_new, interes_total_new, n_new, P_new],
    "Diferencia (nueva - actual)": [
        cuota_new - cuota_old,
        interes_total_new - ref_interest,
        n_new - meses_restantes_old,
        P_new - (saldo_pendiente_old if not (isinstance(saldo_pendiente_old, float) and np.isnan(saldo_pendiente_old)) else np.nan)
    ]
})

st.dataframe(
    cmp_df.style.format({
        "Hipoteca actual (desde hoy)": lambda x: "—" if (isinstance(x, float) and np.isnan(x)) else (eur(x) if isinstance(x, (int, float, np.number)) else x),
        "Nueva oferta": lambda x: "—" if (isinstance(x, float) and np.isnan(x)) else (eur(x) if isinstance(x, (int, float, np.number)) else x),
        "Diferencia (nueva - actual)": lambda x: "—" if (isinstance(x, float) and np.isnan(x)) else (eur(x) if isinstance(x, (int, float, np.number)) else x),
    }),
    use_container_width=True
)

st.caption("Nota: al estar los inputs dentro de formularios, los cambios se aplican al pulsar cada botón de cálculo.")
render_footer()
