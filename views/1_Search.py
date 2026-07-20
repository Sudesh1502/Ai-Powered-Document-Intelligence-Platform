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

st.markdown("""
<div style="
    background: linear-gradient(135deg, #f0f7ff 0%, #e0f2fe 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    border: 1px solid #dbeafe;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.8);
    margin-bottom: 1.5rem;
">
    <h1 style="margin: 0; font-family: 'Outfit', sans-serif; color: #0F172A; font-size: 2.2rem; font-weight: 700;">Document Search</h1>
    <p style="margin: 6px 0 0 0; color: #475569; font-size: 1.05rem;">Search indexed documents using keyword and semantic search.</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

if st.session_state.get("preview_doc"):
    doc = st.session_state.preview_doc

    # Pre-load blob bytes before rendering any UI so there is no layout jump
    with st.spinner("Loading document from cloud..."):
        blob_name = doc.get("sharepoint_url", "")
        file_bytes = None
        extension = None
        preview_error = None
        if blob_name:
            sas_url = generate_sas_url(blob_name)
            if sas_url:
                extension = os.path.splitext(blob_name)[1].lower()
                try:
                    response = requests.get(sas_url)
                    response.raise_for_status()
                    file_bytes = response.content
                except Exception as e:
                    preview_error = str(e)

    # Render header row: heading left, back button right
    col_heading, col_back = st.columns([8.5, 1.5])
    with col_heading:
        st.markdown(f"<h3 style='margin:0; padding-top:2px; font-family: Outfit, sans-serif;'>Reviewing: {doc.get('file_name', 'Document')}</h3>", unsafe_allow_html=True)
    with col_back:
        if st.button("← Back to List", key="back_to_search", use_container_width=True):
            st.session_state.preview_doc = None
            st.rerun()
    st.markdown("---")
    
    # JS: immediately blank the page when Back is clicked to prevent layout-jump flash
    import streamlit.components.v1 as _sc_back_s
    _sc_back_s.html("""
        <script>
        setTimeout(() => {
            const btns = window.parent.document.querySelectorAll('button');
            btns.forEach(btn => {
                if (btn.innerText.trim() === '← Back to List' && !btn.dataset.backWired) {
                    btn.dataset.backWired = 'true';
                    btn.addEventListener('click', () => {
                        const container = window.parent.document.querySelector('.block-container');
                        if (container) {
                            container.style.transition = 'opacity 0.1s ease';
                            container.style.opacity = '0';
                        }
                    });
                }
            });
        }, 200);
        </script>
    """, height=0)

    st.caption("Document Preview")
    if file_bytes:
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
    elif preview_error:
        st.error(f"Failed to load document from cloud: {preview_error}")
    elif not blob_name:
        st.warning("Original document URL not found.")
    else:
        st.warning("Failed to generate secure preview link.")
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
                
        st.markdown("<h3 style='font-family: Montserrat, sans-serif; color: #1a2c47; font-size: 1.15rem; font-weight: 600; margin-bottom: 1rem; margin-top: 1rem;'>Search Results</h3>", unsafe_allow_html=True)
        
        # 1. Inject CSS to tighten up the vertical spacing (just like Action Centre)
        st.markdown("""
            <style>
            [data-testid="column"] { padding-bottom: 0rem !important; padding-top: 0rem !important; }
            </style>
        """, unsafe_allow_html=True)
        is_policy = st.session_state.get("search_index") == "policy-master-index"
        
        # 2. Draw the Master List Header
        col1_text = "Insured Name" if is_policy else "Entity Name"
        col2_text = "Effective Date" if is_policy else "Date"
        
        hcols = st.columns([4, 3, 2, 2], gap="xxsmall")
        hcols[0].markdown("<div style='background-color: #f8fafc; color: #475569; padding: 10px 14px; text-align: left; font-weight: 600; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; border-radius: 6px 0 0 6px; font-family: Inter, sans-serif;'>File Name</div>", unsafe_allow_html=True)
        hcols[1].markdown(f"<div style='background-color: #f8fafc; color: #475569; padding: 10px 14px; text-align: left; font-weight: 600; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; font-family: Inter, sans-serif;'>{col1_text}</div>", unsafe_allow_html=True)
        hcols[2].markdown(f"<div style='background-color: #f8fafc; color: #475569; padding: 10px 14px; text-align: left; font-weight: 600; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; font-family: Inter, sans-serif;'>{col2_text}</div>", unsafe_allow_html=True)
        hcols[3].markdown("<div style='background-color: #f8fafc; color: #475569; padding: 10px 14px; text-align: center; font-weight: 600; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; border-radius: 0 6px 6px 0; font-family: Inter, sans-serif;'>Action</div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 0.2rem 0; border: none; border-bottom: 1px solid #e2e8f0;'/>", unsafe_allow_html=True)
        
        # 3. Loop through results and draw the rows
        for i, r in enumerate(results, start=1):
            cols = st.columns([4, 3, 2, 2], gap="xxsmall")
            
            cols[0].write(r.get('file_name', 'N/A'))
            
            # Map fields based on index
            if is_policy:
                cols[1].write(r.get('insured_name', 'N/A'))
                cols[2].write(str(r.get('policy_effective_date', 'N/A'))[:10])
            else:
                cols[1].write(r.get('entity_name', 'N/A'))
                cols[2].write(str(r.get('document_date', 'N/A'))[:10])
            
            cols[3].markdown("<div class='table-btn-anchor'></div>", unsafe_allow_html=True)
            if cols[3].button("View Document", key=f"view_doc_{i}", use_container_width=True):
                st.session_state.preview_doc = r
                st.rerun()
        
        # JS: show loading state on View Document buttons immediately on click
        import streamlit.components.v1 as _sc
        _sc.html("""
            <script>
            setTimeout(() => {
                const btns = window.parent.document.querySelectorAll('button');
                btns.forEach(btn => {
                    if (btn.innerText.trim() === 'View Document' && !btn.dataset.uxWired) {
                        btn.dataset.uxWired = 'true';
                        btn.addEventListener('click', () => {
                            btn.innerText = 'Loading...';
                            btn.style.opacity = '0.65';
                            btn.style.pointerEvents = 'none';
                        });
                    }
                });
            }, 300);
            </script>
        """, height=0)
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
                st.markdown("<h3 style='font-family: Montserrat, sans-serif; color: #1a2c47; font-size: 1.15rem; font-weight: 600; margin-bottom: 1rem; margin-top: 1rem;'>Summary</h3>", unsafe_allow_html=True)
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
                st.markdown("<h3 style='font-family: Montserrat, sans-serif; color: #1a2c47; font-size: 1.15rem; font-weight: 600; margin-bottom: 1rem; margin-top: 1rem;'>Investigation Report</h3>", unsafe_allow_html=True)
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
