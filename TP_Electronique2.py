import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from fpdf import FPDF
import io
import matplotlib.pyplot as plt

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Labo Électronique Pro", layout="wide")

# Initialisation des mesures dans la session
if 'mesures' not in st.session_state:
    st.session_state.mesures = []

# --- FONCTION GÉNÉRATION PDF ---
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
    H_th = 1/(1+1j*2*np.pi*f_th*tau) if "Bas" in mode else (1j*2*np.pi*f_th*tau)/(1+1j*2*np.pi*f_th*tau)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))
    ax1.semilogx(f_th, 20*np.log10(np.abs(H_th)), color='gray', linestyle='--')
    ax1.semilogx(df['f'], df['g'], 'ro-')
    ax1.set_ylabel('Gain (dB)')
    ax1.grid(True, which="both")
    
    ax2.semilogx(f_th, np.degrees(np.angle(H_th)), color='gray', linestyle='--')
    ax2.semilogx(df['f'], df['p'], 'co-')
    ax2.set_ylabel('Phase (Deg)')
    ax2.grid(True, which="both")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    pdf.image(buf, x=10, y=80, w=180)
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE PRINCIPALE ---
st.title("⚡ Laboratoire Virtuel d'Électronique")

# --- BARRE LATÉRALE (PARAMÈTRES) ---
st.sidebar.header("⚙️ Configuration")
mode = st.sidebar.selectbox("Type de Filtre", ["Passe-Bas (RC)", "Passe-Haut (CR)"])
R = st.sidebar.number_input("R (Ohms)", value=1000, step=100)
C_uF = st.sidebar.number_input("C (uF)", value=0.1, step=0.01)

tau = R * (C_uF * 1e-6)
fc = 1 / (2 * np.pi * tau)
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
    f_in = st.number_input("Fréquence du GBF (Hz)", min_value=1.0, value=float(np.round(fc)), step=10.0)
    
    w_in = 2 * np.pi * f_in
    H_in = 1/(1+1j*w_in*tau) if "Bas" in mode else (1j*w_in*tau)/(1+1j*w_in*tau)
    
    t = np.linspace(0, 2/f_in, 1000)
    ve = np.sin(w_in * t)
    vs = np.abs(H_in) * np.sin(w_in * t + np.angle(H_in))
    
    fig_scope = go.Figure()
    fig_scope.add_trace(go.Scatter(x=t*1e3, y=ve, name="Entrée Ve (V)", line=dict(color='yellow')))
    fig_scope.add_trace(go.Scatter(x=t*1e3, y=vs, name="Sortie Vs (V)", line=dict(color='cyan')))
    fig_scope.update_layout(template="plotly_dark", xaxis_title="Temps (ms)", yaxis_title="Tension (V)", height=400)
    st.plotly_chart(fig_scope, width='stretch')
    
    if st.button("📥 Enregistrer ce point de mesure"):
        st.session_state.mesures.append({
            "f": f_in, 
            "g": 20*np.log10(np.abs(H_in)), 
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
            st.plotly_chart(fg, width='stretch')
        
        with col2:
            fp = go.Figure()
            fp.add_trace(go.Scatter(x=df["f"], y=df["p"], mode='markers+lines', name="Phase (Deg)", marker=dict(color='cyan')))
            fp.update_layout(title="Phase (Deg)", xaxis_type="log", height=400)
            st.plotly_chart(fp, width='stretch')
        
        st.table(df)
        
        # Génération du PDF
        pdf_data = generer_pdf(mode, R, C_uF*1e-6, fc, df)
        st.download_button("💾 Télécharger le Rapport PDF", pdf_data, "Rapport_TP.pdf")
    else:
        st.warning("Aucune mesure enregistrée. Allez dans l'onglet OSCILLOSCOPE pour ajouter des points.")