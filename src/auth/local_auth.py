import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from pathlib import Path
import streamlit as st

class LocalAuthProvider:
    def __init__(self, config_path: str = "auth_config.yaml"):
        self.config_path = Path(config_path)
        self.authenticator = self._load_authenticator()

    def _load_authenticator(self):
        if not self.config_path.exists():
            st.error(f"Authentication config not found at {self.config_path}")
            return None

        with open(self.config_path) as file:
            config = yaml.load(file, Loader=SafeLoader)

        return stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days']
        )

    def login(self):
        if not self.authenticator:
            return None

        # 1. If already logged in, return user instantly without rendering widget
        if st.session_state.get('authentication_status'):
            return {
                "user_id": st.session_state.get("username"),
                "email": st.session_state.get("email", ""),
                "name": st.session_state.get("name", "")
            }

        # 2. Render the login widget cleanly in the center of the screen
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            self.authenticator.login(
                location='main',
                fields={'Username': 'Email Address'}
            )
        
        # 3. Check status immediately after the widget interaction
        auth_status = st.session_state.get('authentication_status')
        
        if auth_status:
            # User literally just clicked 'Login' and it succeeded.
            # Force a rerun to clear the login widget off the screen.
            st.rerun()
        elif auth_status is False:
            with col2:
                st.error('Username/password is incorrect')
            return None
        elif auth_status is None:
            with col2:
                st.warning('Please enter your username and password')
            return None

    def logout(self):
        if self.authenticator:
            self.authenticator.logout('Logout', 'main')
