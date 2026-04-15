# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import base64
import os
from fpdf import FPDF
import datetime

# =================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS EXTENDIDOS
# =================================================================
st.set_page_config(
    page_title="Torque de Pernos de Alta Precisión | Mauricio Riquelme Alvarado",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Contenedores de Métricas */
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #e9ecef;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    /* Caja de Resultado Principal */
    .classification-box {
        background-color: #f8f9fa;
        padding: 30px;
        border: 2px solid #003366;
        border-radius: 15px;
        margin-top: 20px;
        margin-bottom: 30px;
        text-align: center;
    }
    /* Cuadros de Teoría e Ingeniería */
    .theory-box {
        background-color: #ffffff;
        padding: 25px;
        border-left: 8px solid #003366;
        border-radius: 8px;
        font-size: 1rem;
        line-height: 1.6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    /* Alertas de Seguridad */
    .warning-box {
        background-color: #fff3cd;
        padding: 20px;
        border-left: 8px solid #ffc107;
        border-radius: 8px;
        color: #856404;
        font-weight: 500;
        margin-bottom: 25px;
    }
    .danger-box {
        background-color: #f8d7da;
        padding: 20px;
        border-left: 8px solid #dc3545;
        border-radius: 8px;
        color: #721c24;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. CONSTANTES E INGENIERÍA DE MATERIALES (BASE DE DATOS)
# =================================================================

# Datos de Pernos UNC (Diámetro d [mm], Hilos por pulgada [n], Diámetro de contacto de golilla [dw mm])
# dw basado en estándar ASME B18.22.1 para golillas planas tipo Narrow/Regular
PERNOS_DATABASE = {
    "1/4\"-20 UNC": {"d": 6.35, "n": 20, "dw": 15.8},
    "5/16\"-18 UNC": {"d": 7.94, "n": 18, "dw": 17.5},
    "3/8\"-16 UNC": {"d": 9.525, "n": 16, "dw": 20.6},
    "1/2\"-13 UNC": {"d": 12.70, "n": 13, "dw": 27.0},
    "5/8\"-11 UNC": {"d": 15.875, "n": 11, "dw": 33.3},
    "3/4\"-10 UNC": {"d": 19.05, "n": 10, "dw": 37.3}
}

FACTORES_K = {
    "Acero Inoxidable 304/316 con Anti-Seize (Níquel/Cerámica)": 0.15,
    "Acero Zincado / Galvanizado en caliente (Seco)": 0.20,
    "Acero Negro (Aceitado de fábrica)": 0.18,
    "Acero Inoxidable Seco (Riesgo Crítico de Galling)": 0.30,
    "Cadmiado / Lubricación Especial": 0.12
}

ALUMINIO_DATABASE = {
    "AA6063-T5 (Sustrato estándar Fachadas)": {"fy": 110.0, "desc": "Baja resistencia, requiere precaución extrema."},
    "AA6063-T6 (Sustrato Truebond / Campus Santander)": {"fy": 170.0, "desc": "Resistencia media, estándar de ingeniería."},
    "AA6061-T6 (Sustrato Estructural de Alta Resistencia)": {"fy": 235.0, "desc": "Alta resistencia mecánica."},
    "Personalizado (Ingresar valor manual)": {"fy": 0.0, "desc": "Definido por el usuario."}
}

# =================================================================
# 3. BARRA LATERAL (ENTRADA DE DATOS DINÁMICA)
# =================================================================
st.sidebar.image("https://www.truebond.cl/wp-content/uploads/2021/05/logo-truebond.png", width=200) # Simulación de logo
st.sidebar.title("Configuración Técnica")

st.sidebar.markdown("---")
st.sidebar.subheader("📌 Selección del Perno")
perno_key = st.sidebar.selectbox("Designación de Diámetro", list(PERNOS_DATABASE.keys()), index=3)
material_perno = st.sidebar.selectbox("Material del Perno", ["Inox 304 (A2-70)", "Inox 316 (A4-80)", "Grado 5", "Grado 8"])

# Lógica de Fluencia del Perno
if "A2-70" in material_perno: fy_p = 450.0
elif "A4-80" in material_perno: fy_p = 600.0
elif "Grado 5" in material_perno: fy_p = 635.0
else: fy_p = 900.0

st.sidebar.markdown("---")
st.sidebar.subheader("🏗️ Propiedades del Sustrato")
tipo_mat = st.sidebar.radio("Tipo de Material Base", ["Aluminio", "Acero Estructural"])

if tipo_mat == "Aluminio":
    aleacion_sel = st.sidebar.selectbox("Aleación Específica", list(ALUMINIO_DATABASE.keys()), index=1)
    if "Personalizado" in aleacion_sel:
        fy_s = st.sidebar.number_input("Fluencia del Aluminio (MPa)", value=170.0)
    else:
        fy_s = ALUMINIO_DATABASE[aleacion_sel]["fy"]
    limit_aplast = 0.90 # Factor de seguridad para evitar flujo plástico en la cara de apoyo
else:
    fy_s = st.sidebar.number_input("Fluencia del Acero (MPa)", value=250.0)
    limit_aplast = 1.0

st.sidebar.markdown("---")
st.sidebar.subheader("🧪 Condiciones de Montaje")
k_sel = st.sidebar.selectbox("Estado de Superficie (K)", list(FACTORES_K.keys()))
k_value = FACTORES_K[k_sel]

tuerca_nyloc = st.sidebar.checkbox("¿Usa Tuerca con Seguro de Nylon?", value=True)
porcentaje_utilizacion = st.sidebar.slider("Nivel de Precarga Deseada (% de Fy perno)", 30, 90, 70)

# =================================================================
# 4. MOTOR DE CÁLCULO (SINE RECORTE)
# =================================================================

# Recuperar datos geométricos
d = PERNOS_DATABASE[perno_key]["d"]
n = PERNOS_DATABASE[perno_key]["n"]
dw = PERNOS_DATABASE[perno_key]["dw"]
p = 25.4 / n # Paso en mm

# A. Área de Tensión (Tensile Stress Area) - Fórmula AISC/ASME
As = 0.7854 * (d - (0.9382 * p))**2

# B. Área de Aplastamiento (Bearing Area)
# El área que realmente transmite la carga al aluminio
Ab = (np.pi / 4) * (dw**2 - d**2)

# C. Cálculo de Fuerzas Críticas
# 1. Fuerza máxima que aguanta el perno al % de fluencia elegido
F_perno_max = (fy_p * (porcentaje_utilizacion / 100.0)) * As

# 2. Fuerza máxima que aguanta el sustrato (Aluminio) antes de deformarse bajo la golilla
F_sustrato_max = (fy_s * limit_aplast) * Ab

# D. Selección de la Fuerza de Diseño (Pre-carga Fi)
# Lógica de seguridad: No podemos apretar más de lo que el aluminio resiste
controla_sustrato = False
if F_sustrato_max < F_perno_max:
    Fi = F_sustrato_max
    controla_sustrato = True
else:
    Fi = F_perno_max

# E. Cálculo del Torque Base (Fórmula de Torsión de Short)
# T = K * d * Fi
torque_base_nm = k_value * (d / 1000.0) * Fi

# F. Adición de Torque de Prevalencia (Nyloc)
# Según torque.py previo y estándares industriales para 1/2"
t_nylon = 0.0
if tuerca_nyloc:
    if d <= 8: t_nylon = 1.2
    elif d <= 13: t_nylon = 2.5
    else: t_nylon = 4.5

torque_total_nm = torque_base_nm + t_nylon
torque_total_lbft = torque_total_nm * 0.73756

# =================================================================
# 5. INTERFAZ DE RESULTADOS (DESPLIEGUE COMPLETO)
# =================================================================

st.title("🔩 Calculador de Torque de Ingeniería")
st.caption(f"Revisión Técnica: {datetime.date.today().strftime('%d/%m/%Y')} | Campus Santander")

# Columnas de Métricas de Ingeniería
m1, m2, m3, m4 = st.columns(4)
m1.metric("Área Tensión ($A_s$)", f"{As:.2f} mm²")
m2.metric("Área Apoyo ($A_b$)", f"{Ab:.2f} mm²")
m3.metric("Fuerza de Cierre ($F_i$)", f"{Fi/1000:.2f} kN")
m4.metric("Presión de Contacto", f"{Fi/Ab:.1f} MPa")

# Alertas de Control de Ingeniería
if controla_sustrato:
    st.markdown(f"""
    <div class="warning-box">
        ⚠️ <strong>CONTROL POR APLASTAMIENTO DE SUSTRATO:</strong><br>
        La precarga calculada para el perno superaba la capacidad de soporte del aluminio ({fy_s} MPa). 
        El sistema ha ajustado la fuerza de cierre automáticamente para proteger la integridad del perfil 
        y evitar que la golilla se hunda en el material.
    </div>
    """, unsafe_allow_html=True)

if k_value >= 0.30:
    st.markdown(f"""
    <div class="danger-box">
        🚫 <strong>RIESGO CRÍTICO DE GALLING (GRIPADO):</strong><br>
        Está intentando instalar Acero Inoxidable en seco. Existe un 90% de probabilidad de que el perno se 
        suelde en frío antes de alcanzar el torque nominal. <strong>USE ANTI-SEIZE.</strong>
    </div>
    """, unsafe_allow_html=True)

# RESULTADO PRINCIPAL
st.markdown(f"""
<div class="classification-box">
    <h1 style="color: #003366; font-size: 1.2rem; margin-bottom: 10px;">TORQUE NOMINAL RECOMENDADO</h1>
    <span style="font-size: 4rem; font-weight: 800; color: #003366;">{torque_total_nm:.1f} N·m</span>
    <br>
    <span style="font-size: 2rem; font-weight: 400; color: #666;">({torque_total_lbft:.1f} lb·ft)</span>
</div>
""", unsafe_allow_html=True)

# Sección de Fundamentos y Notas de Terreno
c1, c2 = st.columns(2)

with c1:
    st.subheader("📚 Memoria de Cálculo")
    st.markdown(f"""
    <div class="theory-box">
        <strong>Física del Apriete:</strong><br>
        El torque aplicado se distribuye en:<br>
        - 10% Tensión axial del perno (Precarga útil).<br>
        - 40% Fricción en los hilos de la rosca.<br>
        - 50% Fricción bajo la cabeza/tuerca.<br><br>
        <strong>Factor K ({k_value}):</strong> Determina cuánta fuerza se pierde en fricción. 
        Un cambio en la lubricación altera el resultado radicalmente.
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.subheader("🛠️ Instrucciones de Instalación")
    st.markdown(f"""
    <div class="theory-box">
        <strong>Para el Instalador (Joel Valenzuela):</strong><br>
        1. <strong>Lubricación:</strong> Aplique Anti-Seize solo en la rosca, no en la cara del nylon.<br>
        2. <strong>Velocidad:</strong> No use llaves de impacto. El calor funde el nylon y altera el torque.<br>
        3. <strong>Golillas:</strong> Verifique que la golilla sea de {dw} mm de diámetro exterior para asegurar 
        que la presión sobre el aluminio sea de {Fi/Ab:.1f} MPa.
    </div>
    """, unsafe_allow_html=True)

# Pie de página técnico
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; font-size: 0.8rem; color: #999;">
    Ingeniería Delegada Truebond | Desarrollado por Mauricio Riquelme Alvarado | Proyecto Campus Santander<br>
    Basado en Normas: AISC 360-16, VDI 2230, NCh 3357.
</div>
""", unsafe_allow_html=True)