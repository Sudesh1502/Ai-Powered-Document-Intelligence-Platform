import streamlit as st
import pandas as pd

from src.search.search_service import search_documents
from src.utils.logger import get_logs

st.set_page_config(
    page_title="Search",
    page_icon="🔍",
    layout="wide"
)

st.title("Document Search")
st.caption(
    "Search indexed documents using keyword and semantic search."
)

st.markdown("---")

c1, c2, c3 = st.columns([5, 2, 2])

with c1:
    query = st.text_input(
        "Search Query",
        placeholder="Enter keywords..."
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
    use_container_width=True
):

    if not query.strip():
        st.warning(
            "Please enter a search query."
        )

    else:

        with st.spinner(
            "Searching documents..."
        ):

            results = search_documents(
                query=query,
                use_semantic_ranker=semantic,
                top=top
            )

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

            st.success(
                f"{len(results)} document(s) found."
            )

            st.markdown("---")

            for r in results:

                with st.expander(
                    r.get(
                        "file_name",
                        "Document"
                    )
                ):

                    col1, col2 = st.columns(2)

                    with col1:

                        st.write(
                            f"**Title:** "
                            f"{r.get('document_title', 'N/A')}"
                        )

                        st.write(
                            f"**Document Type:** "
                            f"{r.get('document_type', 'N/A')}"
                        )

                        st.write(
                            f"**Document Number:** "
                            f"{r.get('document_number', 'N/A')}"
                        )

                    with col2:

                        st.write(
                            f"**Entity:** "
                            f"{r.get('entity_name', 'N/A')}"
                        )

                        st.write(
                            f"**Score:** "
                            f"{round(r.get('score', 0), 3)}"
                        )

                        st.write(
                            f"**Date:** "
                            f"{r.get('document_date', 'N/A')}"
                        )

                    captions = r.get(
                        "semantic_captions",
                        []
                    )

                    if captions:

                        st.markdown(
                            "##### Semantic Summary"
                        )

                        st.info(
                            "\n".join(
                                captions
                            )
                        )

                    sharepoint_url = r.get(
                        "sharepoint_url",
                        ""
                    )

                    if sharepoint_url:

                        st.link_button(
                            "Open Document",
                            sharepoint_url
                        )

st.markdown("---")

st.subheader(
    "Processing Logs"
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
            keep_cols.append(c)

    display = display[
        keep_cols
    ]

    st.dataframe(
        display.tail(20),
        use_container_width=True,
        hide_index=True
    )