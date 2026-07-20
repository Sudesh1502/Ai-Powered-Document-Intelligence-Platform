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

# ============================================================
# GLOBAL UX POLISH CSS
# ============================================================
st.markdown("""
    <style>
    /* 1. Suppress Streamlit fragment gray-flash on auto-refresh */
    [data-testid="stFragment"] {
        opacity: 1 !important;
        transition: none !important;
    }
    .element-container {
        opacity: 1 !important;
        transition: none !important;
    }

    /* 2. Page fade-in on every navigation */
    @keyframes pageIn {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0);   }
    }
    .block-container {
        animation: pageIn 0.28s ease-out both;
    }

    /* 3. Button press micro-animation */
    button:active {
        transform: scale(0.97) !important;
        transition: transform 0.08s ease !important;
    }

    /* 4. Smooth hover transitions */
    button {
        transition: background-color 0.18s ease, box-shadow 0.18s ease, transform 0.08s ease !important;
    }

    /* 5. Sidebar fade-in */
    [data-testid="stSidebar"] > div {
        animation: pageIn 0.32s ease-out both;
    }

    /* 6. Spinner centering */
    [data-testid="stSpinner"] {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 60px;
    }

    /* 7. Loading state class for buttons (JS-injected) */
    .ux-loading {
        pointer-events: none !important;
        opacity: 0.6 !important;
        cursor: not-allowed !important;
    }

    /* 8. Full-screen blur loading overlay */
    @keyframes ux-spin {
        to { transform: rotate(360deg); }
    }
    #ux-loading-overlay {
        display: none;
        position: fixed;
        inset: 0;
        z-index: 2147483647;
        background: rgba(15, 23, 42, 0.38);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        align-items: center;
        justify-content: center;
        flex-direction: column;
        gap: 18px;
    }
    #ux-loading-overlay .ux-ring {
        width: 52px;
        height: 52px;
        border: 4px solid rgba(255,255,255,0.25);
        border-top-color: #ffffff;
        border-radius: 50%;
        animation: ux-spin 0.75s linear infinite;
    }
    #ux-loading-overlay .ux-label {
        color: #ffffff;
        font-family: 'Outfit', sans-serif;
        font-size: 15px;
        font-weight: 600;
        letter-spacing: 0.04em;
        opacity: 0.92;
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
    
    /* Style Primary Action Buttons */
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
    
    /* Style Secondary buttons */
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
    
    /* Override table action buttons */
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
    
    /* Style VIEW ALL ACTIVITY button */
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
    
    /* Style tables */
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
    if st.button("Logout", key="sidebar_logout_btn", use_container_width=True):
        with st.spinner("Signing out..."):
            logout_user()
        st.rerun()
    st.markdown("---")

# ============================================================
# GLOBAL BLUR LOADING OVERLAY — registered BEFORE pg.run()
# Primary dismiss: polls for [data-testid="stSpinner"] lifecycle
# Fallback dismiss: MutationObserver with 800ms debounce
# State stored on window.parent._uxState to survive iframe refreshes
# ============================================================
import streamlit.components.v1 as _overlay_comp
_overlay_comp.html("""
<script>
(function() {
    var doc = window.parent.document;
    var win = window.parent;

    // -----------------------------------------------------------------
    // PERSISTENT STATE on window.parent
    // The overlay iframe is recreated on EVERY Streamlit rerender.
    // Variables declared inside this IIFE would reset each time.
    // Storing state on win ensures a single source of truth and
    // prevents accumulating multiple observers / timers.
    // -----------------------------------------------------------------
    if (!win._uxState) {
        win._uxState = {
            spinPoll:  null,   // setInterval — watches stSpinner appear/disappear
            mutObs:    null,   // MutationObserver fallback
            debounce:  null,   // debounce timer for MutObs
            safety:    null,   // hard safety cap setTimeout
            bodyObs:   null,   // body observer for re-wiring new buttons (created once)
            active:    false   // true while overlay is showing
        };
    }
    var S = win._uxState;

    // -----------------------------------------------------------------
    // Overlay element — injected once into parent document body
    // -----------------------------------------------------------------
    function ensureOverlay() {
        if (doc.getElementById('ux-loading-overlay')) return;
        var el = doc.createElement('div');
        el.id = 'ux-loading-overlay';
        el.innerHTML = '<div class="ux-ring"></div><div class="ux-label">Loading...</div>';
        el.style.cssText = [
            'display:none','position:fixed','inset:0','z-index:2147483647',
            'background:rgba(15,23,42,0.38)','backdrop-filter:blur(5px)',
            '-webkit-backdrop-filter:blur(5px)','align-items:center',
            'justify-content:center','flex-direction:column','gap:18px'
        ].join(';');
        var ring = el.querySelector('.ux-ring');
        if (ring) ring.style.cssText = [
            'width:52px','height:52px','border-radius:50%',
            'border:4px solid rgba(255,255,255,0.25)',
            'border-top-color:#fff',
            'animation:ux-spin 0.75s linear infinite'
        ].join(';');
        var lbl = el.querySelector('.ux-label');
        if (lbl) lbl.style.cssText = [
            'color:#fff','font-family:Outfit,sans-serif',
            'font-size:15px','font-weight:600','letter-spacing:0.04em'
        ].join(';');
        if (!doc.getElementById('ux-kf')) {
            var s = doc.createElement('style');
            s.id = 'ux-kf';
            s.textContent = '@keyframes ux-spin{to{transform:rotate(360deg)}}';
            doc.head.appendChild(s);
        }
        doc.body.appendChild(el);
    }

    // -----------------------------------------------------------------
    // Dismiss: clears ALL watchers then hides the overlay
    // Guard with S.active so it only fires once per show
    // -----------------------------------------------------------------
    function hideOverlay() {
        if (!S.active) return;
        S.active = false;

        clearInterval(S.spinPoll);  S.spinPoll  = null;
        clearTimeout(S.debounce);   S.debounce  = null;
        clearTimeout(S.safety);     S.safety    = null;
        if (S.mutObs) { S.mutObs.disconnect(); S.mutObs = null; }

        var el = doc.getElementById('ux-loading-overlay');
        if (el) el.style.display = 'none';
    }

    // -----------------------------------------------------------------
    // Dismiss logic — two parallel mechanisms, first one wins
    // -----------------------------------------------------------------
    function startDismissLogic() {
        // Clear any leftover watchers from a previous incomplete cycle
        clearInterval(S.spinPoll);  S.spinPoll  = null;
        clearTimeout(S.debounce);   S.debounce  = null;
        clearTimeout(S.safety);     S.safety    = null;
        if (S.mutObs) { S.mutObs.disconnect(); S.mutObs = null; }
        S.active = true;

        // ── PRIMARY: stSpinner lifecycle polling ──────────────────────
        // Streamlit renders [data-testid="stSpinner"] for every
        // st.spinner() context. We watch it appear then disappear.
        var spinnersEverSeen = false;
        S.spinPoll = setInterval(function() {
            if (!S.active) { clearInterval(S.spinPoll); return; }
            var count = doc.querySelectorAll('[data-testid="stSpinner"]').length;
            if (!spinnersEverSeen && count > 0) {
                spinnersEverSeen = true;                  // rerun started
            } else if (spinnersEverSeen && count === 0) { // rerun finished
                clearInterval(S.spinPoll); S.spinPoll = null;
                setTimeout(hideOverlay, 250);              // brief grace for final paint
            }
        }, 100);

        // ── FALLBACK: MutationObserver with 800ms debounce ───────────
        // Handles fast reruns that have NO explicit st.spinner()
        // (e.g. Back to List, sidebar navigation).
        // 800ms sits comfortably between Streamlit's rerender burst
        // (< 200ms) and the next fragment auto-refresh (≥ 5000ms).
        // The observer disconnects itself as soon as the debounce fires
        // so the fragment tick CANNOT reset it after dismiss.
        var target = doc.querySelector('.block-container') || doc.body;
        S.mutObs = new MutationObserver(function() {
            if (!S.active) { S.mutObs.disconnect(); S.mutObs = null; return; }
            clearTimeout(S.debounce);
            S.debounce = setTimeout(function() {
                if (S.mutObs) { S.mutObs.disconnect(); S.mutObs = null; }
                hideOverlay();
            }, 800);
        });
        S.mutObs.observe(target, { childList: true, subtree: true });

        // ── SAFETY CAP: unconditional dismiss after 8 seconds ─────────
        S.safety = setTimeout(hideOverlay, 8000);
    }

    // -----------------------------------------------------------------
    // Show overlay + start dismiss logic
    // -----------------------------------------------------------------
    function showOverlay(label) {
        ensureOverlay();
        var el = doc.getElementById('ux-loading-overlay');
        var lbl = el.querySelector('.ux-label');
        if (lbl) lbl.textContent = label || 'Loading...';
        el.style.display = 'flex';
        startDismissLogic();
    }

    // -----------------------------------------------------------------
    // Wire action buttons — skips already-wired buttons (no duplicates)
    // -----------------------------------------------------------------
    var BTNS = [
        { text: 'Review',              label: 'Loading document...' },
        { text: 'View Document',       label: 'Loading document...' },
        { text: '\u2190 Back to List', label: 'Going back...'       },
        { text: 'Approve',             label: 'Approving...'        },
        { text: 'Reject',              label: 'Rejecting...'        },
        { text: 'Logout',              label: 'Signing out...'      },
        { text: 'Search Documents',    label: 'Searching...'        },
        { text: 'Process Documents',   label: 'Processing...'       },
    ];

    function wireButtons() {
        doc.querySelectorAll('button').forEach(function(btn) {
            if (btn.dataset.overlayWired) return;
            var txt = btn.innerText.trim();
            var match = null;
            for (var i = 0; i < BTNS.length; i++) {
                if (txt === BTNS[i].text || txt.indexOf(BTNS[i].text) === 0) {
                    match = BTNS[i]; break;
                }
            }
            if (match) {
                btn.dataset.overlayWired = 'true';
                (function(m) {
                    btn.addEventListener('click', function() { showOverlay(m.label); });
                })(match);
            }
        });
        doc.querySelectorAll('[data-testid="stSidebarNav"] a, [data-testid="stSidebarNavLink"]').forEach(function(link) {
            if (link.dataset.overlayWired) return;
            link.dataset.overlayWired = 'true';
            link.addEventListener('click', function() { showOverlay('Navigating...'); });
        });
    }

    // -----------------------------------------------------------------
    // Bootstrap — runs on every iframe refresh
    // bodyObserver is stored on S and created only ONCE to prevent
    // accumulation of identical observers across Streamlit rerenders
    // -----------------------------------------------------------------
    ensureOverlay();
    wireButtons();

    if (!S.bodyObs) {
        S.bodyObs = new MutationObserver(function() { wireButtons(); });
        S.bodyObs.observe(doc.body, { childList: true, subtree: true });
    }
})();
</script>
""", height=0)

# Run page execution
pg.run()
