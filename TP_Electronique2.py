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

# --- SECTION CRÉDITS DANS LA BARRE LATÉRALE ---
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

# --- FONCTION GÉNÉRATION PDF CORRIGÉE (AVEC FICHIER TEMP) ---
def generer_pdf(mode, r_val, c_val, fc_val, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RAPPORT DE TP : FILTRES DU 1ER ORDRE", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "I. ETUDE THEORIQUE", ln=True)
    pdf.set_font("Arial", size=10)
    theorie = f"Circuit : {mode}\nResistance : {r_val} Ohms\nCondensateur : {c_val*1e6:.2f} uF\nFrequence de coupure calculee : {fc_val:.2f} Hz"
    pdf.multi_cell(0, 5, theorie)
    
    # Graphique pour le PDF
    f_th = np.logspace(0, 6, 500)
    tau = r_val * c_val
    # Calcul sécurisé pour éviter les divisions par zéro à basse fréquence
    omega_th = 2 * np.pi * f_th
    if "Bas" in mode:
        H_th = 1 / (1 + 1j * omega_th * tau)
    else:
        H_th = (1j * omega_th * tau) / (1 + 1j * omega_th * tau)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))
    ax1.semilogx(f_th, 20*np.log10(np.abs(H_th) + 1e-12), color='gray', linestyle='--')
    ax1.semilogx(df['f'], df['g'], 'ro-')
    ax1.set_ylabel('Gain (dB)')
    ax1.grid(True, which="both")
    
    ax2.semilogx(f_th, np.degrees(np.angle(H_th)), color='gray', linestyle='--')
    ax2.semilogx(df['f'], df['p'], 'co-')
    ax2.set_ylabel('Phase (Deg)')
    ax2.grid(True, which="both")

    # Utilisation d'un fichier temporaire pour éviter l'erreur rfind
    img_path = "temp_bode.png"
    plt.savefig(img_path, format='png')
    plt.close()
    
    pdf.image(img_path, x=10, y=80, w=180)
    
    # Nettoyage du fichier après inclusion
    output = pdf.output(dest='S')
    if os.path.exists(img_path):
        os.remove(img_path)
        
    return bytes(output)

# --- INTERFACE PRINCIPALE ---
st.title("⚡ Laboratoire Virtuel d'Électronique")

# --- PARAMÈTRES ---
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

# --- ONGLETS ---
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
    st.header("Générateur de fonctions & Oscilloscope")
    f_in = st.number_input("Fréquence du GBF (Hz)", min_value=0.1, value=float(np.round(fc)), step=1.0)
    
    w_in = 2 * np.pi * f_in
    H_in = 1/(1+1j*w_in*tau_val) if "Bas" in mode else (1j*w_in*tau_val)/(1+1j*w_in*tau_val)
    
    # Ajustement automatique de la fenêtre temporelle
    t = np.linspace(0, 2/f_in if f_in > 0 else 1, 1000)
    ve = np.sin(w_in * t)
    vs = np.abs(H_in) * np.sin(w_in * t + np.angle(H_in))
    
    fig_scope = go.Figure()
    fig_scope.add_trace(go.Scatter(x=t*1e3, y=ve, name="Entrée Ve (V)", line=dict(color='yellow')))
    fig_scope.add_trace(go.Scatter(x=t*1e3, y=vs, name="Sortie Vs (V)", line=dict(color='cyan')))
    fig_scope.update_layout(template="plotly_dark", xaxis_title="Temps (ms)", yaxis_title="Tension (V)", height=400)
    st.plotly_chart(fig_scope, use_container_width=True)
    
    if st.button("📥 Enregistrer ce point de mesure"):
        st.session_state.mesures.append({
            "f": f_in, 
            "g": 20*np.log10(np.abs(H_in) + 1e-12), 
            "p": np.degrees(np.angle(H_in))
        })
        st.success(f"Point à {f_in} Hz enregistré !")

with tabs[2]:
    st.header("Diagramme de Bode")
    if st.session_state.mesures:
        df = pd.DataFrame(st.session_state.mesures).sort_values("f")
        
        col1, col2 = st.columns(2)
        with col1:
            fg = go.Figure()
            fg.add_trace(go.Scatter(x=df["f"], y=df["g"], mode='markers+lines', name="Mesures", marker=dict(color='red')))
            fg.update_layout(title="Gain (dB)", xaxis_type="log", height=400)
            st.plotly_chart(fg, use_container_width=True)
        
        with col2:
            fp = go.Figure()
            fp.add_trace(go.Scatter(x=df["f"], y=df["p"], mode='markers+lines', name="Phase (Deg)", marker=dict(color='cyan')))
            fp.update_layout(title="Phase (Deg)", xaxis_type="log", height=400)
            st.plotly_chart(fp, use_container_width=True)
        
        st.table(df)
        
        try:
            pdf_bytes = generer_pdf(mode, R, C_uF*1e-6, fc, df)
            st.download_button("💾 Télécharger le Rapport PDF", pdf_bytes, "Rapport_TP.pdf")
        except Exception as e:
            st.error(f"Erreur PDF : {e}")
    else:
        st.warning("Aucune mesure enregistrée.")
