import os
import base64
import streamlit as st
import pandas as pd
import mammoth
from streamlit_pdf_viewer import pdf_viewer

from src.search.search_service import search_documents, get_summary
from src.search.report_service import generate_investigation_report, generate_pdf_from_markdown
from src.utils.blob_service import generate_sas_url
import requests
import io

st.set_page_config(
    page_title="Search",
    page_icon="🔍",
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

from src.auth.auth_service import login_user, logout_user

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

with st.sidebar:
    st.markdown(f"**Signed in as:** {user['name']}")
    logout_user()
    st.markdown("---")

header1, header2 = st.columns(
    [1, 8]
)

with header1:
    logo_path = "pages/LOGO.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=150)

with header2:
    st.title("Document Search")
    st.caption("Search indexed documents using keyword and semantic search.")

st.markdown("---")

if st.session_state.get("preview_doc"):
    doc = st.session_state.preview_doc
    if st.button("← Back to List", key="back_to_search"):
        st.session_state.preview_doc = None
        st.rerun()
        
    st.markdown(f"### Reviewing: {doc.get('file_name', 'Document')}")
    st.markdown("---")
    
    st.subheader(doc.get("file_name", ""))
    st.caption("Document Preview")

    blob_name = doc.get("sharepoint_url", "")
    if blob_name:
        sas_url = generate_sas_url(blob_name)
        if sas_url:
            extension = os.path.splitext(blob_name)[1].lower()
            try:
                # Fetch securely into RAM
                response = requests.get(sas_url)
                response.raise_for_status()
                file_bytes = response.content
                
                with st.container(border=True):
                    if extension in [".png", ".jpg", ".jpeg"]:
                        st.image(file_bytes, use_container_width=True)
                    elif extension == ".pdf":
                        try:
                            pdf_viewer(file_bytes, width=700, height=800)
                        except Exception as e:
                            st.error(f"Failed to preview PDF: {e}")
                    elif extension == ".docx":
                        try:
                            docx_file = io.BytesIO(file_bytes)
                            result = mammoth.convert_to_html(docx_file)
                            html = result.value
                            st.markdown(
                                f'<div style="height: 800px; overflow-y: auto; padding: 1rem; background: white; color: black; font-family: sans-serif;">{html}</div>', 
                                unsafe_allow_html=True
                            )
                        except Exception as e:
                            st.error(f"Failed to preview DOCX: {e}")
            except Exception as e:
                st.error(f"Failed to load document from cloud: {e}")
        else:
            st.warning("Failed to generate secure preview link.")
    else:
        st.warning("Original document URL not found.")
    st.stop()

c1, c2, c3, c4 = st.columns(
    [4, 2, 2, 2]
)

with c1:
    query = st.text_input(
        "Search Query",
        placeholder="Enter keywords, document number, entity name..."
    )

with c2:
    semantic = st.checkbox("Semantic Search")

with c3:
    index_display = st.selectbox(
        "Search Index",
        ["General Index", "Policy Index"],
        index=0
    )
    
    target_index = "generic-documents-index" if index_display == "General Index" else "policy-master-index"

with c4:
    top = st.selectbox(
        "Top Results",
        [5, 10, 20],
        index=1
    )

st.markdown("")

if st.button(
    "Search Documents",
    width="stretch"
):

    if not query.strip():

        st.warning(
            "Please enter a search query."
        )

    else:

        with st.spinner(
            "Searching documents..."
        ):

            st.session_state.search_results = search_documents(
                query=query,
                use_semantic_ranker=semantic,
                top=top,
                index_name=target_index
            )
            st.session_state.search_query = query
            st.session_state.search_semantic = semantic
            st.session_state.search_index = target_index
            
            # Clear old investigation reports so they don't carry over to the new query
            st.session_state.pop("investigation_report_markdown", None)
            st.session_state.pop("investigation_report_pdf", None)

if "search_results" in st.session_state:

    results = st.session_state.search_results
    query = st.session_state.search_query
    semantic = st.session_state.search_semantic

    if isinstance(
        results,
        dict
    ):

        st.error(
            results.get(
                "error",
                "Search failed."
            )
        )

    elif len(results) == 0:

        st.warning(
            "No documents found."
        )

    else:

        report_placeholder = st.container()
        summary_placeholder = st.empty()
                
        st.markdown("### Search Results")
        
        # 1. Inject CSS to tighten up the vertical spacing (just like Action Centre)
        st.markdown("""
            <style>
            [data-testid="column"] { padding-bottom: 0rem !important; padding-top: 0rem !important; }
            </style>
        """, unsafe_allow_html=True)
        is_policy = st.session_state.get("search_index") == "policy-master-index"
        
        # 2. Draw the Master List Header
        hcols = st.columns([4, 3, 2, 2])
        hcols[0].markdown("**File Name**")
        hcols[1].markdown("**Insured Name**" if is_policy else "**Entity Name**")
        hcols[2].markdown("**Effective Date**" if is_policy else "**Date**")
        hcols[3].markdown("**Action**")
        st.markdown("<hr style='margin: 0.2rem 0; border: none; border-bottom: 1px solid rgba(200,200,200,0.3);'/>", unsafe_allow_html=True)
        
        # 3. Loop through results and draw the rows
        for i, r in enumerate(results, start=1):
            cols = st.columns([4, 3, 2, 2], gap="small")
            
            cols[0].write(r.get('file_name', 'N/A'))
            
            # Map fields based on index
            if is_policy:
                cols[1].write(r.get('insured_name', 'N/A'))
                cols[2].write(str(r.get('policy_effective_date', 'N/A'))[:10])
            else:
                cols[1].write(r.get('entity_name', 'N/A'))
                cols[2].write(str(r.get('document_date', 'N/A'))[:10])
            
            if cols[3].button("View Document", key=f"view_doc_{i}", use_container_width=True):
                st.session_state.preview_doc = r
                st.rerun()
        # 5. Fetch the AI Summary using session state caching to save costs
        with summary_placeholder.container():
            # Check if we already generated a summary for this EXACT query
            if st.session_state.get("last_summary_query") != query:
                with st.spinner("Summary..."):
                    summary = get_summary(
                        search_results=results,
                        user_query=query,
                        semantic_search=semantic
                    )
                    # Cache the new summary and tie it to this query
                    st.session_state["last_summary_query"] = query
                    st.session_state["cached_summary"] = summary
            else:
                # Fetch it instantly from memory for free!
                summary = st.session_state["cached_summary"]

            if isinstance(summary, str):
                st.markdown("### Summary")
                st.info(summary)
            elif isinstance(summary, dict) and "error" in summary:
                st.error(f"Summary Error: {summary['error']}")
                
        # 6. Investigation Report Button
        with report_placeholder:
            st.markdown("---")
            
            has_report = "investigation_report_pdf" in st.session_state
            
            # Dynamically set columns so there isn't a weird gap before generation
            if has_report:
                header_col, gen_btn_col, dl_btn_col = st.columns([3, 1.5, 1.5])
            else:
                header_col, gen_btn_col = st.columns([4, 2])
            
            with header_col:
                st.markdown("<h3 style='margin-bottom: 0;'>Investigation Report</h3>", unsafe_allow_html=True)
                st.caption("Generate a comprehensive investigation report using the retrieved documents.")
                
            with gen_btn_col:
                st.markdown("<div style='margin-top: 22px;'></div>", unsafe_allow_html=True)
                generate_clicked = st.button("Generate Investigation Report", type="primary", use_container_width=True)
                
            if has_report:
                with dl_btn_col:
                    st.markdown("<div style='margin-top: 22px;'></div>", unsafe_allow_html=True)
                    st.download_button(
                        label="Download Report",
                        data=st.session_state["investigation_report_pdf"],
                        file_name="Investigation_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            
            if generate_clicked:
                with st.spinner("Analyzing documents and generating report..."):
                    report_markdown = generate_investigation_report(
                        search_results=results,
                        user_query=query
                    )
                    
                    if report_markdown.startswith("Error"):
                        st.error(report_markdown)
                    else:
                        st.session_state["investigation_report_markdown"] = report_markdown
                        
                        # Generate PDF bytes
                        try:
                            pdf_bytes = generate_pdf_from_markdown(report_markdown)
                            st.session_state["investigation_report_pdf"] = pdf_bytes
                            st.rerun() # Rerun to show the download button immediately
                        except Exception as e:
                            st.error(f"Failed to generate PDF: {e}")
                            
            # Display the PDF preview if it exists in session state
            if "investigation_report_pdf" in st.session_state:
                st.markdown("<br>", unsafe_allow_html=True) # Give a little breathing room
                
                show_preview = st.toggle("Show PDF Preview", value=True)
                if show_preview:
                    with st.container(border=True):
                        try:
                            pdf_viewer(st.session_state["investigation_report_pdf"], width=700, height=800)
                        except Exception as e:
                            st.error(f"Failed to preview PDF: {e}")
