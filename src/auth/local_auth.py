import streamlit_authenticator as stauth
import streamlit as st

class LocalAuthProvider:
    def __init__(self):
        self.authenticator = self._load_authenticator()

    def _load_authenticator(self):
        import os
        from azure.data.tables import TableServiceClient
        from src.config.config import AUTH_COOKIE_EXPIRY_DAYS
        
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
                    'expiry_days': AUTH_COOKIE_EXPIRY_DAYS
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

        # 1. If already logged in, return user instantly
        if st.session_state.get('authentication_status'):
            return {
                "user_id": st.session_state.get("username"),
                "email": st.session_state.get("email", ""),
                "name": st.session_state.get("name", "")
            }

        # 2. Render the login widget cleanly in the center of the screen
        col1, col2, col3 = st.columns([1.2, 1, 1.2])
        with col2:
            st.markdown("""
                <style>
                    div[data-testid="stMarkdownContainer"] h1,
                    div[data-testid="stMarkdownContainer"] h2,
                    div[data-testid="stMarkdownContainer"] h3 {
                        text-align: center !important;
                    }

                    /* Override Streamlit's rigid flexbox parents using the exact container key */
                    div.st-key-FormSubmitter-Login-Login {
                        width: 100% !important;
                        display: block !important;
                    }
                    div[data-testid="stFormSubmitButton"] {
                        width: 100% !important;
                        display: block !important;
                    }
                    button[data-testid="stBaseButton-secondaryFormSubmit"] {
                        width: 100% !important;
                        background-color: #002060 !important;
                        color: white !important;
                        border-color: #002060 !important;
                    }
                    button[data-testid="stBaseButton-secondaryFormSubmit"]:hover {
                        background-color: #001540 !important;
                        border-color: #001540 !important;
                    }
                    /* Hide Streamlit's native eye icon in password fields */
                    div[data-testid="stTextInput"] button[kind="icon"] {
                        display: none !important;
                    }
                    /* Increase the bottom padding of the login card */
                    div[data-testid="stForm"] {
                        padding-bottom: 2.5rem !important;
                        padding-left: 2rem !important;
                        padding-right: 2rem !important;
                    }
                    /* Hide Streamlit's auto-generated anchor links (chain icons) next to headers */
                    div[data-testid="stMarkdownContainer"] h1 a,
                    div[data-testid="stMarkdownContainer"] h2 a,
                    div[data-testid="stMarkdownContainer"] h3 a {
                        display: none !important;
                    }
                    /* Hide 'Press Enter to submit form' text inside input boxes */
                    div[data-testid="InputInstructions"] { 
                        display: none !important; 
                    }
                </style>
            """, unsafe_allow_html=True)
            
            # Render the native authenticator form
            try:
                result = self.authenticator.login(
                    location='main',
                    fields={'Username': 'Email Address'}
                )
                
                if isinstance(result, tuple) and len(result) == 3:
                    name, authentication_status, username = result
                else:
                    authentication_status = st.session_state.get('authentication_status')
                    username = st.session_state.get('username')
                    name = st.session_state.get('name')
            except Exception:
                authentication_status = st.session_state.get('authentication_status')
                username = st.session_state.get('username')
                name = st.session_state.get('name')

            # 3. Use native Streamlit alert rendering below the form
            if authentication_status is False:
                st.error('Username/password is incorrect')

            # 4. Use a headless JS component to securely inject placeholders and the show password toggle
            import streamlit.components.v1 as components
            components.html("""
                <script>
                    // Execute all DOM manipulation inside a timeout to ensure Streamlit's React frontend has completely finished rendering
                    setTimeout(() => {
                        // 1. Inject placeholders robustly
                        const formInputs = window.parent.document.querySelectorAll('div[data-testid="stForm"] input');
                        formInputs.forEach(input => {
                            if(input.type === 'password' || input.getAttribute('type') === 'password') {
                                input.placeholder = "Enter your password...";
                            } else if (input.type === 'text') {
                                input.placeholder = "Enter your email address...";
                            }
                        });

                        // 2. Inject 'show password' toggle above the password input and hide native eye icon
                        const pwInput = window.parent.document.querySelector('div[data-testid="stForm"] input[type="password"]');
                        if (pwInput) {
                            const textInputDiv = pwInput.closest('div[data-testid="stTextInput"]');
                            if (textInputDiv) {
                                // Hide the native eye icon robustly via JS
                                const eyeBtn = textInputDiv.querySelector('button');
                                if (eyeBtn) {
                                    eyeBtn.style.display = 'none';
                                }
                                
                                // Inject custom text toggle on the far right using absolute positioning
                                if (!textInputDiv.querySelector('.custom-show-pw')) {
                                    textInputDiv.style.position = 'relative';
                                    
                                    const toggleBtn = window.parent.document.createElement('span');
                                    toggleBtn.innerText = "show password";
                                    toggleBtn.className = "custom-show-pw";
                                    toggleBtn.style.color = "#64748B";
                                    toggleBtn.style.cursor = "pointer";
                                    toggleBtn.style.fontSize = "13px";
                                    toggleBtn.style.fontWeight = "600";
                                    
                                    // Position it absolutely at the top right of the widget
                                    toggleBtn.style.position = 'absolute';
                                    toggleBtn.style.right = '0';
                                    toggleBtn.style.top = '0';
                                    toggleBtn.style.zIndex = '10';
                                    
                                    toggleBtn.onclick = function() {
                                        if(pwInput.type === 'password') {
                                            pwInput.type = 'text';
                                            toggleBtn.innerText = "hide password";
                                        } else {
                                            pwInput.type = 'password';
                                            toggleBtn.innerText = "show password";
                                        }
                                    };
                                    
                                    textInputDiv.appendChild(toggleBtn);
                                }
                            }
                        }

                        // 3. Inject the subtitle below the Login heading
                        // Scan all possible heading sizes (Streamlit often uses h3 for subheaders)
                        const possibleHeadings = window.parent.document.querySelectorAll('div[data-testid="stMarkdownContainer"] h1, div[data-testid="stMarkdownContainer"] h2, div[data-testid="stMarkdownContainer"] h3, div[data-testid="stMarkdownContainer"] p');
                        
                        let loginHeading = null;
                        for (let i = 0; i < possibleHeadings.length; i++) {
                            if (possibleHeadings[i].innerText.trim() === 'Login') {
                                loginHeading = possibleHeadings[i];
                                break;
                            }
                        }

                        if (loginHeading && !window.parent.document.querySelector('.custom-login-subtitle')) {
                            const subtitle = window.parent.document.createElement('div');
                            subtitle.className = 'custom-login-subtitle';
                            subtitle.innerHTML = 'Secure access to your AI-Powered Intelligent<br>Document Processing workspace.';
                            
                            subtitle.style.textAlign = 'center';
                            subtitle.style.color = '#1f4f8b';
                            subtitle.style.fontSize = '15px';
                            // Center vertically between Login and Email Address
                            subtitle.style.marginTop = '10px';
                            subtitle.style.marginBottom = '15px';
                            
                            // Inject directly below the Markdown container wrapping the heading
                            const mdContainer = loginHeading.closest('div[data-testid="stMarkdownContainer"]');
                            if (mdContainer) {
                                mdContainer.insertAdjacentElement('afterend', subtitle);
                            } else {
                                loginHeading.insertAdjacentElement('afterend', subtitle);
                            }
                        }
                    }, 500);
                </script>
            """, height=0, width=0)
        
        # 5. Return user profile if authenticated
        if authentication_status:
            return {
                "user_id": username,
                "email": st.session_state.get("email", username),
                "name": name
            }
        return None

    def logout(self):
        if self.authenticator:
            self.authenticator.logout('Logout', 'main')
