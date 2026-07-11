import streamlit as st
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Importer le client Supabase partagé
try:
    from skills.db import get_supabase_client
    db = get_supabase_client()
    db_connected = True
except Exception as e:
    db_connected = False
    connection_error = str(e)

# Configuration de la page Streamlit
st.set_page_config(
    page_title="OTIS - Dashboard Personnel",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé pour l'esthétique premium
st.markdown("""
<style>
    /* Style général */
    .main {
        background-color: #f7f9fc;
    }
    .db-status {
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        display: inline-block;
    }
    .db-online {
        background-color: #e6f4ea;
        color: #137333;
        border: 1px solid #137333;
    }
    .db-offline {
        background-color: #fce8e6;
        color: #c5221f;
        border: 1px solid #c5221f;
    }
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        border: 1px solid #f0f0f0;
    }
    .priority-high {
        color: #d93025;
        font-weight: bold;
    }
    .priority-medium {
        color: #e37400;
        font-weight: bold;
    }
    .priority-low {
        color: #185abc;
        font-weight: bold;
    }
    .priority-urgent {
        color: #b06000;
        font-weight: bold;
        background-color: #fce8e6;
        padding: 2px 6px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Barre latérale (Sidebar)
with st.sidebar:
    st.title("🤖 OTIS Dashboard")
    st.markdown("---")
    
    # Indicateur visuel d'état Supabase
    st.markdown("### 🔌 Statut Base de données")
    if db_connected:
        try:
            # Tester la connectivité réelle en faisant une micro-requête
            db.table("finance_categories").select("id").limit(1).execute()
            st.markdown('<div class="db-status db-online">🟢 Supabase Connecté</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="db-status db-offline">🔴 Erreur API Supabase</div>', unsafe_allow_html=True)
            st.caption(f"Détail : {str(e)}")
    else:
        st.markdown(f'<div class="db-status db-offline">🔴 Hors ligne</div>', unsafe_allow_html=True)
        st.caption(f"Erreur d'import : {connection_error}")
        
    st.markdown("---")
    st.caption("OTIS v1.2 - Propulsé par FastAPI & Streamlit")

# En-tête de la page principale
st.title("📱 Tableau de Bord OTIS")
st.markdown("Consultez et suivez en direct vos jalons, tâches et rendez-vous synchronisés par vos agents.")

# Si la connexion n'est pas établie, on arrête le rendu des sections
if not db_connected:
    st.error("Impossible de se connecter à Supabase. Vérifiez votre fichier .env.")
    st.stop()

# Fonctions de récupération de données
@st.cache_data(ttl=5) # Cache expiré toutes les 5 secondes pour actualiser en temps réel
def fetch_tasks():
    try:
        res = db.table("tasks").select("*, milestones(name)").execute()
        return res.data
    except Exception:
        return []

@st.cache_data(ttl=5)
def fetch_milestones():
    try:
        res = db.table("milestones").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception:
        return []

@st.cache_data(ttl=5)
def fetch_meetings():
    try:
        # Récupérer les réunions à venir
        res = db.table("reminders").select("*").eq("channel", "calendar").order("trigger_at", desc=False).execute()
        return res.data
    except Exception:
        return []

# Récupération des données
tasks = fetch_tasks()
milestones = fetch_milestones()
meetings = fetch_meetings()

# Layout Principal en colonnes
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📋 Liste des Tâches Actuelles")
    
    if tasks:
        # Transformer en DataFrame pour manipulation et affichage
        df_tasks = pd.DataFrame(tasks)
        
        # Formater les colonnes
        df_tasks['Milestone'] = df_tasks['milestones'].apply(lambda x: x['name'] if isinstance(x, dict) else 'Aucun')
        
        # Sélecteur de statut pour filtrer
        selected_status = st.multiselect(
            "Filtrer par statut :",
            options=["todo", "in_progress", "backlog", "done"],
            default=["todo", "in_progress", "backlog"]
        )
        
        filtered_df = df_tasks[df_tasks['status'].isin(selected_status)]
        
        if not filtered_df.empty:
            for idx, row in filtered_df.iterrows():
                # Formater la date d'échéance
                due_date_str = "Pas de date"
                if row.get('due_date'):
                    try:
                        due_date_dt = datetime.fromisoformat(row['due_date'].replace('Z', '+00:00'))
                        due_date_str = due_date_dt.strftime("%d/%m/%Y à %H:%M")
                    except Exception:
                        due_date_str = row['due_date']

                priority = str(row.get('priority', 'medium')).lower()
                status_emoji = {
                    "todo": "⏳ À faire",
                    "in_progress": "🔄 En cours",
                    "backlog": "📁 Backlog",
                    "done": "✅ Terminé"
                }.get(row['status'], "❓")
                
                priority_class = f"priority-{priority}"
                
                # Rendu de la carte de tâche
                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: #1a0dab;">{row['title']}</h4>
                        <span class="{priority_class}">{priority.upper()}</span>
                    </div>
                    <p style="color: #666; margin: 8px 0;">{row.get('description') or 'Aucune description'}</p>
                    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #888;">
                        <span>🎯 Jalon: <b>{row['Milestone']}</b></span>
                        <span>📅 Échéance: <b>{due_date_str}</b></span>
                        <span>{status_emoji}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aucune tâche ne correspond à ces critères.")
    else:
        st.info("Aucune tâche enregistrée pour le moment. Utilisez WhatsApp pour en ajouter !")

with col_right:
    # Section Réunions et Calendrier
    st.subheader("📅 Prochains Rendez-vous")
    
    if meetings:
        for meet in meetings:
            # Formater la date
            trigger_str = meet['trigger_at']
            try:
                trigger_dt = datetime.fromisoformat(meet['trigger_at'].replace('Z', '+00:00'))
                trigger_str = trigger_dt.strftime("%d/%m/%Y à %H:%M")
            except Exception:
                pass
                
            st.markdown(f"""
            <div class="card" style="border-left: 5px solid #0f9d58;">
                <h5 style="margin: 0 0 6px 0; color: #0f9d58;">{meet['message']}</h5>
                <p style="margin: 0; font-size: 13px; color: #555;">📅 Prévu le: <b>{trigger_str}</b></p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aucun rendez-vous planifié dans le calendrier.")

    st.markdown("---")
    
    # Section Jalons (Milestones)
    st.subheader("🏁 Jalons Actifs")
    if milestones:
        for ms in milestones:
            st.markdown(f"""
            <div class="card" style="border-left: 5px solid #4285f4; padding: 15px;">
                <h5 style="margin: 0 0 4px 0; color: #1a73e8;">🏆 {ms['name']}</h5>
                <p style="margin: 0; font-size: 12px; color: #666;">{ms.get('description') or 'Aucune description'}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aucun jalon (milestone) actif.")
