import os
import streamlit as st
import tempfile
from datetime import datetime
import shutil
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
from src.utils.review_storage import (
    add_review_document
)

st.set_page_config(
    page_title="Document Intelligence Platform",
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
        "AI Powered Document Intelligence Platform"
    )

    st.caption(
        "Transforming unstructured documents into searchable business intelligence."
    )

st.markdown("---")

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

st.markdown(
    "## 📤 Upload Document"
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

            file_bytes = uploaded_file.getvalue()

            os.makedirs("data", exist_ok=True)
            file_path = os.path.join("data", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(file_bytes)

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

            text = result.content

            page_count = len(result.pages) if result.pages else 0

            st.markdown(
                "## 📄 Extracted Text"
            )

            st.text_area(
                "OCR Output",
                value=text,
                height=300
            )

            st.markdown(
                "## 🎯 OCR Confidence"
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

            st.markdown(
                "## 🏷️ Extracted Metadata"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "Document Type",
                    metadata.get(
                        "document_type",
                        "N/A"
                    )
                )

                st.metric(
                    "Document Number",
                    metadata.get(
                        "document_number",
                        "N/A"
                    )
                )

            with c2:

                st.metric(
                    "Entity",
                    metadata.get(
                        "entity_name",
                        "N/A"
                    )
                )


            with c3:

                st.metric(
                    "Date",
                    str(
                        metadata.get(
                            "document_date",
                            "N/A"
                        )
                    )
                )

                st.metric(
                    "Pages",
                    page_count
                )

            if "error" in metadata:

                st.error(
                    metadata[
                        "error"
                    ]
                )

            else:

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

            with st.expander(
                "Azure Search Document Preview"
            ):

                preview = document.copy()

                preview.pop(
                    "review_status",
                    None
                )

                st.json(
                    preview
                )

            if review_status == "Completed":

                with st.spinner(
                    "Uploading to Azure Search..."
                ):

                    upload_documents(
                        [document]
                    )

                # Removed folder creation and file moving to keep files in data/
                pass

                status = "Completed"
                note = "Indexed Automatically"

                st.success(
                    "✅ Document Indexed Successfully."
                )

            else:

                add_review_document(
                    document
                )

                status = review_status
                note = "Waiting for manual review"

                st.warning(
                    f"Document marked as "
                    f"'{review_status}'. "
                    f"Go to the Action Centre for review."
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

st.markdown(
    "## 📊 Recent Processing Activity"
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

    # Sort by Timestamp descending so newest is at the top
    if "Timestamp" in display.columns:
        display = display.sort_values(by="Timestamp", ascending=False)

    display = display.head(20)

    selected_file = st.selectbox(
        "Open Document",
        ["Select a file"] +
        display["File Name"].tolist()
    )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        height=300
    )
    if selected_file != "Select a file":

        source_file = os.path.join(
            "data",
            selected_file
        )

        processed_file = os.path.join(
            "app_data",
            "processed_docs",
            selected_file
        )

        if os.path.exists(
            processed_file
        ):

            file_path = processed_file

        elif os.path.exists(
            source_file
        ):

            file_path = source_file

        else:

            file_path = None

        if file_path:

            st.markdown("---")
            st.subheader(
                f"Document Preview : {selected_file}"
            )

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
                        pdf,
                        file_name=selected_file,
                        use_container_width=True
                    )

            elif extension == ".docx":

                with open(
                    file_path,
                    "rb"
                ) as doc:

                    st.download_button(
                        "Open DOCX",
                        doc,
                        file_name=selected_file,
                        use_container_width=True
                    )

        else:

            st.warning(
                "Document file not found."
            )