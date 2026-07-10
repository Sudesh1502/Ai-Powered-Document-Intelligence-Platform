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
from src.utils.blob_service import (
    upload_to_blob,
    generate_sas_url
)
from src.utils.review_storage import (
    add_review_document
)
from src.validation.validation_engine import validate_document_orchestrator
from src.utils.review_storage import add_review_document
st.set_page_config(
    page_title="Document Intelligence Platform",
    page_icon="📄",
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
    st.title("AI Powered Document Intelligence Platform")
    st.caption("Transforming unstructured documents into searchable business intelligence.")

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

uploaded_files = st.file_uploader(
    "Choose PDF/Image/DOCX",
    type=[
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "docx"
    ],
    accept_multiple_files=True
)

if uploaded_files:
    if len(uploaded_files) > 5:
        st.error("⚠️ Maximum 5 documents allowed per batch. Please remove some files.")
        st.stop()

    st.success(f"Uploaded: {len(uploaded_files)} document(s)")
    is_policy_doc = st.toggle("This is a Policy Master Document")

    if st.button(
        "Process Documents",
        width="stretch"
    ):
        success_count = 0
        action_centre_count = 0
        failed_count = 0

        for uploaded_file in uploaded_files:
            with st.status(f"📄 Processing: {uploaded_file.name}", expanded=True) as status_container:

                start_time = datetime.now()

                try:

                    file_bytes = uploaded_file.getvalue()

                    from src.indexing.duplicate_detection_service import DuplicateDetectionService
                    dedupe_service = DuplicateDetectionService()

                    if dedupe_service.is_exact_duplicate(file_bytes):
                        st.warning("Exact duplicate document detected. Skipping.")
                        status_container.update(label=f"⏭️ Skipped Duplicate: {uploaded_file.name}", state="complete", expanded=False)
                        continue

                    os.makedirs("data", exist_ok=True)
                    if not is_valid_file(
                        uploaded_file.name
                    ):

                        st.error(
                            "Invalid file."
                        )

                        status_container.update(label=f"❌ Invalid: {uploaded_file.name}", state="error", expanded=False)
                        failed_count += 1
                        continue

                    with st.spinner(
                        "Running OCR..."
                    ):

                        result = extract_text(
                            file_bytes
                        )
                        word_count = len(result.content.split()) if result.content else 0
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
                        height=300,
                        key=f"ocr_output_{uploaded_file.name}"
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
                        if is_policy_doc:
                            from src.extraction.metadata_service import extract_policy_metadata
                            metadata = extract_policy_metadata(text)
                            target_index = "policy-master-index"
                        else:
                            metadata = extract_metadata(text)
                            target_index = "generic-documents-index"

                    # Upload to Azure Blob Storage EARLY so that even rejected/duplicate documents can be previewed in the Action Centre
                    unique_blob_name = upload_to_blob(file_bytes, uploaded_file.name)
                    if not is_policy_doc:
                        metadata["sharepoint_url"] = unique_blob_name
                        
                        # Layer 2 & 3: Near-Duplicate (MinHash/pHash) and Data-Level Duplicate Detection
                        is_near_dup = dedupe_service.is_near_duplicate(text, file_bytes, uploaded_file.name)
                        is_data_dup = dedupe_service.is_data_level_duplicate(metadata)
                        
                        if is_near_dup or is_data_dup:
                            reason = "Near-Duplicate (Text Similarity)" if is_near_dup else "Data-Level Duplicate (Matching ID & Vendor)"
                            st.warning(f"**Duplicate Detected!** {reason}. Routed to Action Centre.")
                            
                            metadata["file_name"] = uploaded_file.name
                            metadata["review_reason"] = f"Duplicate Detected - {reason}"
                            metadata["status"] = "Needs Review"
                            add_review_document(metadata)
                            
                            log_document_status(
                                file_name=uploaded_file.name,
                                url="Streamlit Upload",
                                status="Needs Review",
                                note=f"Duplicate routed to action centre: {reason}",
                                start_time=start_time,
                                end_time=datetime.now(),
                                word_count=word_count,
                            )
                            
                            status_container.update(label=f"⚠️ Action Centre (Duplicate): {uploaded_file.name}", state="complete", expanded=False)
                            action_centre_count += 1
                            continue

                        review_status = (
                            get_review_status(
                                confidence,
                                metadata
                            )
                        )
                    else:
                        review_status = "Completed"

                    if is_policy_doc:
                        # Policies bypass structural validation
                        validation_results = {"missing": [], "invalid": []}
                    else:
                        validation_results = validate_document_orchestrator(metadata)
                    
                    missing_fields = validation_results["missing"]
                    invalid_fields = validation_results["invalid"]
            
                    if len(missing_fields) > 0 or len(invalid_fields) > 0:
                        reasons = []
                        if missing_fields:
                            reasons.append(f"Missing: {', '.join(missing_fields)}")
                        if invalid_fields:
                            reasons.append(f"Invalid Format: {', '.join(invalid_fields)}")
                        reason_str = " | ".join(reasons)
                
                        # 3. Give the user INSTANT visual feedback on the screen!
                        st.error(f"**Validation Failed!** {reason_str}")
                        st.warning("This document has been routed to the Action Centre for manual review.")
                        # 4. Save it to the queue
                        metadata["file_name"] = uploaded_file.name
                        metadata["review_reason"] = f"Validation Failed - {reason_str}"
                        metadata["status"] = "Needs Review"
                        add_review_document(metadata)
                
                        # Log the failure so it appears in metrics
                        log_document_status(
                            file_name=uploaded_file.name,
                            url="Streamlit Upload",
                            status="Needs Review",
                            note=f"Validation failed. {reason_str}",
                            start_time=start_time,
                            end_time=datetime.now(),
                            word_count=0,
                        )
                
                        # 5. Continue to the next file instead of stopping the batch
                        status_container.update(label=f"⚠️ Action Centre: {uploaded_file.name}", state="complete", expanded=False)
                        action_centre_count += 1
                        continue

                    # Cross Validation against Policy Master Index
                    if not is_policy_doc:
                        doc_type = metadata.get("document_type", "").lower()
                        if doc_type in ["major claim", "claim form", "claim closure", "claim settlement"]:
                            from src.validation.cross_validation_service import cross_validate_claim
                            breach_errors = cross_validate_claim(metadata)
                            
                            if breach_errors:
                                reason_str = " | ".join(breach_errors)
                                st.error(f"**Policy Breach!** {reason_str}")
                                st.warning("This document breached a Master Policy rule and has been routed to the Action Centre.")
                                metadata["file_name"] = uploaded_file.name
                                metadata["review_reason"] = f"Policy Breach - {reason_str}"
                                metadata["status"] = "Needs Review"
                                add_review_document(metadata)
                                
                                log_document_status(
                                    file_name=uploaded_file.name,
                                    url="Streamlit Upload",
                                    status="Needs Review",
                                    note=f"Policy Breach. {reason_str}",
                                    start_time=start_time,
                                    end_time=datetime.now(),
                                    word_count=0,
                                )
                                status_container.update(label=f"⚠️ Action Centre (Policy Breach): {uploaded_file.name}", state="complete", expanded=False)
                                action_centre_count += 1
                                continue

                    if not is_policy_doc:
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

                    user_info = {
                        "user_id": user.get("user_id", ""),
                        "email": user.get("email", ""),
                        "name": user.get("name", ""),
                        "uploaded_at": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    # Option B: Inject user tracking directly into the metadata blob
                    
                    # Store fingerprints directly inside the metadata JSON blob
                    if not is_policy_doc:
                        metadata["user_tracking"] = user_info
                        metadata["sha256_signature"] = dedupe_service.generate_sha256_hash(file_bytes)
                        metadata["minhash_signature"] = dedupe_service.generate_minhash(text)
                        metadata["phash_signature"] = dedupe_service.generate_phash(file_bytes, uploaded_file.name)
                    
                    # (Blob upload moved to the top of the pipeline)
                    # Build the document payload based on the index schema
                    if is_policy_doc:
                        from src.utils.document_builder import build_policy_document
                        
                        policies = metadata if isinstance(metadata, list) else [metadata]
                        documents = []
                        
                        st.markdown(f"### 📋 Extracted Policies ({len(policies)} Found)")
                        
                        table_data = []
                        for pol in policies:
                            table_data.append({
                                "Policy Number": pol.get("policy_number", "N/A"),
                                "Insured Name": pol.get("insured_name", "N/A"),
                                "Class": pol.get("class_of_business", "N/A"),
                                "Limit": pol.get("policy_limit", 0)
                            })
                        st.dataframe(table_data, use_container_width=True)
                        
                        for policy_meta in policies:
                            policy_meta["sharepoint_url"] = unique_blob_name
                            documents.append(build_policy_document(uploaded_file, policy_meta))
                            
                    else:
                        documents = [build_document(
                            uploaded_file=uploaded_file,
                            metadata=metadata,
                            text=text,
                            page_count=page_count,
                            confidence=confidence,
                            review_status=review_status
                        )]
                        
                        with st.expander("Azure Search Document Preview"):
                            preview = documents[0].copy()
                            preview.pop("review_status", None)
                            st.json(preview)

                    if review_status == "Completed":

                        with st.spinner("Uploading to Azure Search..."):
                            upload_documents(documents, index_name=target_index)
                        
                        # Log the hashes to Azure Table Storage to prevent future duplicates
                        doc_id = documents[0].get("id", "") if len(documents) > 0 else ""
                        dedupe_service.log_document(file_bytes, doc_id, text, uploaded_file.name)

                        # Removed folder creation and file moving to keep files in data/
                        pass

                        status = "Completed"
                        note = "Indexed Automatically"

                        st.success(
                            "✅ Document Indexed Successfully."
                        )
                        status_container.update(label=f"✅ Completed: {uploaded_file.name}", state="complete", expanded=False)
                        success_count += 1

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
                        status_container.update(label=f"⚠️ Action Centre: {uploaded_file.name}", state="complete", expanded=False)

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
                        url=unique_blob_name,
                        status=status,
                        note=note,
                        start_time=start_time,
                        end_time=end_time,
                        word_count=word_count
                    )

                    st.info(
                        f"Execution Time: "
                        f"{execution_time} sec"
                    )

                except Exception as e:
                    status_container.update(label=f"❌ Failed: {uploaded_file.name}", state="error", expanded=False)
                    failed_count += 1
                    end_time = datetime.now()

                    log_document_status(
                        file_name=uploaded_file.name,
                        url="",
                        status="Failed",
                        note=str(e),
                        start_time=start_time,
                        end_time=end_time,
                        word_count=word_count
                    )

                    st.error(
                        str(e)
                    )


        # --- End of Batch Summary ---
        st.markdown("### 📊 Batch Upload Summary")
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("✅ Indexed Successfully", success_count)
        sc2.metric("⚠️ Action Centre", action_centre_count)
        sc3.metric("❌ Failed", failed_count)


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
        width="stretch",
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
                    width="stretch"
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
                        width="stretch"
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
                        width="stretch"
                    )

        else:

            st.warning(
                "Document file not found."
            )

