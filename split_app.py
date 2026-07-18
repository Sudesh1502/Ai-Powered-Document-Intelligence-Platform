with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Upload page needs: imports + line 108 to end
upload_lines = [
    "import os\n",
    "import streamlit as st\n",
]
upload_lines.extend(lines[20:55]) # lines 21 to 55 (0-indexed 20 to 54)
upload_lines.extend(lines[107:]) # line 108 to end (0-indexed 107 to end)

# Replace "pages/LOGO.png" with "views/LOGO.png"
for i, line in enumerate(upload_lines):
    if "pages/LOGO.png" in line:
        upload_lines[i] = line.replace("pages/LOGO.png", "views/LOGO.png")

with open("views/0_Upload.py", "w", encoding="utf-8") as f:
    f.writelines(upload_lines)

# app.py needs: imports + background worker + login + router
app_lines = lines[:20] # lines 1 to 20
app_lines.extend(lines[55:60]) # st.set_page_config
app_lines.extend(lines[61:74]) # global css
app_lines.append("\nfrom src.auth.auth_service import login_user, logout_user\n")
app_lines.append("\nuser = login_user()\n")
app_lines.append("if not user:\n")
app_lines.append("    st.stop()\n\n")

app_lines.append('upload_page = st.Page("views/0_Upload.py", title="Upload", icon="⬆️", default=True)\n')
app_lines.append('search_page = st.Page("views/1_Search.py", title="Search", icon="🔍")\n')
app_lines.append('action_page = st.Page("views/2_Action Centre.py", title="Action Centre", icon="⚠️")\n')
app_lines.append('settings_page = st.Page("views/3_Settings.py", title="Settings", icon="⚙️")\n\n')

app_lines.append('pg = st.navigation([upload_page, search_page, action_page, settings_page])\n\n')
app_lines.append('with st.sidebar:\n')
app_lines.append('    st.markdown(f"**Signed in as:** {user[\'name\']}")\n')
app_lines.append('    logout_user()\n')
app_lines.append('    st.markdown("---")\n\n')

app_lines.append('pg.run()\n')

with open("app.py", "w", encoding="utf-8") as f:
    f.writelines(app_lines)
