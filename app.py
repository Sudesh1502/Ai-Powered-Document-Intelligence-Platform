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
    layout="wide",
    initial_sidebar_state="expanded"
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

# 1. Wrap the login flow in an empty container
login_placeholder = st.empty()

with login_placeholder.container():
    user = login_user()

if not user:
    # Ensure any stale fast-rerun flags are destroyed since the user is on the login screen
    if 'cookie_saved_rerun' in st.session_state:
        del st.session_state['cookie_saved_rerun']

    # Explicitly clear the navigation state from the frontend before stopping
    pg = st.navigation([st.Page(lambda: None, title="Login")], position="hidden")
    pg.run()
    st.stop()

# --- If we reach here, the user is successfully logged in ---

# 2. Fast Rerun Trick: If we just authenticated this very millisecond, trigger a lightning-fast rerun.
# This guarantees the browser receives the invisible cookie-setting script from the authenticator.
if not st.session_state.get('cookie_saved_rerun'):
    st.session_state['cookie_saved_rerun'] = True
    st.rerun()
else:
    # We are on the SECOND run. The cookie is safely saved in the browser.
    # We must explicitly wipe the stale login form from the previous run BEFORE loading the heavy pages!
    login_placeholder.empty()

# --- Global CSS and Style Injection for Figma Design Reference ---
st.markdown("""
    <style>
    /* Import modern typography */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');
    
    /* Apply globally */
    .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC;
    }
    
    /* Style cards and forms */
    div[data-testid="stForm"], .stCard {
        background-color: #ffffff !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03) !important;
        padding: 2rem !important;
    }
    
    /* Style metrics/KPI cards with vertical left border */
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #E2E8F0 !important;
        border-left: 4px solid #002060 !important;
        border-radius: 8px !important;
        padding: 1.2rem !important;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.02) !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        color: #64748B !important;
        text-transform: uppercase !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        font-size: 1.8rem !important;
    }
    
    /* Style Primary Action Buttons (including Form Submit buttons) */
    button[kind="primary"],
    button[kind="primaryFormSubmit"],
    button[data-testid="stFormSubmitButton"] {
        background-color: #002060 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important;
        transition: all 0.2s ease !important;
    }
    button[kind="primary"]:hover,
    button[kind="primaryFormSubmit"]:hover,
    button[data-testid="stFormSubmitButton"]:hover {
        background-color: #001040 !important;
        transform: translateY(-1px);
        box-shadow: 0px 4px 12px rgba(0, 32, 96, 0.2) !important;
    }
    
    /* Style Secondary buttons (Navigation & Action buttons) as theme color by default */
    button[kind="secondary"] {
        background-color: #002060 !important;
        color: #ffffff !important;
        border: 1px solid #002060 !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        background-color: #001040 !important;
        border-color: #001040 !important;
        color: #ffffff !important;
        box-shadow: 0px 4px 12px rgba(0, 32, 96, 0.15) !important;
    }
    
    /* Keep file uploader buttons light/default */
    [data-testid="stFileUploader"] button {
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: none !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background-color: #E2E8F0 !important;
        border-color: #CBD5E1 !important;
        color: #0F172A !important;
    }
    
    /* Override table action buttons (targeted via custom .table-btn-anchor sibling class) */
    div:has(div.table-btn-anchor) + div button {
        background-color: transparent !important;
        color: #475569 !important;
        border: 1px solid transparent !important;
    }
    div:has(div.table-btn-anchor) + div button:hover {
        color: #002060 !important;
        background-color: #F1F5F9 !important;
        border-color: #002060 !important;
        box-shadow: none !important;
    }
    
    /* Style VIEW ALL ACTIVITY button as a centered text link */
    .view-all-container button {
        background-color: transparent !important;
        color: #2563EB !important;
        border: none !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
        font-size: 0.8rem !important;
        box-shadow: none !important;
        margin: 0 auto !important;
        display: block !important;
        width: auto !important;
        padding: 0.5rem 1.5rem !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    .view-all-container button:hover {
        color: #1D4ED8 !important;
        background-color: #F1F5F9 !important;
        text-decoration: underline !important;
    }
    
    /* Custom spacing and margins */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }
    
    /* Style tables nicely */
    .stTable, [data-testid="stTable"] {
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid #E2E8F0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Show a sleek loading spinner while the heavy home page is evaluated and drawn
with st.spinner("Preparing your workspace..."):
    upload_page = st.Page("views/0_Upload.py", title="Upload", icon="⬆️", default=True)
    search_page = st.Page("views/1_Search.py", title="Search", icon="🔍")
    action_page = st.Page("views/2_Action Centre.py", title="Action Centre", icon="⚠️")
    settings_page = st.Page("views/3_Settings.py", title="Settings", icon="⚙️")

    # Re-enable the standard sidebar navigation
    pg = st.navigation([upload_page, search_page, action_page, settings_page])

# Sidebar contents for authentication and logout
with st.sidebar:
    st.markdown(f"**Signed in as:** {user['name']}")
    logout_user()
    st.markdown("---")

# Run page execution
pg.run()

