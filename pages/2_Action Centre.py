import os
import streamlit as st
from datetime import datetime
import shutil

from src.indexing.upload_document_service import (
    upload_documents
)

from src.utils.logger import (
    log_document_status
)

from src.utils.review_storage import (
    load_review_documents,
    remove_review_document
)

st.set_page_config(
    page_title="Action Centre",
    page_icon="📄",
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
        "Action Centre"
    )

    st.caption(
        "Review and validate documents that require manual intervention."
    )

st.markdown("---")

# Reverse so the newest documents appear at the top
docs = list(reversed(load_review_documents()))

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "Pending Reviews",
        len(docs)
    )

with c2:

    st.metric(
        "Approved Manually",
        st.session_state.get(
            "approved_count",
            0
        )
    )

with c3:

    st.metric(
        "Rejected",
        st.session_state.get(
            "rejected_count",
            0
        )
    )

st.markdown("---")

if not docs:

    st.info(
        "No documents waiting for review."
    )

else:

    for i, doc in enumerate(docs):

        st.markdown("---")

        left, right = st.columns(
            [3, 2]
        )

        # Exclusively read from data/ folder
        file_path = os.path.join(
            "data",
            doc["file_name"]
        )

        with left:

            st.subheader(
                doc["file_name"]
            )

            st.caption(
                "Document Preview"
            )

            if os.path.exists(
                file_path
            ):

                extension = os.path.splitext(
                    file_path
                )[1].lower()

                if extension in [
                    ".png",
                    ".jpg",
                    ".jpeg"
                ]:

                    st.image(
                        file_path,
                        use_container_width=True
                    )

                elif extension == ".pdf":

                    with open(
                        file_path,
                        "rb"
                    ) as pdf:

                        st.download_button(
                            "Open PDF",
                            data=pdf,
                            file_name=doc[
                                "file_name"
                            ],
                            use_container_width=True,
                            key=f"download_pdf_{i}"
                        )

                elif extension == ".docx":

                    with open(
                        file_path,
                        "rb"
                    ) as f:

                        st.download_button(
                            "Open DOCX",
                            data=f,
                            file_name=doc[
                                "file_name"
                            ],
                            use_container_width=True,
                            key=f"download_docx_{i}"
                        )

            else:

                st.warning(
                    "Original document not found."
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
                "Entity Name",
                value=doc.get(
                    "entity_name",
                    ""
                ),
                key=f"entity_{i}"
            )

            document_date = st.text_input(
                "Document Date",
                value=str(
                    doc.get(
                        "document_date",
                        ""
                    )
                ),
                key=f"date_{i}"
            )

            st.metric(
                "Confidence",
                f"{doc.get('confidence')}%"
            )

            st.write(
                f"Current Status : "
                f"{doc.get('review_status')}"
            )

            with st.expander(
                "Azure Search Document Preview"
            ):

                preview = doc.copy()

                preview.pop(
                    "review_status",
                    None
                )

                st.json(
                    preview
                )

            b1, b2 = st.columns(
                2
            )

            with b1:

                if st.button(
                    "Approve",
                    key=f"a_{i}",
                    use_container_width=True
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

                    doc_to_upload = (
                        doc.copy()
                    )

                    doc_to_upload.pop(
                        "review_status",
                        None
                    )

                    os.makedirs(
                        "data/",
                        exist_ok=True
                    )

                    # 1. Format the date properly for Azure Search (ISO 8601)
                    raw_date = str(doc_to_upload.get("document_date", ""))

                    if raw_date and raw_date.strip() not in ["", "None"]:
                        if "T" not in raw_date:
                            doc_to_upload["document_date"] = f"{raw_date.strip()}T00:00:00Z"
                    else:
                        doc_to_upload["document_date"] = None

                    # 2. ACTUALLY upload the document to the Search Index!
                    try:
                        upload_documents([doc_to_upload])
                    except Exception as e:
                        st.error(f"Failed to upload to Azure Search: {e}")
                        st.stop()  # Stop the process so it doesn't falsely show success

                    # (Removed old shutil.move block)

                    log_document_status(
                        file_name=doc[
                            "file_name"
                        ],
                        url=file_path,
                        status="Approved Manually",
                        note="Reviewed and indexed by human reviewer",
                        start_time=datetime.now(),
                        end_time=datetime.now()
                    )

                    st.session_state[
                        "approved_count"
                    ] = (
                        st.session_state.get(
                            "approved_count",
                            0
                        )
                        + 1
                    )

                    remove_review_document(
                        doc["id"]
                    )

                    st.success(
                        "Document approved and indexed successfully."
                    )

                    st.rerun()

            with b2:

                if st.button(
                    "Reject",
                    key=f"r_{i}",
                    use_container_width=True
                ):

                    log_document_status(
                        file_name=doc[
                            "file_name"
                        ],
                        url=file_path,
                        status="Rejected",
                        note="Rejected by human reviewer",
                        start_time=datetime.now(),
                        end_time=datetime.now()
                    )

                    st.session_state[
                        "rejected_count"
                    ] = (
                        st.session_state.get(
                            "rejected_count",
                            0
                        )
                        + 1
                    )

                    remove_review_document(
                        doc["id"]
                    )

                    st.warning(
                        "Document rejected."
                    )

                    st.rerun()