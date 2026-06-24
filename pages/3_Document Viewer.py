import streamlit as st
import os
import base64

st.set_page_config(page_title="Document Viewer", page_icon="📄", layout="wide")

st.markdown("## Document Preview")

if "preview_doc" not in st.session_state:
    st.warning("No document selected for preview.")
    if st.button("Go to Search"):
        st.switch_page("pages/1_Search.py")
    st.stop()

doc = st.session_state.preview_doc
file_name = doc.get("file_name", "")
file_path = os.path.join("data", file_name)

if st.button("🔙 Back to Search"):
    st.switch_page("pages/1_Search.py")

st.markdown("---")

if os.path.exists(file_path):
    extension = os.path.splitext(file_path)[1].lower()
    if extension in [".png", ".jpg", ".jpeg"]:
        st.image(file_path, use_container_width=True)
    elif extension == ".pdf":
        with open(file_path, "rb") as pdf:
            st.download_button("Open PDF", data=pdf, file_name=file_name, use_container_width=True)
    elif extension == ".docx":
        with open(file_path, "rb") as f:
            st.download_button("Open DOCX", data=f, file_name=file_name, use_container_width=True)
else:
    st.warning("Original document not found locally.")
