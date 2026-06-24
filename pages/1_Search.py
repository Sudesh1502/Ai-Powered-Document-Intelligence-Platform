import os
import base64
import streamlit as st
import pandas as pd

from src.search.search_service import search_documents, get_summary
from src.utils.logger import get_logs

st.set_page_config(
    page_title="Search",
    page_icon="🔍",
    layout="wide"
)
header1, header2 = st.columns(
    [1, 8]
)

with header1:

    logo_path = "pages/LOGO.png"

    if os.path.exists(
        logo_path
    ):

        st.image(
            logo_path,
            width=150
        )

with header2:

    st.title(
        "Document Search"
    )

    st.caption(
        "Search indexed documents using keyword and semantic search."
    )

st.markdown("---")

c1, c2, c3 = st.columns(
    [5, 2, 2]
)

with c1:

    query = st.text_input(
        "Search Query",
        placeholder="Enter keywords, document number, entity name or phrases..."
    )

with c2:

    semantic = st.checkbox(
        "Semantic Search"
    )

with c3:

    top = st.selectbox(
        "Top Results",
        [5, 10, 20],
        index=0
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
                top=top
            )
            st.session_state.search_query = query
            st.session_state.search_semantic = semantic

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

        summary_placeholder = st.empty()
                
        st.markdown("### Search Results")
        
        # 1. Inject CSS to tighten up the vertical spacing (just like Action Centre)
        st.markdown("""
            <style>
            [data-testid="column"] { padding-bottom: 0rem !important; padding-top: 0rem !important; }
            </style>
        """, unsafe_allow_html=True)
        # 2. Draw the Master List Header
        hcols = st.columns([4, 3, 2, 2])
        hcols[0].markdown("**File Name**")
        hcols[1].markdown("**Entity Name**")
        hcols[2].markdown("**Date**")
        hcols[3].markdown("**Action**")
        st.markdown("<hr style='margin: 0.2rem 0; border: none; border-bottom: 1px solid rgba(200,200,200,0.3);'/>", unsafe_allow_html=True)
        # 3. Loop through results and draw the rows
        for i, r in enumerate(results, start=1):
            cols = st.columns([4, 3, 2, 2], gap="small")
            
            cols[0].write(r.get('file_name', 'N/A'))
            cols[1].write(r.get('entity_name', 'N/A'))
            cols[2].write(str(r.get('document_date', 'N/A')))
            
            if cols[3].button("View Document", key=f"view_doc_{i}", use_container_width=True):
                st.session_state.preview_doc = r
                st.switch_page("pages/3_Document Viewer.py")
            st.markdown("<hr style='margin: 0.2rem 0; border: none; border-bottom: 1px solid rgba(200,200,200,0.3);'/>", unsafe_allow_html=True)
        # 5. Fetch the AI Summary exactly once after the loop finishes
        with summary_placeholder.container():
            # Only generate summary if it hasn't been generated yet for this specific query
            summary_cache_key = f"summary_{query}_{semantic}"
            if summary_cache_key not in st.session_state:
                with st.spinner("✨ Generating AI Summary..."):
                    summary = get_summary(
                        search_results=results, 
                        user_query=query, 
                        semantic_search=semantic
                    )
                    st.session_state[summary_cache_key] = summary
            else:
                summary = st.session_state[summary_cache_key]
                
            if summary and "error" not in summary:
                st.markdown("### ✨ AI Synthesis")
                st.info(summary)

st.markdown("---")

st.subheader(
    "Recent Processing Logs"
)

logs = get_logs()

if logs.empty:

    st.info(
        "No logs available."
    )

else:

    display = logs.copy()

    keep_cols = []

    for c in [
        "Timestamp",
        "File Name",
        "Status",
        "Processing Time (s)"
    ]:

        if c in display.columns:

            keep_cols.append(
                c
            )

    display = display[
        keep_cols
    ]

    st.dataframe(
        display.tail(20),
        width="stretch",
        hide_index=True,
        height=350
    )
