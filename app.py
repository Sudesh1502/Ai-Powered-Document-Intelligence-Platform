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
    page_icon=":material/description:",
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
    /* ── Typography: Montserrat for headings, Inter for body ── */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    /* ── Global ── */
    .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #FFFFFF;
        color: #1a2c47;
    }

    /* ══════════════════════════════════════════════════
       SIDEBAR — Deep Navy, Adrosonic Corporate
       ══════════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a2c47 0%, #111e34 100%) !important;
        border-right: none !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    /* Signed in text */
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown strong {
        color: rgba(255,255,255,0.7) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
    }
    /* Nav links — clean line icon styling */
    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNavLink"] {
        color: rgba(255,255,255,0.75) !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.75rem !important;
        margin-bottom: 2px !important;
        transition: all 0.18s ease !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }
    [data-testid="stSidebarNav"] a:hover,
    [data-testid="stSidebarNavLink"]:hover {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
    }
    /* Active state — subtle left accent */
    [data-testid="stSidebarNav"] a[aria-selected="true"],
    [data-testid="stSidebarNavLink"][aria-selected="true"] {
        background-color: rgba(0, 204, 255, 0.1) !important;
        color: #00ccff !important;
        font-weight: 600 !important;
        border-left: 3px solid #00ccff !important;
    }
    /* Logout button */
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        color: rgba(255,255,255,0.9) !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
        margin-top: 0.25rem !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: rgba(255,255,255,0.1) !important;
        border-color: #ffffff !important;
        color: #ffffff !important;
    }
    /* Sidebar divider */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.08) !important;
        margin: 0.75rem 0 !important;
    }

    /* ══════════════════════════════════════════════════
       KPI METRIC CARDS — Clean white, soft elevation
       ══════════════════════════════════════════════════ */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%) !important;
        border: 1px solid #dbeafe !important;
        border-radius: 10px !important;
        padding: 1.25rem 1.4rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.8), inset 0 -1px 2px rgba(0, 0, 0, 0.02) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.06), 0 4px 6px -4px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 1) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        color: #64748B !important;
        text-transform: uppercase !important;
        font-size: 0.68rem !important;
        letter-spacing: 0.08em !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        color: #1a2c47 !important;
        font-size: 2rem !important;
        line-height: 1.2 !important;
    }

    /* ══════════════════════════════════════════════════
       FORMS & CARDS — Clean, subtle borders
       ══════════════════════════════════════════════════ */
    div[data-testid="stForm"], .stCard {
        background-color: #ffffff !important;
        border: 1px solid #e8ecf1 !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
        padding: 1.75rem !important;
    }

    /* ══════════════════════════════════════════════════
       PRIMARY BUTTONS — Adrosonic blue gradient CTA
       ══════════════════════════════════════════════════ */
    button[kind="primary"],
    button[kind="primaryFormSubmit"],
    button[data-testid="stFormSubmitButton"] {
        background: linear-gradient(135deg, #1a2c47 0%, #295fd5 100%) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        padding: 0.6rem 1.75rem !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.01em !important;
    }
    button[kind="primary"]:hover,
    button[kind="primaryFormSubmit"]:hover,
    button[data-testid="stFormSubmitButton"]:hover {
        background: linear-gradient(135deg, #142340 0%, #1e4fb8 100%) !important;
        box-shadow: 0 4px 14px rgba(26, 44, 71, 0.2) !important;
        transform: translateY(-1px);
    }

    /* ══════════════════════════════════════════════════
       SECONDARY BUTTONS
       ══════════════════════════════════════════════════ */
    button[kind="secondary"] {
        background: linear-gradient(135deg, #f0f7ff 0%, #dbeafe 100%) !important;
        color: #1a2c47 !important;
        border: 1px solid #bfdbfe !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1.15rem !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #e0f2fe 0%, #bfdbfe 100%) !important;
        border-color: #93c5fd !important;
        color: #1a2c47 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
    }

    /* ── File Uploader Buttons — neutral ── */
    [data-testid="stFileUploader"] button {
        background-color: #f7f8fa !important;
        color: #1a2c47 !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: none !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background-color: #eef1f6 !important;
        border-color: #cbd5e1 !important;
    }

    /* ── Table inline action buttons (View, Review) ── */
    div:has(div.table-btn-anchor) + div button {
        background-color: transparent !important;
        color: #64748b !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }
    div:has(div.table-btn-anchor) + div button:hover {
        color: #1a2c47 !important;
        background-color: #f7f8fa !important;
        border-color: #cbd5e1 !important;
    }

    /* ── View All Activity Link ── */
    .view-all-container button {
        background-color: transparent !important;
        color: #00ccff !important;
        border: none !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.03em !important;
        font-size: 0.8rem !important;
        box-shadow: none !important;
        padding: 0.4rem 1rem !important;
        border-radius: 6px !important;
        transition: all 0.15s ease !important;
    }
    .view-all-container button:hover {
        color: #1a2c47 !important;
        background-color: #f7f8fa !important;
    }

    /* ══════════════════════════════════════════════════
       LAYOUT
       ══════════════════════════════════════════════════ */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }

    /* ── Tables ── */
    .stTable, [data-testid="stTable"] {
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1px solid #e8ecf1 !important;
    }

    /* ══════════════════════════════════════════════════
       TYPOGRAPHY
       ══════════════════════════════════════════════════ */
    h1, h2, h3, h4, h5, h6,
    .stTitle, .stHeader, .stSubheader {
        font-family: 'Montserrat', sans-serif !important;
        color: #1a2c47 !important;
        font-weight: 600 !important;
    }

    /* ── Expanders ── */
    [data-testid="stExpander"] summary {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        color: #1a2c47 !important;
        font-size: 0.9rem !important;
    }

    /* ── Progress bar ── */
    [data-testid="stProgress"] > div > div > div {
        background: linear-gradient(90deg, #00ccff, #03b7b7) !important;
        border-radius: 4px !important;
    }

    /* ── Tabs ── */
    button[data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        color: #64748b !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00ccff !important;
        border-bottom-color: #00ccff !important;
    }

    /* ── Dividers ── */
    hr {
        border-color: #e8ecf1 !important;
    }

    /* ── Captions & Small Text ── */
    .stCaption, [data-testid="stCaption"] {
        color: #94a3b8 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Toggle ── */
    [data-testid="stToggle"] label span {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.875rem !important;
        color: #475569 !important;
    }

    /* ── Input fields ── */
    [data-testid="stTextInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stSelectbox"] div[data-baseweb="select"] {
        font-family: 'Inter', sans-serif !important;
        border-color: #e2e8f0 !important;
        border-radius: 8px !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stDateInput"] input:focus {
        border-color: #00ccff !important;
        box-shadow: 0 0 0 1px #00ccff !important;
    }

    /* ── Download button ── */
    [data-testid="stDownloadButton"] button {
        background-color: #ffffff !important;
        color: #1a2c47 !important;
        border: 1px solid #d1d9e6 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background-color: #f7f8fa !important;
        border-color: #b0bac9 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Show a sleek loading spinner while the heavy home page is evaluated and drawn
with st.spinner("Preparing your workspace..."):
    upload_page = st.Page("views/0_Upload.py", title="Upload", icon=":material/upload:", default=True)
    search_page = st.Page("views/1_Search.py", title="Search", icon=":material/search:")
    action_page = st.Page("views/2_Action Centre.py", title="Action Centre", icon=":material/warning:")
    settings_page = st.Page("views/3_Settings.py", title="Settings", icon=":material/settings:")

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
