import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
import io
import os

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Labo GBM Pro", layout="wide")

if 'mesures' not in st.session_state:
    st.session_state.mesures = []

# --- FONCTION MAGIQUE : RENDU "STYLE LIVRE" ---
def generer_image_formule(texte_formule, nom_fichier):
    """ Crée une image haute qualité de la formule comme dans un livre """
    fig = plt.figure(figsize=(6, 1))
    plt.axis('off')
    # Utilisation du moteur de rendu mathématique de Matplotlib
    plt.text(0.5, 0.5, texte_formule, size=22, ha='center', va='center', fontfamily='serif')
    plt.savefig(nom_fichier, bbox_inches='tight', transparent=True, dpi=300)
    plt.close(fig)

# --- GÉNÉRATEUR DE RAPPORT PDF ---
def generer_pdf(mode, r_val, c_val, fc_val, df):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. En-tête pro
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RAPPORT DE TRAVAUX PRATIQUES : FILTRES", ln=True, align='C')
    pdf.ln(10)

    # 2. Paramètres
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "I. DONNEES DU CIRCUIT", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 7, f"Type de filtre : {mode}", ln=True)
    pdf.cell(0, 7, f"Resistance (R) : {r_val} Ohms", ln=True)
    pdf.cell(0, 7, f"Condensateur (C) : {c_val*1e6:.2f} uF", ln=True)
    pdf.cell(0, 7, f"Frequence de coupure calculee : {fc_val:.2f} Hz", ln=True)
    pdf.ln(10)

    # 3. Formules "Style Livre"
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "II. FORMULES THEORIQUES (MANUEL)", ln=True)
    pdf.ln(5)

    if "Bas" in mode:
        f_gain = r"$G_{dB} = 20 \log_{10} \left( \frac{1}{\sqrt{1 + \left(\frac{f}{f_c}\right)^2}} \right)$"
        f_phase = r"$\phi = -\arctan\left(\frac{f}{f_c}\right) \cdot \frac{180}{\pi}$"
    else:
        f_gain = r"$G_{dB} = 20 \log_{10} \left( \frac{\frac{f}{f_c}}{\sqrt{1 + \left(\frac{f}{f_c}\right)^2}} \right)$"
        f_phase = r"$\phi = 90^\circ - \arctan\left(\frac{f}{f_c}\right) \cdot \frac{180}{\pi}$"

    # On transforme ces codes en images "livre"
    generer_image_formule(f_gain, "img_gain.png")
    generer_image_formule(f_phase, "img_phase.png")
    
    # Insertion des images dans le PDF
    pdf.image("img_gain.png", x=20, w=110)
    pdf.ln(5)
    pdf.image("img_phase.png", x=20, w=110)
    pdf.ln(15)

    # 4. Graphique de Bode
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "III. ANALYSE GRAPHIQUE", ln=True)
    
    f_th = np.logspace(0, 6, 200)
    tau = r_val * c_val
    omega_th = 2 * np.pi * f_th
    H_th = 1/(1+1j*omega_th*tau) if "Bas" in mode else (1j*omega_th*tau)/(1+1j*omega_th*tau)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))
    ax1.semilogx(f_th, 20*np.log10(np.abs(H_th) + 1e-12), color='blue')
    ax1.semilogx(df['f'], df['g'], 'ro')
    ax1.set_ylabel('Gain (dB)')
    ax1.grid(True, which="both")
    
    ax2.semilogx(f_th, np.degrees(np.angle(H_th)), color='green')
    ax2.semilogx(df['f'], df['p'], 'ro')
    ax2.set_ylabel('Phase (Deg)')
    ax2.grid(True, which="both")

    plt.savefig("temp_bode.png", dpi=100)
    plt.close()
    pdf.image("temp_bode.png", x=15, y=130, w=180)
    
    output = pdf.output(dest='S')
    # Nettoyage
    for f in ["img_gain.png", "img_phase.png", "temp_bode.png"]:
        if os.path.exists(f): os.remove(f)
        
    return output.encode('latin-1') if isinstance(output, str) else output

# --- INTERFACE ---
st.title("⚡ Labo Electronique : Rapport Qualité Livre")

mode = st.sidebar.selectbox("Filtre", ["Passe-Bas (RC)", "Passe-Haut (CR)"])
R = st.sidebar.number_input("R (Ohms)", value=1000)
C = st.sidebar.number_input("C (uF)", value=0.1)
fc = 1 / (2 * np.pi * R * C * 1e-6)

if st.button("📥 Enregistrer Mesure"):
    w = 2*np.pi*fc
    tau = R*C*1e-6
    H = 1/(1+1j*w*tau) if "Bas" in mode else (1j*w*tau)/(1+1j*w*tau)
    st.session_state.mesures.append({"f": fc, "g": 20*np.log10(np.abs(H)), "p": np.degrees(np.angle(H))})
    st.success("Point sauvegardé")

if st.session_state.mesures:
    df = pd.DataFrame(st.session_state.mesures)
    st.table(df)
    pdf_bytes = generer_pdf(mode, R, C * 1e-6, fc, df)
    st.download_button("💾 Telecharger le Rapport (Style Livre)", pdf_bytes, "Rapport_Pro.pdf")
