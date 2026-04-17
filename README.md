⚡ Laboratoire Virtuel d'Électronique (Filtres RC/CR)

Cette application interactive, développée avec Streamlit, permet de simuler le comportement fréquentiel et temporel des filtres analogiques
du premier ordre (Passe-Bas et Passe-Haut).
Elle est conçue pour les étudiants .

🚀 Fonctionnalités principales

Simulation en temps réel : Calcul instantané de la fréquence de coupure ($F_c$) en fonction des composants choisis ($R$ et $C$).

Oscilloscope Virtuel : Visualisation des signaux d'entrée ($V_e$) et de sortie ($V_s$) pour observer le déphasage et l'atténuation.

Tracé de Bode Interactif : Enregistrement de points de mesure pour construire les diagrammes de Gain et de Phase.

Génération de Rapport PDF : Exportation automatique d'un rapport complet incluant les paramètres, les formules théoriques et les graphiques.

🛠️ Installation et Lancement

Assurez-vous d'avoir Python installé (version 3.8 ou plus). Installez les bibliothèques nécessaires via votre terminal :

pip install streamlit numpy plotly pandas fpdf matplotlib

2. Lancement de l'application

   streamlit run app.py

   📖 Guide d'utilisation

 Étape 1 : Configuration (Barre latérale)

Type de Filtre : Choisissez entre un filtre Passe-Bas (RC) ou Passe-Haut (CR).


 Composants : Ajustez les valeurs de la résistance ($R$) et de la capacité ($C$).
 La fréquence de coupure ($F_c$) est mise à jour automatiquement.

 Étape 2 : Étude Théorique (Onglet 1)

.Consultez les formules mathématiques (Fonction de transfert) correspondant au filtre sélectionné pour comprendre
le comportement attendu.

Étape 3 : Mesures à l'Oscilloscope (Onglet 2)

Modifiez la fréquence du GBF.

Observez les courbes sur l'oscilloscope.

Cliquez sur le bouton "Enregistrer ce point" pour ajouter la donnée au tableau de mesures.

Astuce : Prenez plusieurs points avant, à, et après $F_c$ pour un beau tracé.

Étape 4 : Analyse et Rapport (Onglet 3)

Visualisez vos points de mesure sur le Diagramme de Bode.

Consultez le tableau récapitulatif.

Cliquez sur "Télécharger le Rapport PDF" pour obtenir votre compte-rendu final.
