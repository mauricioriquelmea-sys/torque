# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import base64
import os
from fpdf import FPDF

# =================================================================
# 1. CONFIGURACIÓN Y ESTILO
# =================================================================
st.set_page_config(page_title="Torque de Pernos | Structural Lab", layout="wide")

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
    </style>
    """, unsafe_allow_html=True)

if os.path.exists("Logo.png"):
    with open("Logo.png", "rb") as f:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{base64.b64encode(f.read()).decode()}" width="380"></div>', unsafe_allow_html=True)

st.title("🔩 Calculador de Torque de Pernos")
st.caption("Ingeniería de Conexiones | Proyectos Estructurales EIRL")

# =================================================================
# 2. BASE DE DATOS TÉCNICA (Mejorada con Áreas de Tensión)
# =================================================================

# Datos de pernos: Nombre, Diámetro Nominal (in), hilos por pulgada (n)
PERNOS = {
    "1/4\"": (0.250, 20), "3/8\"": (0.375, 16), "1/2\"": (0.500, 13),
    "5/8\"": (0.625, 11), "3/4\"": (0.750, 10), "7/8\"": (0.875, 9),
    "1\"": (1.000, 8), "1 1/8\"": (1.125, 7), "1 1/4\"": (1.250, 7),
    "1 3/8\"": (1.375, 6), "1 1/2\"": (1.500, 6), "2\"": (2.000, 4.5)
}

# Coeficientes de Fricción K (Basado en tu Select Case y eFunda)
K_FACTORS = {
    "Perno Negro / Sin lubricar": 0.30,
    "Zincado / Galvanizado": 0.20,
    "Lubricado (Aceite ligero)": 0.18,
    "Cadmiado": 0.16,
    "Acero Inoxidable": 0.15
}

# =================================================================
# 3. INTERFAZ DE ENTRADA
# =================================================================
col_in1, col_in2 = st.sidebar.columns(2)
st.sidebar.header("⚙️ Parámetros de la Conexión")

perno_sel = st.sidebar.selectbox("Diámetro Nominal del Perno", list(PERNOS.keys()), index=2)
condicion = st.sidebar.selectbox("Condición de la Superficie (K)", list(K_FACTORS.keys()), index=1)
fy_input = st.sidebar.number_input("Fluencia del Acero Fy (kN/cm²)", value=25.0, help="Ej: A325 ~ 63, A36 ~ 25")

# =================================================================
# 4. MOTOR DE CÁLCULO (Lógica eFunda + Tu VB)
# =================================================================

D = PERNOS[perno_sel][0]  # Diámetro en pulgadas
n = PERNOS[perno_sel][1]  # Hilos por pulgada
K = K_FACTORS[condicion]

# Cálculo del Área de Tensión As (Pulgadas cuadradas) - Método eFunda
# As = 0.7854 * (D - 0.9743/n)^2
As = 0.7854 * (D - 0.9743 / n)**2

# Conversión de Fy a psi (Para trabajar en unidades imperiales precarga)
# 1 kN/cm2 = 1450.38 psi
Fy_psi = fy_input * 1450.38

# Precarga de Diseño Fi (75% de la carga de prueba o ~60-70% de Fy)
# Tu lógica: Fi = 0.9 * (0.8 * F) * Ap
Fi = 0.75 * Fy_psi * As  # Precarga recomendada en libras (lb)

# Torque (T = K * D * Fi)
Torque_lb_in = K * D * Fi
Torque_lb_ft = Torque_lb_in / 12
Torque_N_m = Torque_lb_ft * 1.35582

# =================================================================
# 5. DESPLIEGUE DE RESULTADOS
# =================================================================

st.markdown("### 📊 Resultados del Análisis")

col_res1, col_res2, col_res3 = st.columns(3)
with col_res1:
    st.metric("Área de Tensión ($A_s$)", f"{As:.4f} in²")
with col_res2:
    st.metric("Precarga ($F_i$)", f"{Fi/1000:.2f} kips")
with col_res3:
    st.metric("Factor K", f"{K:.2f}")

st.markdown(f"""
<div class="classification-box">
    <h3 style="color: #003366; margin-top: 0;">🔧 Torque de Apriete Sugerido</h3>
    <p style="font-size: 2.2em; margin-bottom: 0;">
        <strong>{Torque_N_m:.2f} N·m</strong>
    </p>
    <p style="font-size: 1.5em; color: #555;">
        <strong>{Torque_lb_ft:.2f} lb·ft</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# =================================================================
# 6. GENERADOR DE PDF
# =================================================================
def generar_pdf_torque():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Memoria de Cálculo: Torque de Conexiones", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, "Proyectos Estructurales | Mauricio Riquelme", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_fill_color(230, 240, 255)
    pdf.cell(0, 10, " 1. DATOS DEL PERNO", ln=True, fill=True)
    pdf.cell(0, 8, f" Diametro Nominal: {perno_sel} | Hilos/pulg: {n}", ln=True)
    pdf.cell(0, 8, f" Condicion: {condicion} (K={K})", ln=True)
    pdf.cell(0, 8, f" Fluencia Fy: {fy_input} kN/cm2", ln=True)
    
    pdf.ln(5)
    pdf.cell(0, 10, " 2. CALCULOS INTERMEDIOS", ln=True, fill=True)
    pdf.cell(0, 8, f" Area de Tension As: {As:.4f} in2", ln=True)
    pdf.cell(0, 8, f" Precarga Fi (75% Fy): {Fi:.2f} lb", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, " 3. TORQUE FINAL DE DISENO", ln=True, fill=True)
    pdf.cell(0, 12, f" TORQUE: {Torque_N_m:.2f} N-m ({Torque_lb_ft:.2f} lb-ft)", ln=True)
    
    return pdf.output()

# Botón PDF en Sidebar
st.sidebar.markdown("---")
if st.sidebar.button("📄 Generar Memoria PDF"):
    pdf_bytes = generar_pdf_torque()
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="Memoria_Torque.pdf" class="main-btn">📥 Descargar Reporte</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)

st.markdown("---")
st.info("💡 **Nota Teórica:** Este cálculo asume pernos de serie gruesa (UNC). La precarga se calcula al 75% de la tensión de fluencia para asegurar que el perno permanezca en rango elástico durante el apriete.")