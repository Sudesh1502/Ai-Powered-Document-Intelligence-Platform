import os
import streamlit as st
import subprocess
import sys
import atexit

@st.cache_resource
def start_background_worker():
    print("[SYSTEM] Spawning Gmail Ingestion background worker...")
    process = subprocess.Popen([sys.executable, "run_ingestion.py"])
    
    def cleanup():
        print("[SYSTEM] Shutting down Gmail Ingestion worker...")
        process.terminate()
        
    atexit.register(cleanup)
    return process

start_background_worker()

st.set_page_config(
    page_title="Document Intelligence Platform",
    page_icon="📄",
    layout="wide"
)
st.markdown("""
    <style>
    /* Prevent Streamlit from graying out elements during auto-refresh */
    [data-testid="stFragment"] {
        opacity: 1 !important;
        transition: none !important;
    }
    .element-container {
        opacity: 1 !important;
        transition: none !important;
    }
    </style>
""", unsafe_allow_html=True)

from src.auth.auth_service import login_user, logout_user

# 1. Wrap the login flow in an empty container so we can instantly obliterate it later
login_placeholder = st.empty()

with login_placeholder.container():
    user = login_user()

if not user:
    # Explicitly clear the navigation state from the frontend before stopping
    pg = st.navigation([st.Page(lambda: None, title="Login")], position="hidden")
    pg.run()
    st.stop()

# --- If we reach here, the user is successfully logged in ---

# 2. Instantly wipe the login form from the browser before doing any heavy lifting
login_placeholder.empty()

# 3. Show a sleek loading spinner while the heavy home page is evaluated and drawn
with st.spinner("Preparing your workspace..."):
    upload_page = st.Page("views/0_Upload.py", title="Upload", icon="⬆️", default=True)
    search_page = st.Page("views/1_Search.py", title="Search", icon="🔍")
    action_page = st.Page("views/2_Action Centre.py", title="Action Centre", icon="⚠️")
    settings_page = st.Page("views/3_Settings.py", title="Settings", icon="⚙️")

    pg = st.navigation([upload_page, search_page, action_page, settings_page])

    with st.sidebar:
        st.markdown(f"**Signed in as:** {user['name']}")
        logout_user()
        st.markdown("---")

    pg.run()
