# -*- coding: utf-8 -*-
import re
import numpy as np
import pandas as pd
import streamlit as st

# ----------------------------
# ESTILOS (Tabs + Parámetros sticky + caja gris + valores grandes + footer)
# ----------------------------
_CSS = """
<style>
/* ===== Tabs mejoradas ===== */
.stTabs [role="tablist"] {
    gap: 20px;
    justify-content: center;
    border-bottom: 3px solid #4A90E2;
    margin-bottom: 1rem;
}
.stTabs [role="tab"] {
    background-color: #f5f7fa;
    padding: 0.8rem 2rem;
    font-size: 1.1rem;
    font-weight: 600;
    border-radius: 12px 12px 0 0;
    border: 2px solid #d0d0d0;
    border-bottom: none;
    color: #333;
    transition: all 0.3s ease;
}
.stTabs [role="tab"]:hover {
    background-color: #e8f0fe;
    border-color: #4A90E2;
    color: #000;
}
.stTabs [aria-selected="true"] {
    background-color: #4A90E2 !important;
    color: white !important;
    border-color: #4A90E2 !important;
    font-weight: 700 !important;
}

/* ===== Card sticky para parámetros ===== */
div[data-testid="stForm"] {
    position: sticky;
    top: 0;
    z-index: 1000;
    background: #ffffff;
    border: 2px solid #e6e9ef;
    border-radius: 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    padding: 1rem 1.25rem;
    margin-bottom: 1.25rem;
}
.param-header {
    display: flex;
    align-items: center;
    gap: .6rem;
    margin-bottom: .5rem;
}
.param-chip {
    background: #4A90E2;
    color: #fff;
    font-weight: 700;
    font-size: .85rem;
    padding: .25rem .6rem;
    border-radius: 999px;
}
.param-subtle {
    color: #5f6570;
    font-size: .9rem;
    margin-left: .25rem;
}
.stButton>button {
    border-radius: 10px;
    padding: .6rem 1rem;
    font-weight: 700;
}

/* Caja gris suave */
.soft-box {
    background: #f2f3f5;
    border: 1px solid #e1e3e8;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    display: block;
}

/* Títulos y valores grandes (similar a st.metric) */
.value-title {
    font-size: 0.95rem;
    color: #5f6570;
    margin-bottom: .25rem;
}
.value-big {
    font-size: 1.6rem;
    font-weight: 800;
    line-height: 1.1;
}

/* ===== Footer ===== */
.app-footer {
    margin-top: 1.8rem;
    padding: .9rem 1rem;
    background: #f5f7fa;
    border: 1px solid #e6e9ef;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
    color: #5f6570;
    font-size: .92rem;
    text-align: center;
}
.app-footer a {
    color: #4A90E2;
    text-decoration: none;
    font-weight: 700;
}
.app-footer a:hover { text-decoration: underline; }

/* ===== Fix responsive tabs (móvil) ===== */
@media (max-width: 640px) {
  .stTabs [role="tablist"] {
    justify-content: flex-start;
    gap: 8px;
    overflow-x: auto;
    overflow-y: hidden;
    padding-bottom: .25rem;
    scrollbar-width: thin;
  }
  .stTabs [role="tab"] {
    flex: 0 0 auto;
    white-space: nowrap;
    padding: .5rem .9rem;
    font-size: .95rem;
    border-radius: 10px 10px 0 0;
  }
  div[data-testid="stForm"] {
    top: .5rem;
    padding: .75rem .9rem;
    margin-bottom: .75rem;
  }
  .soft-box {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
  }
  .value-title {
    margin-top: .35rem;
  }
}
.stTabs [role="tablist"]::-webkit-scrollbar { height: 6px; }
.stTabs [role="tablist"]::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: #cdd6e1;
}

/* ===== Bloques prima (dos columnas) ===== */
.prime-block {
    background:#ffffff;
    border:1px solid #e6e9ef;
    border-radius:16px;
    padding:1rem 1.1rem;
    box-shadow: 0 8px 20px rgba(0,0,0,0.05);
    margin-bottom: .75rem;
}
.prime-title {
    font-size: 1.25rem;
    font-weight: 900;
    margin: 0 0 .25rem 0;
    color:#1f2430;
}
.prime-sub {
    color:#5f6570;
    font-size:.95rem;
    margin: 0 0 .2rem 0;
    line-height:1.35;
}
.prime-note {
    color:#5f6570;
    font-size:.9rem;
    margin-top:.4rem;
}
.highlight-total {
    border: 2px solid #4A90E2;
    background: #e8f0fe;
    border-radius: 16px;
    padding: 1.1rem 1.25rem;
    box-shadow: 0 10px 24px rgba(0,0,0,0.06);
}
.highlight-total .k {
    color:#5f6570;
    font-size: .95rem;
    font-weight: 800;
    margin-bottom: .25rem;
}
.highlight-total .v {
    font-size: 2.0rem;
    font-weight: 1000;
    letter-spacing: -0.02em;
}
</style>
"""

def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)

# ============================
# Helpers: formato ES (miles "." y decimal ",")
# ============================
def fmt_number_es(x: float, decimals: int = 2) -> str:
    s = f"{float(x):,.{decimals}f}"  # US: 1,234.56
    return s.replace(",", "X").replace(".", ",").replace("X", ".")  # ES: 1.234,56

def eur(x: float) -> str:
    return f"{fmt_number_es(x, 2)} €"

def parse_number_es(s: str):
    """Acepta '150.000', '150000', '150.000,50', '150000,50', '150000.50', etc."""
    if s is None:
        return None
    s = str(s).strip()
    if s == "":
        return None
    s = s.replace("€", "").replace(" ", "")
    s = re.sub(r"[^0-9,.\-]", "", s)

    if "," in s:
        # Asumimos "," decimal (ES). Quitamos miles con "."
        s = s.replace(".", "").replace(",", ".")
    else:
        # Solo puntos o nada. Si el último grupo tiene 3 dígitos, asumimos miles.
        if "." in s:
            parts = s.split(".")
            if len(parts[-1]) == 3 and len(parts) > 1:
                s = s.replace(".", "")
            # si no, asumimos "." decimal (ya está bien)

    try:
        return float(s)
    except Exception:
        return None

def euro_input(
    label: str,
    key: str,
    default: float,
    decimals: int = 2,
    min_value: float | None = None,
    max_value: float | None = None,
    help_text: str | None = None,
    on_change=None
) -> float:
    """
    Text input con parsing ES.
    - Si pasas on_change, se ejecuta al cambiar el texto.
    """
    raw = st.text_input(
        label,
        value=fmt_number_es(default, decimals),
        key=key,
        help=help_text or "Ejemplo: 150.000 o 150.000,50",
        on_change=on_change
    )
    val = parse_number_es(raw)
    if val is None:
        st.caption(f"⚠️ Formato no válido. Usando {fmt_number_es(default, decimals)}.")
        val = float(default)

    if min_value is not None:
        val = max(val, float(min_value))
    if max_value is not None:
        val = min(val, float(max_value))
    return float(val)

def render_footer():
    st.markdown(
        """
        <div class="app-footer">
          <div><strong>Desarrollado por Alejandro Gordo</strong></div>
          <div>
            En caso de necesitar asesoramiento gratuito o una cotización de mi equipo, no duden en escribir a
            <a href="mailto:alejandro.gordo@nnespana.com">alejandro.gordo@nnespana.com</a>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================
# Utilidades amortización
# ============================
def amortization_schedule(P: float, r_m: float, n: int) -> pd.DataFrame:
    """Cuadro de amortización con tipo mensual constante r_m durante n meses."""
    if P <= 0 or n <= 0:
        return pd.DataFrame()
    if r_m == 0:
        payment = P / n
    else:
        payment = P * r_m / (1 - (1 + r_m) ** (-n))

    balance = P
    rows = []
    for m in range(1, n + 1):
        interest = balance * r_m if r_m != 0 else 0.0
        principal_pay = payment - interest if r_m != 0 else payment

        if m == n:
            principal_pay = balance
            payment_eff = principal_pay + interest
            balance_end = 0.0
        else:
            payment_eff = payment
            balance_end = balance - principal_pay

        rows.append(
            {
                "Mes": m,
                "Cuota": payment_eff,
                "Intereses": interest,
                "Amortización": principal_pay,
                "Saldo final": max(balance_end, 0.0),
            }
        )
        balance = balance_end

    return pd.DataFrame(rows)

def mixed_total_interest(P: float, n: int, r1_m: float, m1: int, r2_m: float):
    """
    Intereses totales de una hipoteca mixta:
    - Periodo 1: r1_m, cuota calculada con r1_m para TODO el plazo (n), se pagan m1 meses.
    - Periodo 2: r2_m, cuota recalculada con r2_m sobre saldo restante y n-m1 meses.
    Devuelve (intereses_totales, intereses_periodo1, intereses_periodo2, saldo_tras_p1).
    """
    if P <= 0 or n <= 0 or m1 < 0 or m1 > n:
        return 0.0, 0.0, 0.0, P

    if r1_m == 0:
        payment1 = P / n
    else:
        payment1 = P * r1_m / (1 - (1 + r1_m) ** (-n))

    balance = P
    interest_p1 = 0.0
    for _ in range(m1):
        interest = balance * r1_m if r1_m != 0 else 0.0
        principal_pay = payment1 - interest if r1_m != 0 else payment1
        balance -= principal_pay
        interest_p1 += interest

    n2 = n - m1
    if n2 <= 0:
        return interest_p1, interest_p1, 0.0, 0.0

    if r2_m == 0:
        payment2 = balance / n2
    else:
        payment2 = balance * r2_m / (1 - (1 + r2_m) ** (-n2))

    interest_p2 = 0.0
    bal = balance
    for _ in range(n2):
        interest = bal * r2_m if r2_m != 0 else 0.0
        principal_pay = payment2 - interest if r2_m != 0 else payment2
        bal -= principal_pay
        interest_p2 += interest

    return interest_p1 + interest_p2, interest_p1, interest_p2, balance

def solve_r2_for_equal_interest(P: float, n: int, r_fixed_m: float, r1_m: float, m1: int):
    """
    Encuentra r2_m (tipo mensual periodo 2) tal que:
    intereses_totales_mixta(r1_m, m1, r2_m) == intereses_totales_fija(r_fixed_m)
    Búsqueda por bisección con cota amplia.
    """
    df_fixed = amortization_schedule(P, r_fixed_m, n)
    target = float(df_fixed["Intereses"].sum())

    if m1 >= n:
        total_mixed, ip1, ip2, _ = mixed_total_interest(P, n, r1_m, m1, r2_m=0.0)
        return None, target, total_mixed, ip1, ip2

    def f(r2m):
        total, _, _, _ = mixed_total_interest(P, n, r1_m, m1, r2m)
        return total - target

    lo = 0.0
    hi = 2.0 / 12.0  # 200% anual aprox.
    f_lo = f(lo)
    f_hi = f(hi)

    attempts = 0
    while f_lo * f_hi > 0 and attempts < 20:
        hi *= 1.5
        f_hi = f(hi)
        attempts += 1

    if f_lo * f_hi > 0:
        total_mixed, ip1, ip2, _ = mixed_total_interest(P, n, r1_m, m1, r2_m=lo)
        return None, target, total_mixed, ip1, ip2

    for _ in range(80):
        mid = (lo + hi) / 2
        f_mid = f(mid)
        if abs(f_mid) < 1e-8:
            lo = hi = mid
            break
        if f_lo * f_mid <= 0:
            hi = mid
        else:
            lo = mid
            f_lo = f_mid

    r2_m_solution = (lo + hi) / 2
    total_mixed, ip1, ip2, _ = mixed_total_interest(P, n, r1_m, m1, r2_m_solution)
    return r2_m_solution, target, total_mixed, ip1, ip2

# ============================
# Matrices de primas + interpolación (edad x capital)
# ============================
CAPITALS_STD = [50000, 75000, 100000, 125000, 150000, 175000, 200000, 225000, 250000, 275000, 300000, 325000, 350000, 375000, 400000]

def _lerp(x0, x1, y0, y1, x):
    if x0 == x1:
        return float(y0)
    return float(y0 + (y1 - y0) * (x - x0) / (x1 - x0))

def prima_orientativa_bilineal(edad: float, capital: float, df: pd.DataFrame) -> float:
    """Interpolación bilineal (edad x capital). Extrapola por el último tramo si se sale del rango."""
    ages = df.index.to_numpy(dtype=float)
    caps = np.array(df.columns, dtype=float)

    if len(ages) < 2 or len(caps) < 2:
        return float(df.iloc[0, 0])

    if edad <= ages.min():
        a0, a1 = ages[0], ages[1]
    elif edad >= ages.max():
        a0, a1 = ages[-2], ages[-1]
    else:
        a1 = ages[ages >= edad].min()
        a0 = ages[ages <= edad].max()

    if capital <= caps.min():
        c0, c1 = caps[0], caps[1]
    elif capital >= caps.max():
        c0, c1 = caps[-2], caps[-1]
    else:
        c1 = caps[caps >= capital].min()
        c0 = caps[caps <= capital].max()

    v_a0c0 = float(df.loc[int(a0), int(c0)])
    v_a0c1 = float(df.loc[int(a0), int(c1)])
    v_a1c0 = float(df.loc[int(a1), int(c0)])
    v_a1c1 = float(df.loc[int(a1), int(c1)])

    v0 = _lerp(c0, c1, v_a0c0, v_a0c1, capital)
    v1 = _lerp(c0, c1, v_a1c0, v_a1c1, capital)
    v = _lerp(a0, a1, v0, v1, edad)
    return float(v)

def _build_df_from_table(table_str: str, capitals: list[int]) -> pd.DataFrame:
    """Parsea tabla (Edad + 15 valores) con coma decimal. Ignora cabecera 'Edad ...'."""
    rows = []
    for line in table_str.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("edad"):
            continue
        parts = re.split(r"\s+", line)
        age = int(parts[0])
        vals = []
        for p in parts[1:1+len(capitals)]:
            vals.append(float(p.replace(".", "").replace(",", ".")))
        if len(vals) != len(capitals):
            raise ValueError(f"Fila edad {age}: esperaba {len(capitals)} valores y recibí {len(vals)}")
        rows.append((age, vals))
    df = pd.DataFrame({age: vals for age, vals in rows}).T
    df.columns = capitals
    df.index.name = "Edad"
    return df.sort_index()

# ---- Bloque IZQ: ejemplo entidad bancaria (ING) ----
PREMIAS_ING = {
    18: [9.41, 13.81, 18.64, 22.88, 27.43, 31.96, 36.50, 41.25, 45.83, 50.42, 54.56, 59.19, 63.74, 68.27, 72.81],
    19: [9.25, 13.88, 18.60, 23.13, 27.75, 32.38, 37.00, 41.63, 46.26, 50.88, 55.39, 60.13, 64.76, 69.39, 73.79],
    20: [9.16, 13.73, 18.31, 22.89, 27.69, 32.05, 36.70, 41.20, 45.78, 50.36, 54.74, 59.51, 64.09, 68.67, 72.77],
    21: [9.20, 13.78, 18.38, 22.98, 27.75, 32.17, 36.83, 41.36, 45.96, 50.56, 54.99, 59.74, 64.34, 68.94, 73.15],
    22: [9.23, 13.84, 18.45, 23.07, 27.82, 32.30, 36.96, 41.52, 46.14, 50.75, 55.25, 59.98, 64.58, 69.21, 73.53],
    23: [9.27, 13.89, 18.52, 23.16, 27.88, 32.42, 37.08, 41.69, 46.32, 50.95, 55.50, 60.21, 64.83, 69.47, 73.91],
    24: [9.30, 13.95, 18.60, 23.25, 27.95, 32.55, 37.21, 41.85, 46.49, 51.14, 55.76, 60.45, 65.09, 69.74, 74.29],
    25: [9.34, 14.00, 18.67, 23.34, 28.01, 32.67, 37.34, 42.01, 46.67, 51.34, 56.01, 60.68, 65.35, 70.01, 74.68],
    26: [9.27, 13.90, 18.60, 23.18, 27.83, 32.46, 37.04, 41.68, 46.34, 51.00, 55.47, 60.04, 64.75, 69.38, 74.11],
    27: [9.21, 13.81, 18.54, 23.01, 27.64, 32.25, 36.74, 41.36, 46.00, 50.67, 54.94, 59.41, 64.15, 68.74, 73.53],
    28: [9.14, 13.71, 18.47, 22.85, 27.46, 32.04, 36.44, 41.04, 45.67, 50.34, 54.40, 58.88, 63.55, 68.11, 72.96],
    29: [9.08, 13.62, 18.41, 22.69, 27.27, 31.82, 36.13, 40.72, 45.33, 50.00, 53.87, 58.36, 62.95, 67.48, 71.89],
    30: [9.01, 13.52, 18.34, 22.53, 27.09, 31.60, 35.83, 40.36, 45.00, 49.50, 53.33, 57.84, 62.34, 66.85, 70.82],
    31: [9.29, 13.95, 19.03, 23.24, 27.81, 32.59, 37.04, 41.71, 46.43, 50.93, 55.11, 59.77, 64.42, 69.08, 73.18],
    32: [9.58, 14.39, 19.71, 23.94, 28.54, 33.57, 38.26, 43.07, 47.86, 52.37, 56.89, 61.71, 66.50, 71.32, 75.55],
    33: [9.86, 14.82, 20.40, 24.64, 29.28, 34.56, 39.48, 44.43, 49.29, 53.80, 58.68, 63.64, 68.59, 73.56, 77.91],
    34: [10.15, 15.26, 21.09, 25.34, 30.01, 35.54, 40.69, 45.77, 50.72, 55.23, 60.46, 65.57, 70.67, 75.79, 80.26],
    35: [10.43, 15.65, 21.80, 26.09, 31.69, 36.52, 41.87, 47.11, 52.17, 57.42, 62.25, 67.50, 72.76, 78.01, 82.62],
    36: [11.01, 16.51, 23.01, 27.52, 33.55, 38.81, 44.32, 49.84, 55.03, 60.56, 65.87, 71.38, 76.81, 82.34, 87.42],
    37: [11.58, 17.37, 24.22, 28.95, 35.40, 41.09, 46.76, 52.56, 57.90, 63.71, 69.48, 75.27, 80.86, 86.66, 92.23],
    38: [12.16, 18.23, 25.44, 30.38, 37.26, 43.38, 49.21, 55.29, 60.77, 66.55, 73.10, 79.15, 84.90, 90.97, 97.04],
    39: [12.73, 19.09, 26.65, 31.81, 39.12, 45.67, 51.65, 58.01, 63.64, 69.84, 76.73, 83.02, 88.94, 95.32, 101.83],
    40: [13.30, 19.95, 27.85, 33.24, 40.98, 47.96, 54.10, 60.74, 66.48, 73.13, 80.36, 86.89, 93.03, 99.66, 106.61],
    41: [15.04, 22.57, 31.45, 37.60, 46.16, 54.00, 60.91, 68.41, 74.40, 82.72, 90.44, 97.14, 104.46, 112.76, 120.96],
    42: [16.79, 25.20, 35.05, 41.95, 51.34, 60.05, 67.72, 76.09, 82.32, 92.31, 100.51, 107.38, 115.89, 125.86, 135.31],
    43: [18.53, 27.83, 38.66, 46.32, 56.51, 66.09, 74.54, 83.76, 90.24, 101.90, 110.59, 117.63, 127.33, 138.96, 149.65],
    44: [20.27, 30.45, 42.27, 50.68, 61.69, 72.14, 81.35, 91.43, 98.16, 111.51, 120.68, 127.88, 138.76, 152.06, 163.00],
    45: [22.02, 33.03, 45.88, 55.04, 66.87, 78.18, 88.17, 99.09, 110.10, 121.11, 130.76, 143.13, 154.14, 165.16, 173.35],
    46: [23.70, 35.55, 49.42, 59.25, 71.99, 83.28, 94.93, 106.68, 118.52, 130.26, 140.74, 153.71, 165.55, 177.40, 186.56],
    47: [25.37, 38.07, 52.95, 63.46, 77.12, 88.38, 101.68, 114.27, 126.95, 139.42, 150.73, 164.30, 176.97, 189.63, 199.77],
    48: [27.04, 40.60, 56.49, 67.67, 82.25, 93.47, 108.44, 121.86, 135.63, 148.58, 160.71, 174.89, 188.39, 201.87, 212.99],
    49: [28.72, 43.12, 60.03, 71.88, 87.38, 98.57, 115.21, 129.45, 144.31, 157.85, 170.70, 185.47, 199.78, 214.10, 226.20],
    50: [30.44, 45.65, 63.57, 76.09, 93.07, 108.67, 121.98, 137.04, 152.19, 167.13, 180.69, 196.03, 211.18, 226.34, 239.41],
    51: [35.69, 53.52, 73.56, 89.21, 107.55, 126.61, 141.14, 160.64, 178.43, 196.25, 209.98, 230.64, 248.33, 266.13, 272.85],
    52: [40.94, 61.39, 83.55, 102.33, 122.04, 144.54, 160.30, 184.24, 204.66, 225.36, 239.26, 265.26, 285.48, 305.92, 306.28],
    53: [46.18, 69.27, 93.54, 115.44, 136.52, 162.48, 179.46, 207.83, 230.90, 254.48, 268.55, 299.88, 322.64, 345.71, 339.70],
    54: [51.43, 77.14, 103.53, 128.56, 151.01, 180.42, 198.62, 231.43, 257.13, 283.09, 297.84, 334.50, 359.79, 385.49, 373.15],
    55: [56.67, 85.01, 113.53, 141.68, 165.45, 198.35, 217.78, 255.03, 283.37, 311.70, 322.13, 369.07, 396.93, 425.27, 426.60],
    56: [59.65, 89.47, 120.36, 149.12, 175.45, 208.76, 231.85, 268.81, 298.24, 328.06, 341.41, 387.87, 417.71, 447.53, 455.75],
    57: [62.62, 93.94, 127.18, 156.56, 185.45, 219.17, 245.92, 282.60, 313.12, 344.41, 360.68, 406.67, 438.50, 469.79, 484.91],
    58: [65.60, 98.40, 134.01, 164.00, 195.44, 229.59, 259.99, 296.38, 327.99, 360.75, 379.95, 425.47, 459.29, 492.05, 514.06],
    59: [68.57, 102.86, 140.83, 171.43, 205.44, 240.00, 272.56, 310.17, 342.86, 377.10, 399.22, 444.27, 480.07, 514.32, 543.21],
    60: [71.55, 107.32, 147.65, 178.86, 215.44, 250.41, 283.14, 321.95, 357.73, 393.50, 418.54, 465.04, 500.82, 536.59, 572.36],
}

PRIMA_ING_DF = pd.DataFrame.from_dict(PREMIAS_ING, orient="index", columns=CAPITALS_STD).sort_index()
PRIMA_ING_DF.index.name = "Edad"

# ---- Bloque DCHA: aseguradora (Nationale Nederlanden) ----
TABLA_NN_FALLEC = """
Edad 50.000,00 75.000,00 100.000,00 125.000,00 150.000,00 175.000,00 200.000,00 225.000,00 250.000,00 275.000,00 300.000,00 325.000,00 350.000,00 375.000,00 400.000,00
18 6,16 6,74 7,32 7,91 8,5 9,08 9,67 10,26 10,84 11,42 12,01 12,6 13,18 13,76 14,35
19 6,17 6,76 7,36 7,95 8,55 9,15 9,74 10,34 10,93 11,53 12,12 12,72 13,31 13,91 14,5
20 6,19 6,79 7,39 8 8,6 9,21 9,82 10,42 11,03 11,63 12,24 12,84 13,45 14,05 14,66
21 6,2 6,81 7,43 8,04 8,66 9,28 9,89 10,51 11,12 11,73 12,35 12,96 13,58 14,19 14,81
22 6,21 6,84 7,46 8,09 8,72 9,34 9,97 10,59 11,21 11,84 12,46 13,09 13,71 14,34 14,96
23 6,22 6,86 7,5 8,13 8,77 9,41 10,04 10,67 11,31 11,94 12,57 13,21 13,84 14,48 15,11
24 6,24 6,89 7,53 8,18 8,82 9,47 10,12 10,76 11,4 12,04 12,69 13,33 13,98 14,62 15,27
25 6,25 6,91 7,57 8,22 8,88 9,54 10,19 10,84 11,5 12,15 12,8 13,46 14,11 14,76 15,42
26 6,28 6,96 7,64 8,32 8,99 9,67 10,35 11,02 11,7 12,37 13,04 13,72 14,4 15,07 15,75
27 6,32 7,02 7,71 8,41 9,11 9,81 10,51 11,2 11,9 12,59 13,29 13,98 14,68 15,38 16,08
28 6,35 7,07 7,79 8,51 9,22 9,94 10,66 11,38 12,1 12,82 13,53 14,25 14,97 15,69 16,4
29 6,39 7,12 7,86 8,6 9,34 10,08 10,82 11,56 12,3 13,04 13,78 14,51 15,25 15,99 16,73
30 6,42 7,18 7,93 8,69 9,46 10,22 10,98 11,74 12,5 13,26 14,02 14,78 15,54 16,3 17,06
31 6,57 7,4 8,24 9,08 9,92 10,76 11,6 12,44 13,28 14,12 14,96 15,8 16,64 17,48 18,32
32 6,71 7,63 8,54 9,46 10,38 11,3 12,22 13,14 14,06 14,98 15,9 16,82 17,74 18,65 19,57
33 6,86 7,85 8,85 9,85 10,85 11,85 12,85 13,84 14,84 15,84 16,84 17,84 18,83 19,83 20,83
34 7 8,08 9,15 10,23 11,31 12,39 13,47 14,55 15,62 16,7 17,78 18,86 19,93 21,01 22,08
35 7,15 8,3 9,46 10,62 11,78 12,93 14,09 15,25 16,4 17,56 18,72 19,88 21,03 22,18 23,34
36 7,49 8,86 10,22 11,49 12,76 14,02 15,29 16,76 18,23 19,69 21,16 22,53 23,89 25,26 26,62
37 7,83 9,41 10,98 12,36 13,74 15,11 16,49 18,27 20,05 21,83 23,6 25,18 26,76 28,33 29,91
38 8,18 9,96 11,75 13,23 14,72 16,2 17,69 19,78 21,87 23,96 26,05 27,83 29,62 31,41 33,19
39 8,52 10,51 12,51 14,1 15,7 17,29 18,89 21,29 23,69 26,09 28,49 30,49 32,48 34,48 36,48
40 8,86 11,06 13,27 14,98 16,68 18,38 20,09 22,8 25,51 28,22 30,93 33,14 35,34 37,55 39,76
41 9,67 12,27 14,87 17,07 19,26 21,46 23,66 26,66 29,66 32,66 35,67 38,27 40,87 43,47 46,07
42 10,49 13,48 16,47 19,16 21,85 24,54 27,23 30,52 33,82 37,11 40,4 43,39 46,39 49,38 52,37
43 11,3 14,68 18,06 21,25 24,43 27,62 30,8 34,38 37,97 41,55 45,14 48,52 51,91 55,29 58,68
44 12,12 15,89 19,66 23,34 27,02 30,69 34,37 38,25 42,12 46 49,87 53,65 57,43 61,21 64,98
45 12,93 17,1 21,26 25,43 29,6 33,77 37,94 42,11 46,28 50,44 54,61 58,78 62,95 67,12 71,29
46 13,98 18,72 23,46 28,2 32,94 37,69 42,43 47,17 51,91 56,65 61,39 66,13 70,88 75,62 80,36
47 15,04 20,35 25,66 30,98 36,29 41,6 46,92 52,23 57,54 62,86 68,17 73,48 78,8 84,12 89,43
48 16,09 21,98 27,86 33,75 39,64 45,52 51,41 57,3 63,18 69,06 74,95 80,84 86,72 92,61 98,5
49 17,15 23,6 30,06 36,52 42,98 49,44 55,9 62,36 68,82 75,27 81,73 88,19 94,65 101,11 107,57
50 18,2 25,23 32,26 39,29 46,32 53,36 60,39 67,42 74,45 81,48 88,51 95,54 102,58 109,61 116,64
51 19,8 27,55 35,3 43,04 50,77 58,51 66,25 73,99 81,72 89,46 97,2 104,95 112,69 120,43 128,17
52 21,4 29,87 38,34 46,78 55,22 63,66 72,1 80,55 89 97,45 105,9 114,35 122,8 131,25 139,7
53 23 32,19 41,37 50,52 59,67 68,81 77,96 87,12 96,28 105,43 114,59 123,75 132,91 142,07 151,23
54 24,6 34,51 44,41 54,26 64,11 73,96 83,81 93,68 103,55 113,42 123,29 133,15 143,02 152,89 162,76
55 26,2 36,83 47,45 58 68,56 79,11 89,67 100,25 110,82 121,4 131,98 142,56 153,14 163,71 174,29
56 27,51 38,79 50,06 61,29 72,51 83,74 94,96 106,2 117,44 128,69 139,93 151,17 162,41 173,65 184,89
57 28,82 40,75 52,68 64,57 76,46 88,36 100,25 112,16 124,06 135,97 147,88 159,78 171,68 183,59 195,49
58 30,14 42,72 55,3 67,86 80,42 92,98 105,54 118,11 130,68 143,25 155,82 168,39 180,96 193,52 206,09
59 31,45 44,68 57,91 71,14 84,37 97,6 110,83 124,06 137,3 150,54 163,77 177 190,23 203,46 216,69
"""

TABLA_NN_FALL_IA = """
Edad 50.000,00 75.000,00 100.000,00 125.000,00 150.000,00 175.000,00 200.000,00 225.000,00 250.000,00 275.000,00 300.000,00 325.000,00 350.000,00 375.000,00 400.000,00
18 9,66 11,9 14,14 15,93 17,72 19,51 21,31 23,33 25,35 27,37 29,39 31,41 33,42 35,44 37,46
19 9,6 11,81 14,02 15,79 17,56 19,32 21,09 23,1 25,12 27,13 29,15 31,16 33,17 35,19 37,2
20 9,54 11,73 13,9 15,65 17,39 19,13 20,88 22,88 24,88 26,88 28,89 30,89 32,9 34,9 36,91
21 9,47 11,64 13,78 15,51 17,23 18,95 20,67 22,66 24,65 26,64 28,63 30,61 32,6 34,59 36,58
22 9,41 11,56 13,65 15,37 17,06 18,76 20,46 22,44 24,42 26,4 28,38 30,36 32,34 34,32 36,29
23 9,34 11,47 13,53 15,24 16,9 18,58 20,24 22,21 24,19 26,17 28,14 30,12 32,09 34,07 36,05
24 9,28 11,39 13,41 15,1 16,73 18,39 20,03 21,99 23,96 25,93 27,9 29,87 31,84 33,81 35,79
25 9,21 11,3 13,38 15,04 16,69 18,35 20 21,85 23,71 25,56 27,42 29,28 31,13 32,99 34,88
26 9,23 11,36 13,48 15,18 16,89 18,59 20,3 22,23 24,15 26,08 28,01 29,93 31,86 33,78 35,71
27 9,26 11,42 13,58 15,32 17,08 18,81 20,61 22,6 24,6 26,6 28,59 30,59 32,59 34,58 36,58
28 9,28 11,48 13,68 15,46 17,27 19,03 20,92 22,98 25,05 27,12 29,18 31,25 33,31 35,38 37,45
29 9,3 11,55 13,78 15,61 17,46 19,25 21,23 23,35 25,49 27,63 29,76 31,99 34,23 36,46 38,7
30 9,33 11,49 13,65 15,37 17,1 18,82 20,54 22,57 24,61 26,64 28,67 30,7 32,74 34,77 36,8
31 9,56 11,88 14,19 16,05 17,9 19,75 21,61 23,73 25,85 27,98 30,1 32,41 34,73 37,04 39,36
32 9,8 12,26 14,73 16,72 18,71 20,68 22,67 24,89 27,12 29,35 31,58 34,04 36,51 38,97 41,43
33 10,03 12,65 15,26 17,39 19,51 21,61 23,74 26,05 28,37 30,68 32,99 35,61 38,22 40,83 43,45
34 10,27 13,03 15,8 18,06 20,31 22,54 24,86 27,22 29,58 31,94 34,31 37,07 39,84 42,6 45,37
35 10,5 13,24 15,97 18,16 20,34 22,53 24,71 27,22 29,73 32,24 34,75 37,16 39,58 41,99 44,4
36 11,05 13,98 16,91 19,26 21,61 23,95 26,3 28,99 31,68 34,36 37,05 39,98 42,9 45,83 48,75
37 11,6 14,73 17,85 20,37 22,88 25,38 27,9 30,75 33,59 36,44 39,29 42,4 45,52 48,63 51,75
38 12,14 15,47 18,79 21,47 24,14 26,8 29,51 32,51 35,52 38,52 41,53 44,86 48,18 51,51 54,85
39 12,69 16,21 19,73 22,58 25,41 28,23 31,12 34,28 37,44 40,6 43,76 47,32 50,88 54,44 58
40 13,24 17,54 21,83 25,23 28,62 32,01 35,41 39,25 43,09 46,93 50,77 54,61 58,44 62,28 66,12
41 14,46 19,45 24,44 28,4 32,35 36,31 40,26 44,73 49,2 53,67 58,14 63,12 68,11 73,09 78,07
42 15,68 21,36 27,05 31,57 36,09 40,6 45,12 50,21 55,31 60,4 65,5 71,18 76,86 82,54 88,22
43 16,9 23,27 29,67 34,74 39,82 44,9 49,97 55,7 61,42 67,15 72,88 79,24 85,61 91,97 98,34
44 18,12 25,18 32,28 37,91 43,55 49,18 54,83 61,18 67,54 73,89 80,25 87,32 94,4 101,47 108,55
45 19,34 26,56 33,77 39,44 45,11 50,78 56,45 62,89 69,33 75,76 82,2 89,42 96,65 103,88 107,95
46 21,16 29,55 37,93 44,57 51,22 57,86 64,51 72,1 79,68 87,27 94,86 103,24 111,63 120,01 128,4
47 22,98 32,54 42,09 49,7 57,32 64,93 72,55 81,3 90,04 98,78 107,53 117,09 126,64 136,2 145,76
48 24,8 35,53 46,25 54,84 63,41 72,01 80,6 90,49 100,39 110,29 120,18 130,93 141,67 152,42 163,17
49 26,62 38,53 50,4 59,97 69,52 79,08 88,64 99,69 110,74 121,79 132,84 144,78 156,72 168,66 180,6
50 28,44 40,34 52,24 61,56 70,87 80,19 89,52 99,13 108,75 118,36 127,98 139,09 150,2 161,31 172,42
51 31,36 44,9 58,45 69,13 79,8 90,48 101,15 113,29 125,43 137,57 149,71 163,25 176,79 190,33 203,87
52 34,28 49,46 64,64 76,69 88,74 100,77 112,81 127,45 142,1 156,74 171,38 186,56 201,74 216,92 232,11
53 37,2 54,02 70,85 84,25 97,67 111,06 124,46 141,62 158,78 175,93 193,09 209,66 226,23 242,8 259,37
54 40,12 58,58 77,04 91,82 106,61 121,35 136,11 155,78 175,46 195,13 214,8 232,76 250,71 268,67 286,63
55 43,04 61,62 80,2 95,7 111,2 126,69 138,18 154,73 171,28 187,84 204,39 220,94 237,49 254,04 270,59
56 45,75 66,29 86,83 103,34 119,84 136,35 147,7 165,99 184,29 202,58 220,88 241,42 261,96 282,49 303,03
57 48,47 70,95 93,46 110,97 128,48 145,99 157,21 177,25 197,29 217,33 237,37 261,91 286,45 310,99 335,53
58 51,18 75,62 100,1 118,61 137,11 155,63 166,73 188,52 210,3 232,09 253,88 282,4 310,92 339,43 367,95
59 53,89 77,81 101,73 121,99 142,25 162,5 176,25 197,54 218,82 240,11 261,39 282,81 304,24 325,39 346,54
60 56,6 80 103,35 125,45 147,55 169,65 185,93 209,09 232,25 255,41 278,57 304,17 329,78 355,38 380,98
"""

@st.cache_data(show_spinner=False)
def get_nn_dfs():
    nn_fallec = _build_df_from_table(TABLA_NN_FALLEC, CAPITALS_STD)
    nn_fall_ia = _build_df_from_table(TABLA_NN_FALL_IA, CAPITALS_STD)
    return nn_fallec, nn_fall_ia

# ============================
# Helpers de sincronización: capital banco/aseguradora
# ============================
def sync_capital_from_source(source_key: str, target_keys: list[str], decimals: int = 0):
    """
    Copia el capital (text input) de source_key al resto de target_keys.
    Útil para mantener sincronizados:
      - capital_ing_prima_eur
      - capital_nn_prima_eur
    """
    raw = st.session_state.get(source_key, "")
    val = parse_number_es(raw)
    if val is None:
        return
    for k in target_keys:
        st.session_state[k] = fmt_number_es(val, decimals)
