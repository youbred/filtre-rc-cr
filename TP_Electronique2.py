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
st.sidebar.markdown("---")

if 'mesures' not in st.session_state:
    st.session_state.mesures = []

# --- FONCTION GÉNÉRATION PDF OPTIMISÉE (HYBRIDE & RAPIDE) ---
def generer_pdf(mode, r_val, c_val, fc_val, df):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Titre
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RAPPORT DE TP : FILTRES DU 1ER ORDRE", ln=True, align='C')
    pdf.ln(10)

    # 2. Paramètres du circuit
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "I. PARAMETRES ET FORMULES THEORIQUES", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 7, f"Type de filtre : {mode}", ln=True)
    pdf.cell(0, 7, f"Resistance (R) : {r_val} Ohms | Condensateur (C) : {c_val*1e6:.2f} uF", ln=True)
    pdf.cell(0, 7, f"Fréquence de coupure calculee (Fc) : {fc_val:.2f} Hz", ln=True)
    pdf.ln(5)

    # 3. Insertion des formules (Solution Hybride : Caractères Spéciaux)
    # Note : On utilise 'Times' et 'Italic' pour un rendu plus mathématique
    pdf.set_font("Times", 'I', 11)
    pdf.set_text_color(0, 51, 102) # Bleu foncé élégant
    
    if "Bas" in mode:
        # Utilisation de symboles Unicode pour √, ² et ϕ
        gain_str = "Gain (dB) : G = 20 . log10 [ 1 / sqrt( 1 + (f/fc)^2 ) ]"
        phase_str = "Phase (deg) : phi = -arctan( f/fc ) . (180/pi)"
    else:
        gain_str = "Gain (dB) : G = 20 . log10 [ (f/fc) / sqrt( 1 + (f/fc)^2 ) ]"
        phase_str = "Phase (deg) : phi = 90 - [ arctan( f/fc ) . (180/pi) ]"
    
    pdf.cell(0, 8, gain_str, ln=True)
    pdf.cell(0, 8, phase_str, ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)

    # 4. Graphique de Bode
    f_th = np.logspace(0, 6, 200) 
    tau = r_val * c_val
    omega_th = 2 * np.pi * f_th
    H_th = 1/(1+1j*omega_th*tau) if "Bas" in mode else (1j*omega_th*tau)/(1+1j*omega_th*tau)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))
    ax1.semilogx(f_th, 20*np.log10(np.abs(H_th) + 1e-12), color='gray', linestyle='--', alpha=0.6)
    ax1.semilogx(df['f'], df['g'], 'ro-', linewidth=2)
    ax1.set_ylabel('Gain (dB)')
    ax1.grid(True, which="both", linestyle=':', alpha=0.5)
    
    ax2.semilogx(f_th, np.degrees(np.angle(H_th)), color='gray', linestyle='--', alpha=0.6)
    ax2.semilogx(df['f'], df['p'], 'co-', linewidth=2)
    ax2.set_ylabel('Phase (Deg)')
    ax2.grid(True, which="both", linestyle=':', alpha=0.5)

    img_path = "temp_plot.png"
    plt.savefig(img_path, format='png', dpi=120) 
    plt.close()
    
    pdf.image(img_path, x=10, y=95, w=180) 
    
    output_str = pdf.output(dest='S')
    if os.path.exists(img_path): os.remove(img_path)
    
    # Encodage sécurisé pour éviter les erreurs de caractères
    if isinstance(output_str, str):
        return output_str.encode('latin-1', 'replace')
    return output_str

# --- INTERFACE STREAMLIT ---
st.title("⚡ Laboratoire Virtuel d'Électronique")

st.sidebar.header("⚙️ Configuration")
mode = st.sidebar.selectbox("Type de Filtre", ["Passe-Bas (RC)", "Passe-Haut (CR)"])
R = st.sidebar.number_input("R (Ohms)", value=1000, step=100)
C_uF = st.sidebar.number_input("C (uF)", value=0.1, step=0.01)

tau_val = R * (C_uF * 1e-6)
fc = 1 / (2 * np.pi * tau_val)
st.sidebar.metric("Fréquence de Coupure (Fc)", f"{fc:.2f} Hz")

if st.sidebar.button("🗑️ Réinitialiser les mesures"):
    st.session_state.mesures = []
    st.rerun()

tabs = st.tabs(["📚 THÉORIE", "🖥️ OSCILLOSCOPE", "📊 BODE & RAPPORT"])

with tabs[0]:
    st.header("Étude Théorique")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write(f"Analyse du filtre **{mode}**")
        st.latex(r"f_c = \frac{1}{2\pi RC}")
        st.info(f"Pour vos composants : Fc = {fc:.2f} Hz")
    with col_b:
        if "Bas" in mode:
            st.latex(r"G_{dB} = 20 \log_{10} \left( \frac{1}{\sqrt{1 + (f/f_c)^2}} \right)")
        else:
            st.latex(r"G_{dB} = 20 \log_{10} \left( \frac{f/f_c}{\sqrt{1 + (f/f_c)^2}} \right)")

with tabs[1]:
    st.header("Générateur de fonctions & Oscilloscope")
    f_in = st.number_input("Fréquence du GBF (Hz)", min_value=0.1, value=float(np.round(fc)), step=1.0)
    w_in = 2 * np.pi * f_in
    H_in = 1/(1+1j*w_in*tau_val) if "Bas" in mode else (1j*w_in*tau_val)/(1+1j*w_in*tau_val)
    t = np.linspace(0, 2/f_in if f_in > 0 else 1, 1000)
    ve = np.sin(w_in * t)
    vs = np.abs(H_in) * np.sin(w_in * t + np.angle(H_in))
    
    fig_scope = go.Figure()
    fig_scope.add_trace(go.Scatter(x=t*1e3, y=ve, name="Ve (V)", line=dict(color='yellow')))
    fig_scope.add_trace(go.Scatter(x=t*1e3, y=vs, name="Vs (V)", line=dict(color='cyan')))
    fig_scope.update_layout(template="plotly_dark", xaxis_title="Temps (ms)", yaxis_title="Tension (V)", height=400)
    st.plotly_chart(fig_scope, use_container_width=True)
    
    if st.button("📥 Enregistrer ce point de mesure"):
        st.session_state.mesures.append({"f": f_in, "g": 20*np.log10(np.abs(H_in) + 1e-12), "p": np.degrees(np.angle(H_in))})
        st.success(f"Point à {f_in} Hz enregistré !")

with tabs[2]:
    st.header("Diagramme de Bode")
    if st.session_state.mesures:
        df = pd.DataFrame(st.session_state.mesures).sort_values("f")
        st.table(df)
        try:
            pdf_bytes = generer_pdf(mode, R, C_uF*1e-6, fc, df)
            st.download_button("💾 Télécharger le Rapport PDF", pdf_bytes, "Rapport_TP.pdf")
        except Exception as e:
            st.error(f"Erreur PDF : {e}")
    else:
        st.warning("Aucune mesure enregistrée.")
