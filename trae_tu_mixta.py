# trae_tu_mixta.py
# -*- coding: utf-8 -*-
import math
import numpy as np
import pandas as pd
import streamlit as st

from common import (
    inject_css, euro_input, eur, amortization_schedule, render_footer
)

inject_css()

st.title("🔁 Trae tu hipoteca mixta")
st.caption(
    "Compara tu hipoteca mixta actual (lo que te queda por pagar) frente a una nueva oferta mixta del banco. "
    "En el periodo variable asumimos un Euríbor constante para todo el periodo (estimación)."
)

# -----------------------------
# Helpers
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

def _is_nan(x):
    return isinstance(x, float) and np.isnan(x)

def _ensure_text_state(key: str):
    """euro_input usa st.text_input -> el estado debe ser string; si hay float/int, convertir."""
    if key in st.session_state:
        v = st.session_state[key]
        if isinstance(v, (int, float, np.floating, np.integer)):
            st.session_state[key] = f"{float(v):.2f}"

def build_mixed_schedule(
    principal: float,
    n_months: int,
    m1_months: int,
    r1_monthly: float,
    r2_monthly: float
):
    """
    Construye el cuadro de amortización de una mixta como en tu ejemplo:
    - Periodo 1: cuota calculada a tipo r1 sobre el plazo total (n_months), se toman m1_months filas.
    - Periodo 2: se recalcula cuota con saldo al final del periodo 1 y plazo restante (n2).
    Devuelve df_mix (con columnas estandarizadas), y métricas.
    """
    if principal <= 0 or n_months <= 0:
        return pd.DataFrame(), 0.0, 0.0, 0.0, 0.0, np.nan

    m1_months = int(max(0, min(m1_months, n_months)))
    n2_months = int(max(n_months - m1_months, 0))

    df_full_r1 = amortization_schedule(principal, r1_monthly, n_months).copy()
    if df_full_r1.empty:
        return pd.DataFrame(), 0.0, 0.0, 0.0, 0.0, np.nan

    col_cuota = _pick_col(df_full_r1, ["Cuota", "cuota", "Payment"])
    col_int   = _pick_col(df_full_r1, ["Intereses", "Interés", "Interes", "Interest"])
    col_amort = _pick_col(df_full_r1, ["Amortización", "Amortizacion", "Amortization", "Principal", "Capital"])
    col_saldo = _pick_col(df_full_r1, ["Saldo final", "Saldo", "saldo", "Balance", "Outstanding", "Remaining"])
    col_mes   = _pick_col(df_full_r1, ["Mes", "mes", "Month"])

    if col_cuota is None or col_int is None:
        return pd.DataFrame(), 0.0, 0.0, 0.0, 0.0, np.nan

    # Normaliza df_full_r1
    df1 = df_full_r1.copy()
    if col_mes is None:
        df1["Mes"] = np.arange(1, len(df1) + 1)
        col_mes = "Mes"

    df1_std = pd.DataFrame({
        "Mes": df1[col_mes].astype(int),
        "Cuota": df1[col_cuota].astype(float),
        "Intereses": df1[col_int].astype(float),
    })
    if col_amort is not None:
        df1_std["Amortización"] = df1[col_amort].astype(float)
    else:
        df1_std["Amortización"] = np.nan
    if col_saldo is not None:
        df1_std["Saldo final"] = df1[col_saldo].astype(float)
    else:
        df1_std["Saldo final"] = np.nan

    monthly_payment_p1 = float(df1_std["Cuota"].iloc[0])

    # Periodo 1 recortado
    if m1_months > 0:
        df_p1 = df1_std.head(m1_months).copy()
        df_p1["Periodo"] = 1
        interest_p1 = float(df_p1["Intereses"].sum())
        balance_after_p1 = float(df_p1["Saldo final"].iloc[-1]) if not _is_nan(float(df_p1["Saldo final"].iloc[-1])) else np.nan
    else:
        df_p1 = df1_std.iloc[0:0].copy()
        df_p1["Periodo"] = 1
        interest_p1 = 0.0
        balance_after_p1 = float(principal)

    # Periodo 2
    monthly_payment_p2 = 0.0
    interest_p2 = 0.0
    if n2_months > 0:
        if _is_nan(balance_after_p1):
            df_p2 = df1_std.iloc[0:0].copy()
            df_p2["Periodo"] = 2
        else:
            df2_raw = amortization_schedule(balance_after_p1, r2_monthly, n2_months).copy()
            if df2_raw.empty:
                df_p2 = df1_std.iloc[0:0].copy()
                df_p2["Periodo"] = 2
            else:
                col_cuota2 = _pick_col(df2_raw, ["Cuota", "cuota", "Payment"])
                col_int2   = _pick_col(df2_raw, ["Intereses", "Interés", "Interes", "Interest"])
                col_amort2 = _pick_col(df2_raw, ["Amortización", "Amortizacion", "Amortization", "Principal", "Capital"])
                col_saldo2 = _pick_col(df2_raw, ["Saldo final", "Saldo", "saldo", "Balance", "Outstanding", "Remaining"])
                col_mes2   = _pick_col(df2_raw, ["Mes", "mes", "Month"])

                if col_mes2 is None:
                    df2_raw["Mes"] = np.arange(1, len(df2_raw) + 1)
                    col_mes2 = "Mes"

                if col_cuota2 is None or col_int2 is None:
                    df_p2 = df1_std.iloc[0:0].copy()
                    df_p2["Periodo"] = 2
                else:
                    df2_std = pd.DataFrame({
                        "Mes": df2_raw[col_mes2].astype(int) + m1_months,
                        "Cuota": df2_raw[col_cuota2].astype(float),
                        "Intereses": df2_raw[col_int2].astype(float),
                    })
                    df2_std["Amortización"] = df2_raw[col_amort2].astype(float) if col_amort2 is not None else np.nan
                    df2_std["Saldo final"] = df2_raw[col_saldo2].astype(float) if col_saldo2 is not None else np.nan
                    df2_std["Periodo"] = 2

                    monthly_payment_p2 = float(df2_std["Cuota"].iloc[0])
                    interest_p2 = float(df2_std["Intereses"].sum())

                    df_p2 = df2_std.copy()
    else:
        df_p2 = df1_std.iloc[0:0].copy()
        df_p2["Periodo"] = 2

    df_mix = pd.concat([df_p1, df_p2], ignore_index=True)
    return df_mix, monthly_payment_p1, monthly_payment_p2, interest_p1, interest_p2, balance_after_p1


# ============================================================
# 1) Tu hipoteca mixta actual
# ============================================================
st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">1) Tu hipoteca mixta actual</span>
      <span class="param-subtle">Introduce condiciones y meses ya pagados para estimar lo que te queda.</span>
    </div>
    """,
    unsafe_allow_html=True
)

_ensure_text_state("ttm_p_old_eur")

with st.form("form_old_mixed", clear_on_submit=False):
    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
    with c1:
        P_old = euro_input(
            "Importe inicial financiado (€)",
            key="ttm_p_old_eur",
            default=200000.0,
            decimals=2,
            min_value=1000.0
        )
    with c2:
        Y_old = st.slider("Plazo total (años)", 1, 40, 30, 1, key="ttm_y_old")
    with c3:
        change_year_old = st.slider(
            "Año en que pasa a variable",
            min_value=0, max_value=Y_old, value=min(5, Y_old), step=1, key="ttm_change_year_old"
        )
    with c4:
        n_old_tmp = safe_int(Y_old) * 12
        months_paid_in = st.number_input(
            "Meses ya pagados",
            min_value=0,
            max_value=max(n_old_tmp, 0),
            value=min(safe_int(st.session_state.get("ttm_months_paid", 0)), max(n_old_tmp, 0)),
            step=1,
            key="ttm_months_paid",
            help="Al estar en formulario, se aplica al pulsar el botón."
        )

    d1, d2, d3 = st.columns([1, 1, 1])
    with d1:
        r1_old = st.number_input(
            "Interés periodo 1 (fijo) — % TIN anual",
            min_value=0.0, max_value=30.0, value=3.00, step=0.05, format="%.2f", key="ttm_r1_old"
        )
    with d2:
        diff_old = st.number_input(
            "Diferencial periodo variable — (% puntos)",
            min_value=-2.0, max_value=10.0, value=1.00, step=0.05, format="%.2f", key="ttm_diff_old"
        )
    with d3:
        euribor_old = st.number_input(
            "Euríbor estimado (%)",
            min_value=-2.0, max_value=10.0, value=3.00, step=0.05, format="%.2f", key="ttm_euribor_old"
        )
        st.caption("(**Estimación constante** de Euríbor para todo el periodo variable)")

    _ = st.form_submit_button("✅ Calcular hipoteca actual")

n_old = safe_int(Y_old) * 12
m1_old = safe_int(change_year_old) * 12
m1_old = max(0, min(m1_old, n_old))
months_paid = min(max(safe_int(months_paid_in), 0), n_old)

r1_old_m = (r1_old / 100.0) / 12.0
r2_old_pct = euribor_old + diff_old
r2_old_m = (r2_old_pct / 100.0) / 12.0

if P_old <= 0 or n_old <= 0:
    st.warning("Introduce un importe y plazo válidos.")
    st.stop()

df_old, cuota_p1_old, cuota_p2_old, ip1_old, ip2_old, balance_after_p1_old = build_mixed_schedule(
    P_old, n_old, m1_old, r1_old_m, r2_old_m
)

if df_old.empty:
    st.error("No se pudo construir el cuadro de amortización (revisa amortization_schedule/common.py).")
    st.stop()

meses_restantes_old = max(n_old - months_paid, 0)

# Saldo pendiente ahora
if months_paid == 0:
    saldo_pendiente_old = float(P_old)
else:
    idx = min(months_paid - 1, len(df_old) - 1)
    saldo_pendiente_old = float(df_old["Saldo final"].iloc[idx]) if not _is_nan(float(df_old["Saldo final"].iloc[idx])) else np.nan

# Interés restante desde hoy
if months_paid >= n_old:
    interes_restante_old = 0.0
else:
    interes_restante_old = float(df_old["Intereses"].iloc[months_paid:].sum())

# Cuota "actual" según periodo donde estés
if months_paid < m1_old and m1_old > 0:
    cuota_actual_old = cuota_p1_old
    periodo_actual = "Periodo 1 (fijo)"
else:
    cuota_actual_old = cuota_p2_old if (n_old - m1_old) > 0 else cuota_p1_old
    periodo_actual = "Periodo 2 (variable)" if (n_old - m1_old) > 0 else "Periodo 1 (fijo)"

# Métricas
mA, mB, mC, mD, mE, mF = st.columns(6)
mA.metric("💳 Cuota actual (según periodo)", eur(cuota_actual_old))
mB.metric("🏷️ Periodo actual", periodo_actual)
mC.metric("🧾 Intereses restantes (desde hoy)", eur(interes_restante_old))
mD.metric("⏱️ Meses restantes", f"{meses_restantes_old}")
mE.metric("✅ Meses pagados (usados)", f"{months_paid}")
mF.metric("🏠 Saldo pendiente", "—" if _is_nan(saldo_pendiente_old) else eur(saldo_pendiente_old))

st.caption(
    f"Periodo 1: {m1_old} meses a {r1_old:.2f}% · "
    f"Periodo 2: {max(n_old-m1_old,0)} meses a (Euríbor {euribor_old:.2f}% + dif {diff_old:.2f}%) = {r2_old_pct:.2f}% (estimado)."
)

with st.expander("Ver resumen de tu hipoteca actual (detalle)"):
    old_summary = pd.DataFrame({
        "Concepto": [
            "Importe inicial financiado",
            "Plazo total (meses)",
            "Meses ya pagados",
            "Meses restantes",
            "Año cambio a variable",
            "Tipo periodo 1 (% TIN)",
            "Euríbor estimado (%)",
            "Diferencial (%)",
            "Tipo periodo 2 estimado (% TIN)",
            "Cuota periodo 1",
            "Cuota periodo 2",
            "Intereses totales periodo 1",
            "Intereses totales periodo 2",
            "Intereses totales (p1+p2)",
            "Intereses restantes (desde hoy)",
            "Saldo pendiente (aprox.)",
        ],
        "Valor": [
            P_old,
            n_old,
            months_paid,
            meses_restantes_old,
            change_year_old,
            r1_old,
            euribor_old,
            diff_old,
            r2_old_pct,
            cuota_p1_old if m1_old > 0 else np.nan,
            cuota_p2_old if (n_old - m1_old) > 0 else np.nan,
            ip1_old,
            ip2_old,
            float(ip1_old + ip2_old),
            interes_restante_old,
            saldo_pendiente_old if not _is_nan(saldo_pendiente_old) else np.nan,
        ]
    })
    st.dataframe(
        old_summary.style.format({"Valor": lambda x: "—" if (isinstance(x, float) and np.isnan(x)) else eur(x)}),
        use_container_width=True
    )

st.divider()

# ============================================================
# 2) Nueva oferta mixta del banco
# ============================================================
st.markdown(
    """
    <div class="param-header">
      <span class="param-chip">2) Nueva oferta mixta del banco</span>
      <span class="param-subtle">Mismos campos. Calculamos intereses totales de la nueva y comparamos con lo que te queda.</span>
    </div>
    """,
    unsafe_allow_html=True
)

def _autofill_new_offer():
    # euro_input -> st.text_input -> guardar STRING
    if not _is_nan(saldo_pendiente_old):
        st.session_state["ttm_p_new_eur"] = f"{float(saldo_pendiente_old):.2f}"
    suggested_years = max(1, int(math.ceil(meses_restantes_old / 12))) if meses_restantes_old > 0 else 1
    st.session_state["ttm_y_new"] = suggested_years
    st.session_state["ttm_change_year_new"] = min(int(st.session_state.get("ttm_change_year_old", 0)), suggested_years)

_ensure_text_state("ttm_p_new_eur")

cbtn1, cbtn2 = st.columns([1, 3])
with cbtn1:
    st.button(
        "✨ Autocompletar con saldo pendiente y plazo restante",
        use_container_width=True,
        on_click=_autofill_new_offer,
        key="ttm_btn_autofill"
    )
with cbtn2:
    if _is_nan(saldo_pendiente_old):
        st.info(
            "No puedo autocompletar el saldo pendiente porque tu amortization_schedule no devuelve saldo. "
            "Introduce el importe manualmente."
        )

with st.form("form_new_mixed", clear_on_submit=False):
    c1n, c2n, c3n, c4n = st.columns([1.2, 1, 1, 1])
    with c1n:
        _ensure_text_state("ttm_p_new_eur")
        P_new = euro_input(
            "Importe a financiar en la nueva hipoteca (€)",
            key="ttm_p_new_eur",
            default=float(saldo_pendiente_old) if not _is_nan(saldo_pendiente_old) else 150000.0,
            decimals=2,
            min_value=1000.0
        )
    with c2n:
        Y_new_default = max(1, int(math.ceil(meses_restantes_old / 12))) if meses_restantes_old > 0 else 25
        Y_new = st.slider(
            "Plazo total nueva (años)",
            min_value=1, max_value=40,
            value=int(st.session_state.get("ttm_y_new", Y_new_default)),
            step=1,
            key="ttm_y_new"
        )
    with c3n:
        change_year_new = st.slider(
            "Año en que pasa a variable (nueva)",
            min_value=0, max_value=Y_new,
            value=min(int(st.session_state.get("ttm_change_year_new", min(5, Y_new))), Y_new),
            step=1,
            key="ttm_change_year_new"
        )
    with c4n:
        r1_new = st.number_input(
            "Interés periodo 1 (fijo) — % TIN anual (nueva)",
            min_value=0.0, max_value=30.0, value=2.75, step=0.05, format="%.2f", key="ttm_r1_new"
        )

    d1n, d2n, d3n = st.columns([1, 1, 1])
    with d1n:
        diff_new = st.number_input(
            "Diferencial periodo variable — (% puntos) (nueva)",
            min_value=-2.0, max_value=10.0, value=0.80, step=0.05, format="%.2f", key="ttm_diff_new"
        )
    with d2n:
        euribor_new = st.number_input(
            "Euríbor estimado (%) (nueva)",
            min_value=-2.0, max_value=10.0, value=3.00, step=0.05, format="%.2f", key="ttm_euribor_new"
        )
        st.caption("(**Estimación constante** de Euríbor para todo el periodo variable)")
    with d3n:
        _ = st.form_submit_button("🧮 Calcular nueva oferta")

n_new = safe_int(Y_new) * 12
m1_new = safe_int(change_year_new) * 12
m1_new = max(0, min(m1_new, n_new))

r1_new_m = (r1_new / 100.0) / 12.0
r2_new_pct = euribor_new + diff_new
r2_new_m = (r2_new_pct / 100.0) / 12.0

df_new, cuota_p1_new, cuota_p2_new, ip1_new, ip2_new, _ = build_mixed_schedule(
    P_new, n_new, m1_new, r1_new_m, r2_new_m
)

if df_new.empty:
    st.error("No se pudo construir el cuadro de amortización de la nueva oferta (revisa amortization_schedule).")
    st.stop()

interes_total_new = float(ip1_new + ip2_new)

m1c, m2c, m3c, m4c, m5c = st.columns(5)
m1c.metric("💳 Cuota periodo 1 (nueva)", eur(cuota_p1_new) if m1_new > 0 else "—")
m2c.metric("💳 Cuota periodo 2 (nueva)", eur(cuota_p2_new) if (n_new - m1_new) > 0 else "—")
m3c.metric("💡 Intereses periodo 1 (nueva)", eur(ip1_new))
m4c.metric("💡 Intereses periodo 2 (nueva)", eur(ip2_new))
m5c.metric("📌 Intereses totales (nueva)", eur(interes_total_new))

st.caption(
    f"Nueva oferta: Periodo 1: {m1_new} meses a {r1_new:.2f}% · "
    f"Periodo 2: {max(n_new-m1_new,0)} meses a (Euríbor {euribor_new:.2f}% + dif {diff_new:.2f}%) = {r2_new_pct:.2f}% (estimado)."
)

st.divider()

# ============================================================
# 3) Comparación (visual)
# ============================================================
st.markdown("## 🔥 Comparación rápida")

ref_interest = interes_restante_old  # lo que te queda pagar de intereses en la actual
diff_interest = interes_total_new - ref_interest  # + => nueva peor (más intereses que lo que te queda)
diff_cuota_now = cuota_p1_new - cuota_actual_old  # comparamos cuota "ahora" vs cuota del periodo 1 de la nueva

if ref_interest <= 0:
    st.info("Tu hipoteca actual no tiene intereses restantes (o está finalizada).")
else:
    ahorro = ref_interest - interes_total_new  # + => ahorro
    ratio = 0.0 if ref_interest == 0 else max(0.0, min(1.0, ahorro / ref_interest))

    if ahorro >= 0:
        st.markdown(
            f"""
            <div class="soft-box" style="padding:18px;border-radius:18px;">
              <div class="value-title">✅ Ahorro estimado en intereses (nueva vs lo que te queda)</div>
              <div class="value-big">{eur(ahorro)}</div>
              <div class="param-subtle">Comparo <b>intereses restantes</b> de tu mixta actual con <b>intereses totales</b> de la nueva oferta (mixta).</div>
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
cZ.metric("Cuota actual (según periodo)", eur(cuota_actual_old))
cW.metric("Cuota periodo 1 (nueva)", eur(cuota_p1_new), delta=eur(diff_cuota_now))

cmp_df = pd.DataFrame({
    "Concepto": [
        "Intereses (referencia)",
        "Cuota ahora",
        "Meses restantes (actual)",
        "Saldo pendiente (actual)",
        "Intereses totales (nueva)",
        "Plazo total (nueva)",
        "Importe financiado (nueva)",
        "Tipo periodo 2 estimado (actual)",
        "Tipo periodo 2 estimado (nueva)",
    ],
    "Hipoteca actual (desde hoy)": [
        ref_interest,
        cuota_actual_old,
        meses_restantes_old,
        saldo_pendiente_old if not _is_nan(saldo_pendiente_old) else np.nan,
        np.nan,
        np.nan,
        np.nan,
        r2_old_pct,
        np.nan,
    ],
    "Nueva oferta": [
        np.nan,
        cuota_p1_new,
        n_new,
        np.nan,
        interes_total_new,
        n_new,
        P_new,
        np.nan,
        r2_new_pct,
    ],
    "Diferencia (nueva - actual)": [
        interes_total_new - ref_interest,
        cuota_p1_new - cuota_actual_old,
        n_new - meses_restantes_old,
        (P_new - saldo_pendiente_old) if not _is_nan(saldo_pendiente_old) else np.nan,
        np.nan,
        np.nan,
        np.nan,
        np.nan,
        (r2_new_pct - r2_old_pct),
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

with st.expander("Ver detalle alrededor del cambio (actual)"):
    if len(df_old) == 0:
        st.info("Sin detalle.")
    else:
        i0 = max(m1_old - 6, 0)
        i1 = min(m1_old + 6, len(df_old))
        st.dataframe(
            df_old.iloc[i0:i1].style.format({"Cuota": eur, "Intereses": eur, "Amortización": eur, "Saldo final": eur}),
            use_container_width=True
        )

with st.expander("Ver detalle alrededor del cambio (nueva)"):
    if len(df_new) == 0:
        st.info("Sin detalle.")
    else:
        i0 = max(m1_new - 6, 0)
        i1 = min(m1_new + 6, len(df_new))
        st.dataframe(
            df_new.iloc[i0:i1].style.format({"Cuota": eur, "Intereses": eur, "Amortización": eur, "Saldo final": eur}),
            use_container_width=True
        )

st.caption(
    "Notas: No contempla comisiones, seguros ni cambios reales del Euríbor. "
    "El periodo variable se estima como Euríbor constante + diferencial."
)

render_footer()
