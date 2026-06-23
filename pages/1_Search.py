import os
import streamlit as st
import pandas as pd

from src.search.search_service import search_documents
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
            
            if isinstance(results, list):

                if not results:
                    st.info("No documents found.")

                else:
                    for i, r in enumerate(results, start=1):
                        ...
            else:
                st.error(results)

            for i, r in enumerate(
                results,
                start=1
            ):

                with st.container():

                    st.markdown(
                        f"### Result {i}"
                    )

                    st.markdown(
                        f"**File Name:** "
                        f"{r.get('file_name', 'N/A')}"
                    )

                    c1, c2, c3 = st.columns(
                        3
                    )

                    with c1:

                        st.metric(
                            "Document Type",
                            r.get(
                                "document_type",
                                "N/A"
                            )
                        )

                        st.metric(
                            "Document Number",
                            r.get(
                                "document_number",
                                "N/A"
                            )
                        )

                    with c2:

                        st.metric(
                            "Entity",
                            r.get(
                                "entity_name",
                                "N/A"
                            )
                        )

                        st.metric(
                            "Date",
                            str(
                                r.get(
                                    "document_date",
                                    "N/A"
                                )
                            )
                        )

                    with c3:

                        st.metric(
                            "Search Score",
                            round(
                                r.get(
                                    "score",
                                    0
                                ),
                                3
                            )
                        )

                        st.metric(
                            "Title",
                            r.get(
                                "document_title",
                                "N/A"
                            )
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
                            sharepoint_url,
                            width="stretch"
                        )

                    st.markdown(
                        "---"
                    )

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