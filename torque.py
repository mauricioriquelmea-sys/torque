# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import base64
import os
from fpdf import FPDF

# =================================================================
# 1. CONFIGURACIÓN Y ESTILO CORPORATIVO
# =================================================================
st.set_page_config(page_title="Torque de Pernos | Mauricio Riquelme", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; }
    .main-btn {
        display: flex; align-items: center; justify-content: center;
        background-color: #003366; color: white !important; padding: 12px 10px;
        text-decoration: none !important; border-radius: 8px; font-weight: bold; width: 100%;
    }
    .classification-box {
        background-color: #f1f8ff; padding: 20px; border: 1px solid #c8e1ff;
        border-radius: 5px; margin-bottom: 25px;
    }
    .theory-box {
        background-color: #fdfdfe; padding: 20px; border-left: 5px solid #ff4b4b;
        border-radius: 5px; font-size: 0.95rem; line-height: 1.5;
    }
    </style>
    """, unsafe_allow_html=True)

if os.path.exists("Logo.png"):
    with open("Logo.png", "rb") as f:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{base64.b64encode(f.read()).decode()}" width="380"></div>', unsafe_allow_html=True)

st.title("🔩 Calculador de Torque de Pernos")
st.caption("Proyectos Estructurales EIRL | Ingeniería de Conexiones de Precisión")

# =================================================================
# 2. BASE DE DATOS TÉCNICA
# =================================================================

# Datos de pernos (Sistema Imperial para selección, cálculo convertido a métrico)
# Nombre: (Diámetro d en mm, hilos por pulgada n)
PERNOS_INFO = {
    "1/4\"": (6.35, 20), "3/8\"": (9.525, 16), "1/2\"": (12.70, 13),
    "5/8\"": (15.875, 11), "3/4\"": (19.05, 10), "7/8\"": (22.225, 9),
    "1\"": (25.40, 8), "1 1/8\"": (28.575, 7), "1 1/4\"": (31.75, 7),
    "1 1/2\"": (38.10, 6), "2\"": (50.80, 4.5)
}

# Coeficientes de Fricción K
K_FACTORS = {
    "Perno Negro (Sin lubricar)": 0.30,
    "Zincado / Galvanizado": 0.20,
    "Lubricado (Aceite ligero)": 0.18,
    "Cadmiado": 0.16,
    "Acero Inoxidable": 0.15
}

# =================================================================
# 3. INTERFAZ LATERAL
# =================================================================
st.sidebar.header("⚙️ Parámetros de Diseño")
perno_sel = st.sidebar.selectbox("Diámetro Nominal del Perno", list(PERNOS_INFO.keys()), index=2)
condicion = st.sidebar.selectbox("Condición de Superficie (Factor K)", list(K_FACTORS.keys()), index=1)
fy_mpa = st.sidebar.number_input("Tensión de Fluencia del Perno (MPa)", value=250.0, step=10.0)
porcentaje_f = st.sidebar.slider("Precarga deseada (% de Fy)", 50, 90, 75)

# =================================================================
# 4. MOTOR DE CÁLCULO MÉTRICO
# =================================================================

d_mm, n_in = PERNOS_INFO[perno_sel]
K = K_FACTORS[condicion]

# 1. Área de Esfuerzo de Tensión As (convertida a cm2)
# Fórmula: As = 0.7854 * (d_mm - 0.9382 * p_mm)^2 donde p es el paso
paso_mm = 25.4 / n_in
As_mm2 = 0.7854 * (d_mm - (0.9382 * paso_mm))**2
As_cm2 = As_mm2 / 100

# 2. Precarga Fi (MPa)
# Fi_mpa es la tensión aplicada. La Fuerza Fi total es Fi_mpa * As
Fi_tension_mpa = fy_mpa * (porcentaje_f / 100)
Fi_fuerza_N = Fi_tension_mpa * As_mm2 # Newton

# 3. Torque Final (T = K * D * Fi)
# D en metros, Fi en Newton -> T en N-m
Torque_Nm = K * (d_mm / 1000) * Fi_fuerza_N
Torque_lbft = Torque_Nm / 1.3558179

# =================================================================
# 5. DESPLIEGUE DE RESULTADOS
# =================================================================

st.markdown("### 📊 Resultados del Análisis")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Área de Tensión ($A_s$)", f"{As_cm2:.4f} cm²")
with col2:
    st.metric("Tensión de Precarga", f"{Fi_tension_mpa:.1f} MPa")
with col3:
    st.metric("Factor K (Fricción)", f"{K:.2f}")

st.markdown(f"""
<div class="classification-box">
    <h3 style="color: #003366; margin-top: 0;">🔧 Torque de Apriete Recomendado</h3>
    <p style="font-size: 2.5em; margin-bottom: 0;">
        <strong>{Torque_Nm:.2f} N·m</strong>
    </p>
    <p style="font-size: 1.5em; color: #555;">
        <strong>{Torque_lbft:.2f} lbf·ft</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# Nota Explicativa sobre Factor K
st.markdown("### 📚 Nota Técnica: El Factor de Corrección de Torque (K)")
st.markdown(f"""
<div class="theory-box">
    La relación entre el torque aplicado y la tensión (precarga) resultante en un perno no es una ciencia exacta, 
    ya que aproximadamente el <strong>90% del torque se pierde en vencer la fricción</strong>:
    <ul>
        <li><strong>50%</strong> de la fricción ocurre bajo la cabeza del perno o la cara de la tuerca.</li>
        <li><strong>40%</strong> de la fricción ocurre en los hilos de la rosca.</li>
        <li>Sólo el <strong>10%</strong> restante se convierte efectivamente en precarga útil.</li>
    </ul>
    El <strong>Factor K</strong> es un coeficiente empírico que agrupa todas estas variables de fricción. Un perno seco 
    (K ≈ 0.30) requiere mucho más torque para lograr la misma precarga que un perno lubricado (K ≈ 0.18). 
    <em>El uso de lubricantes reduce la dispersión y permite un apriete mucho más controlado.</em>
</div>
""", unsafe_allow_html=True)

# =================================================================
# 6. GENERADOR DE PDF
# =================================================================
def generar_pdf_torque():
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("Logo.png"): pdf.image("Logo.png", x=10, y=8, w=33)
    pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, "Memoria de Calculo: Torque de Pernos", ln=True, align='C')
    pdf.set_font("Arial", '', 10); pdf.cell(0, 10, "Proyectos Estructurales | Mauricio Riquelme", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, " 1. PARAMETROS DE ENTRADA", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f" Perno: {perno_sel} | Fluencia Fy: {fy_mpa} MPa | Precarga: {porcentaje_f}%", ln=True)
    pdf.cell(0, 8, f" Condicion: {condicion} | Factor K: {K}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, " 2. RESULTADOS METRICOS", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f" Area de Tension (As): {As_cm2:.4f} cm2", ln=True)
    pdf.cell(0, 8, f" Tension de Precarga (sigma_i): {Fi_tension_mpa:.2f} MPa", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, " 3. TORQUE FINAL DE DISENO", ln=True, fill=True)
    pdf.cell(0, 12, f" TORQUE SUGERIDO: {Torque_Nm:.2f} N-m / {Torque_lbft:.2f} lb-ft", ln=True)
    
    pdf.set_y(-30); pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Nota: Calculos basados en el metodo de Factor de Friccion K (ANSI/ASME).", align='C')
    return pdf.output()

# Botón PDF en Sidebar
st.sidebar.markdown("---")
try:
    pdf_bytes = generar_pdf_torque()
    b64 = base64.b64encode(pdf_bytes).decode()
    st.sidebar.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Memoria_Torque_Metrico.pdf" class="main-btn">📥 DESCARGAR MEMORIA PDF</a>', unsafe_allow_html=True)
except Exception as e:
    st.sidebar.error(f"Error PDF: {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Mauricio Riquelme | Structural Lab <br> <em>'Programming is understanding'</em></div>", unsafe_allow_html=True)