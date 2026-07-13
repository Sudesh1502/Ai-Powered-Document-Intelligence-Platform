import streamlit as st
from src.auth.auth_service import login_user, logout_user

st.set_page_config(
    page_title="Settings",
    page_icon="📄",
    layout="wide"
)

# Hide sidebar instantly to prevent flash before login
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Authentication Wall ---
user = login_user()
if not user:
    st.stop()

# If user is logged in, restore the sidebar
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] { display: block !important; }
    </style>
    """,
    unsafe_allow_html=True
)
# ---------------------------

# Sidebar Logout
st.sidebar.markdown("---")
st.sidebar.write(f"**Signed in as:** {user.get('name', 'User')}")
if st.sidebar.button("Logout", key="logout_btn"):
    logout_user()

st.title("Settings")
st.markdown("---")

st.header("Cross-Validation Configuration")
st.markdown(
    "<span style='color: gray; font-size: 0.9em;'>Configure the automated rules applied when adjudicating claims against the Policy Master Index.</span>", 
    unsafe_allow_html=True
)
st.write("") # Spacer

rules = [
    {
        "id": "policy_exists",
        "name": "policy_number | policy_ref_umr",
    },
    {
        "id": "identity_match",
        "name": "insured_name | claimant_name | policy_insured",
    },
    {
        "id": "financial_limits",
        "name": "settlement_amount | paid_amount_100 | net_settlement_amount | claim_amount",
    },
    {
        "id": "temporal_coverage",
        "name": "date_of_loss | loss_date_from",
    }
]

for rule in rules:
    with st.container(border=True):
        col_text, col_toggle = st.columns([5, 1])
        with col_text:
            st.markdown(f"`{rule['name']}`")
        with col_toggle:
            st.toggle("Active", value=True, disabled=True, key=f"toggle_{rule['id']}", label_visibility="collapsed")

# Custom Attributes Management
if "custom_attributes" not in st.session_state:
    st.session_state.custom_attributes = []

attributes_to_keep = []

for custom_attr in st.session_state.custom_attributes:
    with st.container(border=True):
        col_text, col_toggle, col_del = st.columns([6, 1, 1])
        with col_text:
            st.markdown(f"`{custom_attr['name']}`")
        with col_toggle:
            # Custom attributes can be toggled by the user
            custom_attr["active"] = st.toggle("Active", value=custom_attr["active"], disabled=False, key=f"toggle_{custom_attr['id']}", label_visibility="collapsed")
        with col_del:
            if st.button("Delete", key=f"del_{custom_attr['id']}"):
                continue # Skip appending this item to effectively delete it
                
    attributes_to_keep.append(custom_attr)

# If an item was deleted, update state and refresh UI immediately
if len(attributes_to_keep) != len(st.session_state.custom_attributes):
    st.session_state.custom_attributes = attributes_to_keep
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

with st.expander("Add Custom Attribute", expanded=False):
    with st.form("add_attribute_form", clear_on_submit=True):
        new_attr_name = st.text_input("Exact JSON Attribute Name (e.g. `medical_history`)")
        submit_btn = st.form_submit_button("Add Attribute")
        
        if submit_btn:
            if new_attr_name.strip():
                # Check for duplicates
                exists = any(attr["name"] == new_attr_name.strip() for attr in st.session_state.custom_attributes)
                if not exists:
                    new_id = f"custom_{len(st.session_state.custom_attributes) + 1}_{new_attr_name.strip().lower().replace(' ', '_')}"
                    st.session_state.custom_attributes.append({
                        "id": new_id,
                        "name": new_attr_name.strip(),
                        "active": True
                    })
                    st.rerun()
                else:
                    st.error("Attribute already exists.")

st.markdown("---")
st.header("General Configuration")
st.write("Placeholder for future system settings.")
