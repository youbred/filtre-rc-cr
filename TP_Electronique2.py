import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from fpdf import FPDF
import io
import matplotlib.pyplot as plt
import os

# --- CONFIGURATION MATPLOTLIB POUR ÉVITER L'ERREUR ---
import matplotlib
matplotlib.rcParams['mathtext.default'] = 'regular'

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

# --- FONCTION GÉNÉRATION PDF ---
def generer_pdf(mode, r_val, c_val, fc_val, df):
    pdf = FPDF()
    pdf.add_page()
    
    # Page 1 : Titre et Théorie
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RAPPORT DE TP : FILTRES DU 1ER ORDRE", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "I. ETUDE THEORIQUE", ln=True)
    pdf.set_font("Arial", size=10)
    theorie = (f"Circuit : {mode}\n"
               f"Resistance (R) : {r_val} Ohms\n"
               f"Condensateur (C) : {c_val*1e6:.2f} uF\n"
               f"Frequence de coupure calculee (Fc) : {fc_val:.2f} Hz")
    pdf.multi_cell(0, 6, theorie)
    pdf.ln(5)

    # Page 1 : Tableau de Mesures
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "II. TABLEAU DES RESULTATS EXPERIMENTAUX", ln=True)
    pdf.set_font("Arial", 'B', 8)
    
    w = 31.6
    headers = ["F (Hz)", "Ve (V)", "Vs (V)", "G (dB)", "Dt (ms)", "Phi (deg)"]
    for header in headers:
        pdf.cell(w, 8, header, border=1, align='C')
    pdf.ln()

    pdf.set_font("Arial", size=8)
    for _, row in df.iterrows():
        pdf.cell(w, 7, f"{row['f']:.1f}", border=1, align='C')
        pdf.cell(w, 7, f"{row['ve']:.1f}", border=1, align='C')
        pdf.cell(w, 7, f"{row['vs']:.3f}", border=1, align='C')
        pdf.cell(w, 7, f"{row['g']:.2f}", border=1, align='C')
        pdf.cell(w, 7, f"{row['dt']:.4f}", border=1, align='C')
        pdf.cell(w, 7, f"{row['p']:.1f}", border=1, align='C')
        pdf.ln()

    # --- SAUT DE PAGE POUR LES GRAPHIQUES ---
    pdf.add_page() 
    
    # Page 2 : Graphiques de Bode
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "III. DIAGRAMME DE BODE", ln=True)
    pdf.ln(5)
    
    f_th = np.logspace(0, 6, 500)
    tau = r_val * c_val
    omega_th = 2 * np.pi * f_th
    H_th = 1/(1+1j*omega_th*tau) if "Bas" in mode else (1j*omega_th*tau)/(1+1j*omega_th*tau)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 9))
    
    # Gain
    ax1.semilogx(f_th, 20*np.log10(np.abs(H_th) + 1e-12), color='gray', linestyle='--', label='Theorie')
    ax1.semilogx(df['f'], df['g'], 'ro-', label='Mesures')
    ax1.set_ylabel('Gain (dB)')
    ax1.grid(True, which="both")
    ax1.legend()
    
    # Phase
    ax2.semilogx(f_th, np.degrees(np.angle(H_th)), color='gray', linestyle='--')
    ax2.semilogx(df['f'], df['p'], 'co-', label='Mesures')
    ax2.set_ylabel('Phase (Deg)')
    ax2.set_xlabel('Frequence (Hz)')
    ax2.grid(True, which="both")

    img_path = "temp_pdf_plot.png"
    plt.tight_layout()
    plt.savefig(img_path, format='png', dpi=120)
    plt.close()
    
    pdf.image(img_path, x=15, w=180)
    
    output_str = pdf.output(dest='S')
    if os.path.exists(img_path): os.remove(img_path)
    
    return output_str.encode('latin-1') if isinstance(output_str, str) else output_str

# --- INTERFACE PRINCIPALE ---
st.title("⚡ Laboratoire Virtuel d'Électronique")

# Configuration Sidebar
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

# Onglets
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
            st.latex(r"H(j\omega) = \frac{1}{1 + jRC\omega}")
        else:
            st.latex(r"H(j\omega) = \frac{jRC\omega}{1 + jRC\omega}")

with tabs[1]:
    st.header("Générateur & Oscilloscope")
    f_in = st.number_input("Fréquence du GBF (Hz)", min_value=0.1, value=float(np.round(fc)), step=1.0)
    
    # Calculs avec Ve = 2V
    w_in = 2 * np.pi * f_in
    H_in = 1/(1+1j*w_in*tau_val) if "Bas" in mode else (1j*w_in*tau_val)/(1+1j*w_in*tau_val)
    
    ve_amp = 2.0 # Amplitude Entrée fixée à 2V
    vs_amp = ve_amp * np.abs(H_in)
    phi_deg = np.degrees(np.angle(H_in))
    dt_ms = (phi_deg / (360 * f_in)) * 1000 
    
    t = np.linspace(0, 2/f_in if f_in > 0 else 1, 1000)
    ve_wave = ve_amp * np.sin(w_in * t)
    vs_wave = vs_amp * np.sin(w_in * t + np.radians(phi_deg))
    
    fig_scope = go.Figure()
    fig_scope.add_trace(go.Scatter(x=t*1e3, y=ve_wave, name="Ve (V)", line=dict(color='yellow')))
    fig_scope.add_trace(go.Scatter(x=t*1e3, y=vs_wave, name="Vs (V)", line=dict(color='cyan')))
    fig_scope.update_layout(template="plotly_dark", xaxis_title="Temps (ms)", yaxis_title="Tension (V)", height=400)
    st.plotly_chart(fig_scope, use_container_width=True)
    
    if st.button("📥 Enregistrer ce point"):
        st.session_state.mesures.append({
            "f": f_in, "ve": ve_amp, "vs": vs_amp,
            "g": 20*np.log10(np.abs(H_in) + 1e-12), "dt": dt_ms, "p": phi_deg
        })
        st.success(f"Point {f_in} Hz enregistré !")

with tabs[2]:
    st.header("Résultats et Exportation")
    if st.session_state.mesures:
        df = pd.DataFrame(st.session_state.mesures).sort_values("f")
        
        st.subheader("Tableau de données")
        st.dataframe(df.style.format({
            'f': '{:.1f}', 've': '{:.1f}', 'vs': '{:.3f}', 
            'g': '{:.2f}', 'dt': '{:.4f}', 'p': '{:.1f}'
        }), use_container_width=True)
        
        try:
            pdf_bytes = generer_pdf(mode, R, C_uF*1e-6, fc, df)
            st.download_button(
                label="💾 Télécharger le Rapport Complet (PDF)",
                data=pdf_bytes,
                file_name="Rapport_TP_Electronique.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erreur lors de la préparation du PDF : {e}")
    else:
        st.warning("Prenez des mesures dans l'onglet OSCILLOSCOPE.")
