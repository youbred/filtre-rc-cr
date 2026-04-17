import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from fpdf import FPDF
import io
import matplotlib.pyplot as plt
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Labo Électronique Pro", layout="wide")

# --- SECTION CRÉDITS ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 👨‍🏫 Informations")
st.sidebar.info("""
**Réalisé par :** Youbi Ridha  
**Laboratoire :** GBM  
**Contact :** [youbiridha13@gmail.com](mailto:youbiridha13@gmail.com)
""")

if 'mesures' not in st.session_state:
    st.session_state.mesures = []

# --- FONCTION POUR TRANSFORMER LATEX EN IMAGE ---
def latex_to_image(formula, filename):
    fig = plt.figure(figsize=(6, 0.8))
    fig.text(0, 0.5, formula, fontsize=14, va='center')
    plt.savefig(filename, bbox_inches='tight', transparent=True, dpi=300)
    plt.close()

# --- FONCTION GÉNÉRATION PDF ---
def generer_pdf(mode, r_val, c_val, fc_val, df):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Titre
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RAPPORT DE TP : FILTRES DU 1ER ORDRE", ln=True, align='C')
    pdf.ln(10)

    # 2. Paramètres
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "I. PARAMETRES ET FORMULES THEORIQUES", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 7, f"Type de filtre : {mode}", ln=True)
    pdf.cell(0, 7, f"Resistance (R) : {r_val} Ohms | Condensateur (C) : {c_val*1e6:.2f} uF", ln=True)
    pdf.cell(0, 7, f"Frequence de coupure (Fc) : {fc_val:.2f} Hz", ln=True)
    pdf.ln(5)

    # 3. Formules en LaTeX (Image)
    if "Bas" in mode:
        f_gain = r"$G_{dB} = 20 \log_{10} \left( \frac{1}{\sqrt{1 + (f/f_c)^2}} \right)$"
        f_phase = r"$\phi = -\arctan(f/f_c) \cdot \frac{180}{\pi}$"
    else:
        f_gain = r"$G_{dB} = 20 \log_{10} \left( \frac{f/f_c}{\sqrt{1 + (f/f_c)^2}} \right)$"
        f_phase = r"$\phi = 90^\circ - \arctan(f/f_c) \cdot \frac{180}{\pi}$"
    
    latex_to_image(f_gain, "gain.png")
    latex_to_image(f_phase, "phase.png")
    
    pdf.image("gain.png", x=10, y=65, w=100)
    pdf.image("phase.png", x=10, y=75, w=100)
    pdf.ln(25)

    # 4. Graphiques de Bode
    f_th = np.logspace(0, 6, 500)
    tau = r_val * c_val
    omega_th = 2 * np.pi * f_th
    H_th = 1/(1+1j*omega_th*tau) if "Bas" in mode else (1j*omega_th*tau)/(1+1j*omega_th*tau)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))
    ax1.semilogx(f_th, 20*np.log10(np.abs(H_th) + 1e-12), color='gray', linestyle='--')
    ax1.semilogx(df['f'], df['g'], 'ro-')
    ax1.set_ylabel('Gain (dB)')
    ax1.grid(True, which="both")
    ax2.semilogx(f_th, np.degrees(np.angle(H_th)), color='gray', linestyle='--')
    ax2.semilogx(df['f'], df['p'], 'co-')
    ax2.set_ylabel('Phase (Deg)')
    ax2.grid(True, which="both")

    plt.savefig("bode_plot.png", format='png', dpi=300)
    plt.close()
    
    pdf.image("bode_plot.png", x=10, y=100, w=180) 
    
    output = pdf.output(dest='S')
    
    # Nettoyage
    for f in ["gain.png", "phase.png", "bode_plot.png"]:
        if os.path.exists(f): os.remove(f)
        
    return output.encode('latin-1') if isinstance(output, str) else output

# --- INTERFACE STREAMLIT (Reste identique) ---
st.title("⚡ Laboratoire Virtuel d'Électronique")
mode = st.sidebar.selectbox("Type de Filtre", ["Passe-Bas (RC)", "Passe-Haut (CR)"])
R = st.sidebar.number_input("R (Ohms)", value=1000)
C_uF = st.sidebar.number_input("C (uF)", value=0.1)
tau_val = R * (C_uF * 1e-6)
fc = 1 / (2 * np.pi * tau_val)
st.sidebar.metric("Fréquence de Coupure (Fc)", f"{fc:.2f} Hz")

tabs = st.tabs(["📚 THÉORIE", "🖥️ OSCILLOSCOPE", "📊 BODE & RAPPORT"])

with tabs[1]:
    f_in = st.number_input("Fréquence (Hz)", min_value=0.1, value=float(fc))
    w_in = 2 * np.pi * f_in
    H_in = 1/(1+1j*w_in*tau_val) if "Bas" in mode else (1j*w_in*tau_val)/(1+1j*w_in*tau_val)
    t = np.linspace(0, 2/f_in, 1000)
    ve, vs = np.sin(w_in*t), np.abs(H_in)*np.sin(w_in*t + np.angle(H_in))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t*1e3, y=ve, name="Ve", line=dict(color='yellow')))
    fig.add_trace(go.Scatter(x=t*1e3, y=vs, name="Vs", line=dict(color='cyan')))
    st.plotly_chart(fig, use_container_width=True)
    if st.button("📥 Enregistrer le point"):
        st.session_state.mesures.append({"f": f_in, "g": 20*np.log10(np.abs(H_in)+1e-12), "p": np.degrees(np.angle(H_in))})

with tabs[2]:
    if st.session_state.mesures:
        df = pd.DataFrame(st.session_state.mesures).sort_values("f")
        st.table(df)
        pdf_bytes = generer_pdf(mode, R, C_uF*1e-6, fc, df)
        st.download_button("💾 Télécharger le Rapport PDF", pdf_bytes, "Rapport_TP.pdf")
