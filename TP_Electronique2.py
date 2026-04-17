import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from fpdf import FPDF
import io
import matplotlib.pyplot as plt
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Labo Électronique Pro", layout="wide")

# --- CRÉDITS ---
st.sidebar.markdown("### 👨‍🏫 Informations")
st.sidebar.info("**Youbi Ridha** - Labo GBM")

if 'mesures' not in st.session_state:
    st.session_state.mesures = []

# --- FONCTION DE RENDU RAPIDE ---
def render_latex_fast(formula, filename):
    # Taille réduite pour plus de vitesse
    fig = plt.figure(figsize=(4, 0.6))
    plt.axis('off')
    plt.text(0.5, 0.5, formula, size=15, ha='center', va='center')
    # DPI réduit à 150 pour la vitesse (suffisant pour le PDF)
    plt.savefig(filename, bbox_inches='tight', transparent=True, dpi=150)
    plt.close(fig)

# --- GÉNÉRATION DU RAPPORT ---
def generer_pdf(mode, r_val, c_val, fc_val, df):
    pdf = FPDF()
    pdf.add_page()
    
    # Titre
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RAPPORT DE TP : FILTRES DU 1ER ORDRE", ln=True, align='C')
    pdf.ln(10)

    # Paramètres
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "I. PARAMETRES ET FORMULES", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 7, f"Filtre : {mode} | Fc = {fc_val:.2f} Hz", ln=True)
    pdf.ln(5)

    # Formules LaTeX
    if "Bas" in mode:
        g_tex = r"$G_{dB} = 20 \log_{10} \left( \frac{1}{\sqrt{1 + (f/f_c)^2}} \right)$"
        p_tex = r"$\phi = -\arctan(f/f_c) \cdot \frac{180}{\pi}$"
    else:
        g_tex = r"$G_{dB} = 20 \log_{10} \left( \frac{f/f_c}{\sqrt{1 + (f/f_c)^2}} \right)$"
        p_tex = r"$\phi = 90^\circ - \arctan(f/f_c) \cdot \frac{180}{\pi}$"

    render_latex_fast(g_tex, "g.png")
    render_latex_fast(p_tex, "p.png")
    pdf.image("g.png", x=15, w=90)
    pdf.image("p.png", x=15, w=90)
    pdf.ln(5)

    # Graphique de Bode (Optimisé)
    f_th = np.logspace(0, 6, 200) # 200 points au lieu de 500 pour aller plus vite
    tau = r_val * c_val
    omega_th = 2 * np.pi * f_th
    H_th = 1/(1+1j*omega_th*tau) if "Bas" in mode else (1j*omega_th*tau)/(1+1j*omega_th*tau)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 9))
    ax1.semilogx(f_th, 20*np.log10(np.abs(H_th) + 1e-12), color='gray', alpha=0.5)
    ax1.semilogx(df['f'], df['g'], 'ro-')
    ax1.set_ylabel('Gain (dB)')
    ax1.grid(True, which="both", alpha=0.3)
    
    ax2.semilogx(f_th, np.degrees(np.angle(H_th)), color='gray', alpha=0.5)
    ax2.semilogx(df['f'], df['p'], 'co-')
    ax2.set_ylabel('Phase (Deg)')
    ax2.grid(True, which="both", alpha=0.3)

    plt.savefig("b.png", dpi=150)
    plt.close()
    pdf.image("b.png", x=15, y=100, w=170)
    
    output = pdf.output(dest='S')
    
    # Nettoyage
    for f in ["g.png", "p.png", "b.png"]:
        if os.path.exists(f): os.remove(f)
        
    return output.encode('latin-1') if isinstance(output, str) else output

# --- INTERFACE ---
st.title("⚡ Laboratoire Virtuel")

mode = st.sidebar.selectbox("Filtre", ["Passe-Bas (RC)", "Passe-Haut (CR)"])
R = st.sidebar.number_input("R (Ohms)", value=1000)
C_uF = st.sidebar.number_input("C (uF)", value=0.1)
fc = 1 / (2 * np.pi * R * C_uF * 1e-6)

tab1, tab2, tab3 = st.tabs(["📚 Théorie", "🖥️ Scope", "📊 Rapport"])

with tab1:
    st.latex(r"G_{dB} = 20 \log_{10} \left( |H(j\omega)| \right)")

with tab2:
    f_in = st.number_input("Fréquence (Hz)", value=float(fc))
    # Simulation simplifiée
    t = np.linspace(0, 2/f_in, 500)
    w = 2*np.pi*f_in
    tau = R*C_uF*1e-6
    H = 1/(1+1j*w*tau) if "Bas" in mode else (1j*w*tau)/(1+1j*w*tau)
    ve, vs = np.sin(w*t), np.abs(H)*np.sin(w*t + np.angle(H))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=ve, name="Ve"))
    fig.add_trace(go.Scatter(x=t, y=vs, name="Vs"))
    st.plotly_chart(fig, use_container_width=True)
    
    if st.button("Enregistrer"):
        st.session_state.mesures.append({"f": f_in, "g": 20*np.log10(np.abs(H)+1e-12), "p": np.degrees(np.angle(H))})

with tab3:
    if st.session_state.mesures:
        df = pd.DataFrame(st.session_state.mesures).sort_values("f")
        st.table(df)
        if st.button("Générer le PDF"):
            pdf_bytes = generer_pdf(mode, R, C_uF*1e-6, fc, df)
            st.download_button("💾 Télécharger", pdf_bytes, "Rapport.pdf")
