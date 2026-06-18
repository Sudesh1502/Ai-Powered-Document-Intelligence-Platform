import streamlit as st
import tempfile
from datetime import datetime

from src.validation.file_validator import is_valid_file
from src.extraction.extraction_service import (
    extract_text,
    calculate_confidence
)
from src.extraction.metadata_service import (
    extract_metadata
)
from src.indexing.upload_document_service import (
    upload_documents
)
from src.utils.logger import (
    log_document_status,
    get_logs,
    get_metrics
)
from src.utils.review_service import (
    get_review_status
)
from src.utils.document_builder import (
    build_document
)

st.set_page_config(
    page_title="Document Intelligence Platform",
    page_icon="📄",
    layout="wide"
)

if "review_documents" not in st.session_state:
    st.session_state.review_documents = []

st.title(
    "AI Powered Document Intelligence Platform"
)

st.caption(
    "OCR • Metadata Extraction • Azure AI Search"
)

metrics = get_metrics()

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Documents Processed",
        metrics["processed"]
    )

with c2:
    st.metric(
        "Documents Indexed",
        metrics["indexed"]
    )

with c3:
    st.metric(
        "OCR Confidence",
        "--"
    )

with c4:
    st.metric(
        "Avg Processing Time",
        f"{metrics['avg_time']} sec"
    )

st.markdown("---")

st.subheader(
    "Upload Document"
)

uploaded_file = st.file_uploader(
    "Choose PDF/Image/DOCX",
    type=[
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "docx"
    ]
)

if uploaded_file:

    st.success(
        f"Uploaded: {uploaded_file.name}"
    )

    if st.button(
        "Process Document",
        use_container_width=True
    ):

        start_time = datetime.now()

        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix="." +
                uploaded_file.name.split(".")[-1]
            ) as tmp:

                tmp.write(
                    uploaded_file.read()
                )

                file_path = tmp.name

            if not is_valid_file(
                file_path
            ):

                st.error(
                    "Invalid file."
                )

                st.stop()

            with st.spinner(
                "Running OCR..."
            ):

                result = extract_text(
                    file_path
                )

            confidence = round(
                calculate_confidence(
                    result
                ) * 100,
                2
            )

            text = ""

            for page in result.pages:

                for line in page.lines:

                    text += (
                        line.content
                        + "\n"
                    )

            page_count = len(
                result.pages
            )

            st.subheader(
                "Extracted Text"
            )

            st.text_area(
                "OCR Output",
                value=text,
                height=300
            )

            st.subheader(
                "OCR Confidence"
            )

            st.progress(
                confidence / 100
            )

            st.info(
                f"Confidence: {confidence}%"
            )

            with st.spinner(
                "Extracting Metadata..."
            ):

                metadata = extract_metadata(
                    text
                )

            review_status = (
                get_review_status(
                    confidence,
                    metadata
                )
            )

            st.info(
                f"Review Status: "
                f"{review_status}"
            )

            st.subheader(
                "Document Information"
            )

            left, right = st.columns(2)

            with left:

                st.write(
                    f"**Document Type:** "
                    f"{metadata.get('document_type', 'N/A')}"
                )

                st.write(
                    f"**Document Title:** "
                    f"{metadata.get('document_title', 'N/A')}"
                )

                st.write(
                    f"**Document Number:** "
                    f"{metadata.get('document_number', 'N/A')}"
                )

            with right:

                st.write(
                    f"**Entity:** "
                    f"{metadata.get('entity_name', 'N/A')}"
                )

                st.write(
                    f"**Amount:** "
                    f"{metadata.get('amount', 'N/A')}"
                )

                st.write(
                    f"**Date:** "
                    f"{metadata.get('document_date', 'N/A')}"
                )

            with st.expander(
                "Additional Metadata"
            ):

                st.json(
                    metadata
                )

            document = build_document(
                uploaded_file=uploaded_file,
                metadata=metadata,
                text=text,
                page_count=page_count,
                confidence=confidence,
                review_status=review_status
            )

            if review_status == "Completed":

                with st.spinner(
                    "Uploading to Azure Search..."
                ):

                    upload_documents(
                        [document]
                    )

                status = "Completed"
                note = "Indexed Successfully"

                st.success(
                    "Document Indexed Successfully."
                )

            else:

                st.session_state.review_documents.append(
                    document
                )

                status = review_status
                note = "Waiting For Human Review"

                st.warning(
                    f"Document marked as "
                    f"'{review_status}'. "
                    f"Needs Human Review."
                )

            end_time = datetime.now()

            execution_time = round(
                (
                    end_time
                    -
                    start_time
                ).total_seconds(),
                2
            )

            log_document_status(
                file_name=uploaded_file.name,
                url=file_path,
                status=status,
                note=note,
                start_time=start_time,
                end_time=end_time
            )

            st.info(
                f"Execution Time: "
                f"{execution_time} sec"
            )

        except Exception as e:

            end_time = datetime.now()

            log_document_status(
                file_name=uploaded_file.name,
                url="",
                status="Failed",
                note=str(e),
                start_time=start_time,
                end_time=end_time
            )

            st.error(
                str(e)
            )

st.markdown("---")

st.subheader(
    "Recent Processing Activity"
)

logs = get_logs()

if logs.empty:

    st.info(
        "No logs available."
    )

else:

    keep_cols = []

    for c in [
        "Timestamp",
        "File Name",
        "Status",
        "Processing Time (s)"
    ]:

        if c in logs.columns:

            keep_cols.append(
                c
            )

    display = logs[
        keep_cols
    ]

    st.dataframe(
        display.tail(10),
        use_container_width=True,
        hide_index=True
    )