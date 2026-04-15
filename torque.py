# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import base64
import os
import datetime

# =================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS EXTENDIDOS
# =================================================================
st.set_page_config(
    page_title="Calculador de Torque de Ingeniería | Sustratos Acero y Aluminio",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #e9ecef;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .classification-box {
        background-color: #f8f9fa;
        padding: 35px;
        border: 2px solid #003366;
        border-radius: 15px;
        margin-top: 20px;
        margin-bottom: 30px;
        text-align: center;
    }
    .theory-box {
        background-color: #f1f8ff;
        padding: 25px;
        border-left: 8px solid #003366;
        border-radius: 8px;
        font-size: 1rem;
        line-height: 1.6;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 20px;
        border-left: 8px solid #ffa000;
        border-radius: 8px;
        color: #856404;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. BASES DE DATOS TÉCNICAS (SIN RECORTES)
# =================================================================

PERNOS_DB = {
    "1/4\"-20 UNC": {"d": 6.35, "n": 20, "dw": 15.8},
    "5/16\"-18 UNC": {"d": 7.94, "n": 18, "dw": 17.5},
    "3/8\"-16 UNC": {"d": 9.525, "n": 16, "dw": 20.6},
    "1/2\"-13 UNC": {"d": 12.70, "n": 13, "dw": 27.0},
    "5/8\"-11 UNC": {"d": 15.875, "n": 11, "dw": 33.3},
    "3/4\"-10 UNC": {"d": 19.05, "n": 10, "dw": 37.3}
}

# Factores K para Acero
K_ACERO = {
    "Zincado / Galvanizado (Seco)": 0.20,
    "Perno Negro (Aceitado)": 0.18,
    "Lubricado (Grasa/Aceite)": 0.15,
    "Personalizado": 0.0
}

# Factores K para Aluminio (Enfoque en lubricación para evitar soldadura en frío)
K_ALUMINIO = {
    "Aluminio con Pasta Anti-Seize (Recomendado)": 0.15,
    "Aluminio Seco (Alto riesgo de Galling)": 0.25,
    "Aluminio con Lubricación Ligera": 0.18,
    "Personalizado": 0.0
}

ALUMINIO_ALLOYS = {
    "AA6063-T5 (Fy = 110 MPa)": 110.0,
    "AA6063-T6 (Fy = 170 MPa)": 170.0,
    "AA6061-T6 (Fy = 235 MPa)": 235.0,
    "Personalizado (Ingresar manual)": 0.0
}

# =================================================================
# 3. INTERFAZ Y LÓGICA DE ENTRADA
# =================================================================

st.sidebar.title("🛠️ Parámetros de Ingeniería")

st.sidebar.subheader("Perno")
perno_sel = st.sidebar.selectbox("Designación Perno", list(PERNOS_DB.keys()), index=3)
fy_p = st.sidebar.number_input("Fluencia Perno (MPa)", value=450.0)

st.sidebar.markdown("---")
st.sidebar.subheader("Sustrato Base")
tipo_mat = st.sidebar.radio("Material del Sustrato", ["Acero", "Aluminio"])

# Lógica condicional para el Sustrato
if tipo_mat == "Aluminio":
    aleacion = st.sidebar.selectbox("Aleación", list(ALUMINIO_ALLOYS.keys()), index=1)
    if "Personalizado" in aleacion:
        fy_s = st.sidebar.number_input("Fy Aluminio (MPa)", value=170.0)
    else:
        fy_s = ALUMINIO_ALLOYS[aleacion]
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Superficie Aluminio (K)")
    k_opt = st.sidebar.selectbox("Estado de Superficie", list(K_ALUMINIO.keys()))
    if "Personalizado" in k_opt:
        k_val = st.sidebar.number_input("Valor K Manual", value=0.15, step=0.01)
    else:
        k_val = K_ALUMINIO[k_opt]
    limit_factor = 0.90 # Seguridad s/ aplastamiento
else:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Superficie Acero (K)")
    fy_s = st.sidebar.number_input("Fy Acero (MPa)", value=250.0)
    k_opt = st.sidebar.selectbox("Estado de Superficie", list(K_ACERO.keys()))
    if "Personalizado" in k_opt:
        k_val = st.sidebar.number_input("Valor K Manual", value=0.20, step=0.01)
    else:
        k_val = K_ACERO[k_opt]
    limit_factor = 1.0

tuerca_nyloc = st.sidebar.checkbox("Usa Seguro de Nylon (Nyloc)", value=True)
perc_util = st.sidebar.slider("Precarga (% Fy Perno)", 30, 90, 70)

# =================================================================
# 4. CÁLCULOS DE INGENIERÍA
# =================================================================

d = PERNOS_DB[perno_sel]["d"]
n = PERNOS_DB[perno_sel]["n"]
dw = PERNOS_DB[perno_sel]["dw"]
p = 25.4 / n

# Áreas
As = 0.7854 * (d - (0.9382 * p))**2
Ab = (np.pi / 4) * (dw**2 - d**2)

# Fuerzas
F_p = (fy_p * (perc_util / 100.0)) * As
F_s = (fy_s * limit_factor) * Ab

# Selección de Precarga (Fi) controlada por el sustrato
control_s = False
if F_s < F_p:
    Fi = F_s
    control_s = True
else:
    Fi = F_p

# Torque Base + Nylon
torque_base = k_val * (d / 1000.0) * Fi
t_nylon = 2.5 if (tuerca_nyloc and d >= 12) else (1.2 if tuerca_nyloc else 0.0)

torque_final = torque_base + t_nylon

# =================================================================
# 5. DESPLIEGUE DE RESULTADOS
# =================================================================

st.title("🔩 Memoria de Torque Conexiones Mecánicas]")
st.caption(f"Configuración de Sustrato: {tipo_mat} | Factor K Adoptado: {k_val}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Área Tensión", f"{As:.1f} mm²")
m2.metric("Área Apoyo", f"{Ab:.1f} mm²")
m3.metric("Precarga Fi", f"{Fi/1000:.2f} kN")
m4.metric("Presión Cara", f"{Fi/Ab:.1f} MPa")

if control_s:
    st.markdown(f"""<div class="warning-box">
    <strong>⚠️ LIMITACIÓN POR APLASTAMIENTO:</strong> La fuerza del perno excedía la capacidad del sustrato 
    de {tipo_mat}. Se ha reducido la precarga para proteger el material base de deformación permanente.
    </div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class="classification-box">
    <h2 style="color: #003366; font-size: 1.1rem; margin-bottom: 5px;">TORQUE DE APRIETE NOMINAL</h2>
    <span style="font-size: 4.5rem; font-weight: 900; color: #003366;">{torque_final:.2f} N·m</span>
    <br>
    <span style="font-size: 2rem; color: #666;">({torque_final*0.73756:.2f} lb·ft)</span>
</div>
""", unsafe_allow_html=True)

st.subheader("📝 Resumen de Diseño")
st.markdown(f"""
<div class="theory-box">
    <strong>Análisis Cinemático:</strong><br>
    - Sustrato: <strong>{tipo_mat}</strong> (Fy = {fy_s} MPa)<br>
    - Factor de Fricción K: <strong>{k_val}</strong> ({k_opt})<br>
    - Adición por Nyloc: <strong>{t_nylon} N·m</strong><br><br>
    <em>Nota: El valor de K influye en un 90% en la precisión de la precarga. En sustratos de aluminio, 
    la falta de lubricante anti-seize puede llevar a lecturas de torque falsas por fricción excesiva.</em>
</div>
""", unsafe_allow_html=True)