import streamlit as st
from src.auth.local_auth import LocalAuthProvider

def get_auth_provider():
    """
    Factory function to get the current authentication provider.
    Currently hardcoded to LocalAuthProvider, but can be switched to EntraIDAuthProvider later.
    """
    if "auth_provider" not in st.session_state:
        st.session_state.auth_provider = LocalAuthProvider()
    return st.session_state.auth_provider

def login_user():
    """
    Attempts to log in the user and returns the user profile if successful.
    If successful, it also stores the user in st.session_state.user.
    """
    provider = get_auth_provider()
    user_profile = provider.login()
    
    if user_profile:
        st.session_state.user = user_profile
        return user_profile
    return None

def logout_user():
    """
    Logs out the user and clears the session state.
    """
    provider = get_auth_provider()
    provider.logout()
    if 'user' in st.session_state:
        del st.session_state.user
