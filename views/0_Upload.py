import os
import streamlit as st
from src.auth.auth_service import login_user

user = login_user()
import tempfile
from datetime import datetime
from src.utils.time_utils import get_ist_now
import shutil
from src.validation.file_validator import is_valid_file
from src.extraction.extraction_service import (
    extract_text
)
from src.utils.ocr_scoring import calculate_weighted_confidence
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
# --- Render Custom Top Header with Heading and Logo ---
import base64
logo_path = "views/LOGO.png"
if os.path.exists(logo_path):
    with open(logo_path, "rb") as img_file:
        b64_logo = base64.b64encode(img_file.read()).decode()
    logo_html = f"<img src='data:image/png;base64,{b64_logo}' style='height: 60px; margin-right: 20px; vertical-align: middle;' />"
else:
    logo_html = ""

st.markdown(f"""
    <div style='display: flex; align-items: center; margin-bottom: 15px; margin-top: 10px;'>
        {logo_html}
        <div>
            <h2 style='margin:0; font-family: Outfit, sans-serif; color: #0F172A; font-size: 1.7rem; line-height: 1.2;'>AI Powered Document Intelligence Platform</h2>
            <p style='margin: 4px 0 0 0; color: #64748B; font-size: 13.5px;'>Transforming unstructured documents into searchable business intelligence with enterprise-grade precision.</p>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<hr style='margin: 0 0 1.5rem 0; border: none; border-bottom: 1px solid #E2E8F0;'/>", unsafe_allow_html=True)

@st.fragment(run_every="5s")
def render_real_time_metrics():
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
            f"{metrics['avg_confidence']}%"
        )

    with c4:

        st.metric(
            "Avg Processing Time",
            f"{metrics['avg_time']} sec"
        )

render_real_time_metrics()

st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

st.markdown("<h3 style='font-family: Outfit, sans-serif; color: #0F172A; font-size: 1.3rem; margin-bottom: 1rem;'>⬆️ Upload Document</h3>", unsafe_allow_html=True)

with st.form("upload_form", clear_on_submit=True):
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

    is_policy_doc = st.toggle("This is a Policy Master Document")
    submitted = st.form_submit_button("Process Documents →", type="primary", use_container_width=True)

if submitted and uploaded_files:
    if len(uploaded_files) > 5:
        st.error("⚠️ Maximum 5 documents allowed per batch. Please remove some files.")
        st.stop()

    st.success(f"Processing {len(uploaded_files)} document(s)")
    
    processing_area = st.empty()
    with processing_area.container():
        success_count = 0
        action_centre_count = 0
        failed_count = 0
    
        for uploaded_file in uploaded_files:
            with st.status(f"📄 Processing: {uploaded_file.name}", expanded=True) as status_container:
    
                start_time = get_ist_now()
                confidence = 0.0
    
                try:
    
                    file_bytes = uploaded_file.getvalue()
    
                    from src.indexing.duplicate_detection_service import DuplicateDetectionService
                    dedupe_service = DuplicateDetectionService()
    
                    if dedupe_service.is_exact_duplicate(file_bytes):
                        st.warning("Exact duplicate document detected. Skipping.")
                        status_container.update(label=f"⏭️ Skipped Duplicate: {uploaded_file.name}", state="complete", expanded=False)
                        
                        # Upload to Blob Storage for audit trail purposes
                        blob_url = upload_to_blob(file_bytes, uploaded_file.name)
                        sas_url = generate_sas_url(blob_url)
                        
                        log_document_status(
                            file_name=uploaded_file.name,
                            url=sas_url,
                            status="Rejected",
                            note="Exact duplicate document detected. Processing aborted.",
                            start_time=get_ist_now(),
                            end_time=get_ist_now(),
                            word_count=0,
                            confidence=0.0,
                            source="Streamlit UI"
                        )
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
    
                        extension = os.path.splitext(uploaded_file.name)[1].lower()
                        result = extract_text(
                            file_bytes, extension=extension
                        )
                        word_count = len(result.content.split()) if result.content else 0
                    ocr_analysis = calculate_weighted_confidence(result)
                    confidence = round(ocr_analysis.get("weighted_score", 0.0), 2)
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
                        "## ⭕ OCR Confidence"
                    )
    
                    # Ensure it is passed as a valid float [0.0, 1.0] to avoid type errors in older Streamlit versions
                    st.progress(
                        confidence / 100.0
                    )
    
                    st.info(
                        f"Confidence: {confidence}%"
                    )
    
                    # ---------------------------------------------------------
                    # EARLY STOP: Near-Duplicate Detection (Saves Gemini Cost)
                    # ---------------------------------------------------------
                    is_near_dup = dedupe_service.is_near_duplicate(text, file_bytes, uploaded_file.name)
                    if is_near_dup:
                        reason = "Near-Duplicate (Text Similarity)"
                        st.warning(f"**Duplicate Detected!** {reason}. Routed to Action Centre.")
                        
                        unique_blob_name = upload_to_blob(file_bytes, uploaded_file.name)
                        metadata = {
                            "file_name": uploaded_file.name,
                            "document_title": uploaded_file.name,
                            "review_reason": f"Duplicate Detected - {reason}",
                            "status": "Needs Review",
                            "source": "Manual Ingestion",
                            "sharepoint_url": unique_blob_name
                        }
                        
                        add_review_document(metadata)
                        log_document_status(
                            file_name=uploaded_file.name,
                            url="Streamlit Upload",
                            status="Needs Review",
                            note=f"Duplicate routed to action centre: {reason}",
                            start_time=start_time,
                            end_time=get_ist_now(),
                            word_count=word_count,
                            confidence=confidence,
                            source="Streamlit UI"
                        )
                        status_container.update(label=f"⚠️ Action Centre (Duplicate): {uploaded_file.name}", state="complete", expanded=False)
                        action_centre_count += 1
                        continue
    
                    # Register hashes early so that duplicate detection works even if the document fails validation or is routed to Action Centre
                    dedupe_service.log_document(file_bytes, "", text, uploaded_file.name)
    
    
                    with st.spinner(
                        "Extracting Metadata..."
                    ):
                        user_id = user.get("user_id", "default_global") if user else "default_global"
                        if is_policy_doc:
                            from src.extraction.metadata_service import extract_policy_metadata
                            metadata = extract_policy_metadata(text, user_id)
                            target_index = "policy-master-index"
                        else:
                            metadata = extract_metadata(text, user_id)
                            target_index = "generic-documents-index"
                            
                        # Tag source for Action Centre tracking and keep Abhishek's flagged_tokens addition
                        if isinstance(metadata, list):
                            for item in metadata:
                                item["source"] = "Manual Ingestion"
                                item["flagged_tokens"] = ocr_analysis.get("flagged_tokens", [])
                        else:
                            metadata["source"] = "Manual Ingestion"
                            metadata["flagged_tokens"] = ocr_analysis.get("flagged_tokens", [])
    
                    # Upload to Azure Blob Storage EARLY so that even rejected/duplicate documents can be previewed in the Action Centre
                    unique_blob_name = upload_to_blob(file_bytes, uploaded_file.name)
                    if not is_policy_doc:
                        metadata["sharepoint_url"] = unique_blob_name
                        
                        # Layer 3: Data-Level Duplicate Detection (Requires Metadata)
                        is_data_dup = dedupe_service.is_data_level_duplicate(metadata)
                        
                        if is_data_dup:
                            reason = "Data-Level Duplicate (Matching ID & Vendor)"
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
                                end_time=get_ist_now(),
                                word_count=word_count,
                                confidence=confidence,
                                source="Streamlit UI"
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
                            end_time=get_ist_now(),
                            word_count=0,
                            confidence=confidence,
                            source="Streamlit UI"
                        )
                
                        # 5. Continue to the next file instead of stopping the batch
                        status_container.update(label=f"⚠️ Action Centre: {uploaded_file.name}", state="complete", expanded=False)
                        action_centre_count += 1
                        continue
    
                    # Cross Validation against Policy Master Index
                    if not is_policy_doc:
                        doc_type = metadata.get("document_type", "").lower()
                        if doc_type in ["major claim", "claim form", "claim closure", "claim closure report", "claim settlement"]:
                            from src.validation.cross_validation_service import cross_validate_claim
                            user_id = user.get("user_id", "default_global") if user else "default_global"
                            breach_errors = cross_validate_claim(metadata, user_id)
                            
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
                                    end_time=get_ist_now(),
                                    word_count=0,
                                    confidence=confidence,
                                    source="Streamlit UI"
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
                            # Clean up metadata before upload to Azure Search
                            docs_to_upload = []
                            for doc in documents:
                                doc_copy = doc.copy()
                                if "metadata" in doc_copy:
                                    try:
                                        import json
                                        meta_dict = json.loads(doc_copy["metadata"])
                                        meta_dict.pop("flagged_tokens", None)
                                        doc_copy["metadata"] = json.dumps(meta_dict)
                                    except Exception:
                                        pass
                                docs_to_upload.append(doc_copy)
                                
                            upload_documents(docs_to_upload, index_name=target_index)
                        
                        status = "Completed"
                        note = "Indexed Automatically"
    
                        st.success(
                            "✅ Document Indexed Successfully."
                        )
                        status_container.update(label=f"✅ Completed: {uploaded_file.name}", state="complete", expanded=False)
                        success_count += 1
    
                    elif review_status == "Failed":
                        st.error(f"❌ Document Rejected: OCR Confidence is too low ({confidence}%).")
                        status = "Failed"
                        note = "Rejected due to extremely low confidence"
                        status_container.update(label=f"❌ Rejected: {uploaded_file.name}", state="error", expanded=False)
                        
                    else: # "Needs Review"
    
                        metadata["file_name"] = uploaded_file.name
                        metadata["status"] = "Needs Review"
                        metadata["review_reason"] = f"Low OCR Confidence ({confidence}%)"
                        add_review_document(metadata)
    
                        status = review_status
                        note = "Waiting for manual review"
    
                        st.warning(
                            f"Document marked as "
                            f"'{review_status}'. "
                            f"Go to the Action Centre for review."
                        )
                        status_container.update(label=f"⚠️ Action Centre: {uploaded_file.name}", state="complete", expanded=False)
                    end_time = get_ist_now()
    
                    execution_time = round(
                        (
                            end_time
                            -
                            start_time
                        ).total_seconds(),
                        2
                    )
    
                    # GLOBALLY log the hashes to Azure Table Storage for ALL ingested documents
                    # to prevent future exact/near duplicates, even if routed to Action Centre.
                    doc_id = documents[0].get("id", "") if "documents" in locals() and len(documents) > 0 else ""
                    dedupe_service.log_document(file_bytes, doc_id, text, uploaded_file.name)
                    
                    sas_url = generate_sas_url(unique_blob_name) if "unique_blob_name" in locals() and unique_blob_name else ""
                    log_document_status(
                        file_name=uploaded_file.name,
                        url=sas_url,
                        status=status,
                        note=note,
                        start_time=start_time,
                        end_time=end_time,
                        word_count=word_count,
                        confidence=confidence,
                        source="Streamlit UI"
                    )
    
                    st.info(
                        f"Execution Time: "
                        f"{execution_time} sec"
                    )
    
                except Exception as e:
                    status_container.update(label=f"❌ Failed: {uploaded_file.name}", state="error", expanded=False)
                    failed_count += 1
                    end_time = get_ist_now()
    
                    log_document_status(
                        file_name=uploaded_file.name,
                        url="",
                        status="Failed",
                        note=str(e),
                        start_time=start_time,
                        end_time=end_time,
                        word_count=word_count,
                        confidence=confidence,
                        source="Streamlit UI"
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
    



# Render Custom Recent Processing Activity Card Layout (No indentation to prevent markdown code blocks)
logs = get_logs()

if logs.empty:
    st.info("No logs available.")
else:
    # 1. Rename the 'Note' column from the CSV to 'Reason' so your code can use it
    logs = logs.rename(columns={"Note": "Reason"})
    
    keep_cols = []
    for c in ["Timestamp", "File Name", "Status", "Reason", "Processing Time (s)"]:
        if c in logs.columns:
            keep_cols.append(c)

    display = logs[keep_cols]
    if "Timestamp" in display.columns:
        display = display.sort_values(by="Timestamp", ascending=False)

    display = display.head(100) # Increased to 100 records to support scrolling through history

    # Generate custom HTML table for pixel-perfect match with scrollable overflow container
    html_table = """<div style='background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; box-shadow: 0px 4px 12px rgba(0,0,0,0.02); padding: 1.5rem; margin-bottom: 1.5rem;'>
<div style='display: flex; align-items: center; gap: 10px; margin-bottom: 20px;'>
<span style='font-size: 20px;'>🕒</span>
<h3 style='margin: 0; font-family: Outfit, sans-serif; color: #002060; font-size: 1.3rem;'>Recent Processing Activity</h3>
</div>
<div style='max-height: 420px; overflow-y: auto; border: 1px solid #F1F5F9; border-radius: 6px;'>
<table style='width: 100%; border-collapse: collapse; font-family: Inter, sans-serif; font-size: 14px;'>
<thead>
<tr style='background-color: #F8FAFC; border-bottom: 1px solid #E2E8F0; text-align: left; position: sticky; top: 0; z-index: 10;'>
<th style='padding: 12px; color: #64748B; font-weight: 600; font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase; background-color: #F8FAFC; width: 160px; white-space: nowrap;'>Timestamp</th>
<th style='padding: 12px; color: #64748B; font-weight: 600; font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase; background-color: #F8FAFC; min-width: 200px;'>File Name</th>
<th style='padding: 12px; color: #64748B; font-weight: 600; font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase; background-color: #F8FAFC; width: 130px; text-align: center; white-space: nowrap;'>Status</th>
<th style='padding: 12px; color: #64748B; font-weight: 600; font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase; background-color: #F8FAFC; min-width: 250px;'>Reason</th>
<th style='padding: 12px; color: #64748B; font-weight: 600; font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase; background-color: #F8FAFC; width: 150px; text-align: right; white-space: nowrap;'>Processing Time (s)</th>
</tr>
</thead>
<tbody>"""

    for idx, row in display.iterrows():
        status = row.get("Status", "Unknown")
        if status == "Rejected":
            badge = "<span style='background-color: #FEE2E2; color: #991B1B; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; font-family: Inter, sans-serif; display: inline-block; white-space: nowrap;'>Rejected</span>"
        elif status == "Needs Review":
            badge = "<span style='background-color: #0F172A; color: #FFFFFF; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; font-family: Inter, sans-serif; display: inline-block; white-space: nowrap;'>Needs Review</span>"
        elif status == "Completed":
            badge = "<span style='background-color: #D1FAE5; color: #065F46; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; font-family: Inter, sans-serif; display: inline-block; white-space: nowrap;'>Completed</span>"
        else:
            badge = f"<span style='background-color: #F1F5F9; color: #475569; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; font-family: Inter, sans-serif; display: inline-block; white-space: nowrap;'>{status}</span>"

        time_val = row.get("Processing Time (s)", "0")
        
        # Get the renamed 'Reason' value and display it in the 4th column
        reason_val = row.get("Reason", "")
        
        html_table += f"""<tr style='border-bottom: 1px solid #F1F5F9; vertical-align: middle;'>
<td style='padding: 14px 12px; color: #475569; white-space: nowrap;'>{row.get("Timestamp", "")}</td>
<td style='padding: 14px 12px; color: #0F172A; font-weight: 500;'>{row.get("File Name", "")}</td>
<td style='padding: 14px 12px; text-align: center;'>{badge}</td>
<td style='padding: 14px 12px; color: #475569;'>{reason_val}</td>
<td style='padding: 14px 12px; color: #475569; text-align: right;'>{time_val}</td>
</tr>"""

    html_table += """</tbody>
</table>
</div>
</div>"""
    st.markdown(html_table, unsafe_allow_html=True)
