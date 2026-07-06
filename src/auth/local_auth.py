import streamlit_authenticator as stauth
import streamlit as st

class LocalAuthProvider:
    def __init__(self):
        self.authenticator = self._load_authenticator()

    def _load_authenticator(self):
        import os
        from azure.data.tables import TableServiceClient
        
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            st.error("Azure Storage connection string is missing.")
            return None
            
        try:
            table_service_client = TableServiceClient.from_connection_string(connection_string)
            table_client = table_service_client.get_table_client("Users")
            
            usernames = {}
            # Dynamically build the configuration dictionary from the Azure Table
            for entity in table_client.list_entities():
                email = entity.get("RowKey")
                if email:
                    usernames[email] = {
                        "email": entity.get("Email"),
                        "name": entity.get("Name"),
                        "password": entity.get("Password")
                    }
                    
            config = {
                'credentials': {'usernames': usernames},
                'cookie': {
                    'name': 'doc_intel_auth_v2',
                    'key': 'adrosonic_secret_auth_key_8492',
                    'expiry_days': 30
                }
            }
            
            return stauth.Authenticate(
                config['credentials'],
                config['cookie']['name'],
                config['cookie']['key'],
                config['cookie']['expiry_days']
            )
            
        except Exception as e:
            st.error(f"Failed to load users from Azure Table Storage: {e}")
            return None

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
