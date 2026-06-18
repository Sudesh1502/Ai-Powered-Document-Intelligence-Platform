import streamlit as st
from datetime import datetime

from src.indexing.upload_document_service import (
    upload_documents
)
from src.utils.logger import (
    log_document_status
)

st.set_page_config(
    page_title="Human Review",
    page_icon="📝",
    layout="wide"
)

if "review_documents" not in st.session_state:
    st.session_state.review_documents = []

st.title(
    "Human Review Queue"
)

docs = st.session_state.review_documents

st.metric(
    "Pending Reviews",
    len(docs)
)

if not docs:

    st.info(
        "No documents waiting for review."
    )

else:

    for i, doc in enumerate(docs):

        st.markdown("---")

        left, right = st.columns(
            [2, 1]
        )

        with left:

            st.subheader(
                doc["file_name"]
            )

            st.text_area(
                "OCR Content",
                value=doc.get(
                    "content",
                    ""
                ),
                height=400,
                disabled=True,
                key=f"text_{i}"
            )

        with right:

            st.subheader(
                "Metadata Review"
            )

            document_type = st.text_input(
                "Document Type",
                value=doc.get(
                    "document_type",
                    ""
                ),
                key=f"type_{i}"
            )

            document_title = st.text_input(
                "Document Title",
                value=doc.get(
                    "document_title",
                    ""
                ),
                key=f"title_{i}"
            )

            document_number = st.text_input(
                "Document Number",
                value=doc.get(
                    "document_number",
                    ""
                ),
                key=f"number_{i}"
            )

            entity_name = st.text_input(
                "Entity",
                value=doc.get(
                    "entity_name",
                    ""
                ),
                key=f"entity_{i}"
            )

            document_date = st.text_input(
                "Date",
                value=str(
                    doc.get(
                        "document_date",
                        ""
                    )
                ),
                key=f"date_{i}"
            )

            st.info(
                f"Confidence : "
                f"{doc.get('confidence')}%"
            )

            st.warning(
                f"Status : "
                f"{doc.get('review_status', 'Review Required')}"
            )

            c1, c2 = st.columns(2)

            with c1:

                if st.button(
                    "Approve",
                    key=f"a_{i}"
                ):

                    doc[
                        "document_type"
                    ] = document_type

                    doc[
                        "document_title"
                    ] = document_title

                    doc[
                        "document_number"
                    ] = document_number

                    doc[
                        "entity_name"
                    ] = entity_name

                    doc[
                        "document_date"
                    ] = document_date

                    doc_to_upload = doc.copy()

                    doc_to_upload.pop(
                        "review_status",
                        None
                    )

                    upload_documents(
                        [doc_to_upload]
                    )

                    log_document_status(
                        file_name=doc[
                            "file_name"
                        ],
                        url="",
                        status="Completed",
                        note="Approved by Human Reviewer",
                        start_time=datetime.now(),
                        end_time=datetime.now()
                    )

                    docs.pop(i)

                    st.success(
                        "Document approved and indexed successfully."
                    )

                    st.rerun()

            with c2:

                if st.button(
                    "Reject",
                    key=f"r_{i}"
                ):

                    log_document_status(
                        file_name=doc[
                            "file_name"
                        ],
                        url="",
                        status="Rejected",
                        note="Rejected by Human Reviewer",
                        start_time=datetime.now(),
                        end_time=datetime.now()
                    )

                    docs.pop(i)

                    st.warning(
                        "Document rejected."
                    )

                    st.rerun()