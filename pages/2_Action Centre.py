import os
import json
from datetime import datetime
import streamlit as st
from datetime import datetime
import shutil
import pandas as pd
from streamlit_pdf_viewer import pdf_viewer
import io
import requests
from src.utils.blob_service import generate_sas_url, delete_blob
from src.indexing.duplicate_detection_service import DuplicateDetectionService

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
    st.title("Action Centre")
    st.caption("Review and validate documents that require manual intervention.")

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

    if "selected_doc_index" not in st.session_state:
        st.session_state.selected_doc_index = None

    if st.session_state.selected_doc_index is None:
        # Inject CSS to drastically reduce vertical whitespace for the list rows
        st.markdown("""
            <style>
            [data-testid="column"] {
                padding-bottom: 0rem !important;
                padding-top: 0rem !important;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("### Pending Documents")
        hcols = st.columns([4, 3, 3, 2])
        hcols[0].markdown("**File Name**")
        hcols[1].markdown("**Entity Name**")
        hcols[2].markdown("**Document Date**")
        hcols[3].markdown("**Action**")
        st.markdown("<hr style='margin: 0.2rem 0; border: none; border-bottom: 1px solid rgba(200,200,200,0.3);'/>", unsafe_allow_html=True)
        
        for idx, list_doc in enumerate(docs):
            cols = st.columns([4, 3, 3, 2], gap="small")
            
            # File Name is always available
            cols[0].write(list_doc.get("file_name", "Unknown"))
            
            # Handle Entity Name & Errors
            if "error" in list_doc:
                cols[1].markdown("🚨 **Extraction Failed**")
                cols[2].markdown("🚨 **Failed**")
            else:
                entity = list_doc.get("entity_name")
                cols[1].write(entity if entity and str(entity).strip() else "⚠️ *Missing*")
                
                date = list_doc.get("document_date")
                cols[2].write(str(date) if date and str(date).strip() else "⚠️ *Missing*")
            
            if cols[3].button("Review", key=f"review_btn_{idx}", use_container_width=True):
                st.session_state.selected_doc_index = idx
                st.rerun()
            st.markdown("<hr style='margin: 0.2rem 0; border: none; border-bottom: 1px solid rgba(200,200,200,0.3);'/>", unsafe_allow_html=True)

            
    else:
        i = st.session_state.selected_doc_index
        if i >= len(docs):
            st.session_state.selected_doc_index = None
            st.rerun()
            
        doc = docs[i]
        
        if st.button("← Back to List", key="back_to_list"):
            st.session_state.selected_doc_index = None
            st.rerun()
            
        st.markdown(f"### Reviewing: {doc.get('file_name', 'Document')}")
        st.markdown("---")

        left, right = st.columns(
            [5, 4]
        )

        blob_name = doc.get("sharepoint_url", "")
        
        with left:
            st.subheader(doc["file_name"])
            st.caption("Document Preview")

            if blob_name:
                sas_url = generate_sas_url(blob_name)
                if sas_url:
                    extension = os.path.splitext(blob_name)[1].lower()
                    
                    try:
                        # Fetch securely into RAM
                        response = requests.get(sas_url)
                        response.raise_for_status()
                        file_bytes = response.content
                        
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
                                    
                                    # Render DOCX content inside a scrollable container
                                    st.markdown(
                                        f'<div style="height: 800px; overflow-y: auto; padding: 1rem; background: white; color: black; font-family: sans-serif;">{html}</div>', 
                                        unsafe_allow_html=True
                                    )
                                except Exception as e:
                                    st.error(f"Failed to preview DOCX: {e}")
                    except Exception as e:
                        st.error(f"Failed to load document from cloud: {e}")
                else:
                    st.warning("Failed to generate secure preview link.")
            else:
                st.warning("Original document URL not found in metadata.")

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

            default_date = None

            try:
                if doc.get("document_date"):
                    default_date = datetime.strptime(
                        str(doc["document_date"]),
                        "%d %B %Y"
                    ).date()
            except:
                pass

            document_date = st.date_input(
                "Document Date",
                value=default_date,
                key=f"date_{i}"
            )

            st.markdown("##### Metadata")
            
            metadata_fields_key = f"metadata_fields_{i}"

            if metadata_fields_key not in st.session_state:
                metadata_list = []
                raw_metadata = doc.get("metadata", "")
                
                if raw_metadata:
                    try:
                        parsed_meta = json.loads(raw_metadata)
                        if isinstance(parsed_meta, dict):
                            # In some cases, Gemini nests metadata in a 'metadata' key
                            if "metadata" in parsed_meta and isinstance(parsed_meta["metadata"], dict):
                                parsed_meta = parsed_meta["metadata"]
                                
                            for k, v in parsed_meta.items():
                                if k not in ["document_type", "document_title", "document_number", "entity_name", "document_date", "error"]:
                                    metadata_list.append({"Key": str(k), "Value": str(v)})
                    except Exception:
                        pass
                
                if not metadata_list:
                    # Empty dataframe with string columns ensures 0 data rows and exactly 1 "+" row
                    df = pd.DataFrame({
                        "Key": pd.Series(dtype="str"),
                        "Value": pd.Series(dtype="str")
                    })
                else:
                    df = pd.DataFrame(metadata_list[:50])
                    
                st.session_state[metadata_fields_key] = df

            df = st.session_state[metadata_fields_key]
            
            df = st.session_state[metadata_fields_key]
            
            # Ensure Delete column exists
            if "Delete" not in df.columns:
                df["Delete"] = False

            # Render metadata data_editor with fixed rows to prevent auto-appending
            edited_metadata = st.data_editor(
                df,
                num_rows="fixed",
                column_config={
                    "Key": st.column_config.TextColumn(
                        "Key",
                        width="medium"
                    ),
                    "Value": st.column_config.TextColumn(
                        "Value",
                        width="medium"
                    ),
                    "Delete": st.column_config.CheckboxColumn(
                        "Del",
                        default=False
                    )
                },
                hide_index=True,
                use_container_width=False,  # Important
                key=f"editor_{i}"
            )
            
            # Process deletions instantly
            if any(edited_metadata["Delete"] == True):
                new_df = edited_metadata[edited_metadata["Delete"] == False].reset_index(drop=True)
                st.session_state[metadata_fields_key] = new_df
                st.rerun()

            # Custom gray button to add a new row
            if st.button("➕ Add Metadata Field", type="secondary", key=f"add_row_{i}"):
                new_row = pd.DataFrame([{"Key": "", "Value": "", "Delete": False}])
                new_df = pd.concat([edited_metadata, new_row], ignore_index=True)
                st.session_state[metadata_fields_key] = new_df
                st.rerun()
            
            edited_metadata = st.session_state[metadata_fields_key]
            
            if len(edited_metadata) > 50:
                st.warning("Warning: Only the first 50 entries will be saved.")

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
                    width="stretch"
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

                    # Collect non-empty metadata
                    final_metadata = {}
                    
                    for _, row in edited_metadata.iterrows():
                        if pd.notna(row.get("Key")) and pd.notna(row.get("Value")):
                            k = str(row["Key"]).strip()
                            v = str(row["Value"]).strip()
                            if k and v:
                                final_metadata[k] = v
                    
                    # Truncate to 50 items to be safe
                    final_metadata = dict(list(final_metadata.items())[:50])
                    doc["metadata"] = json.dumps(final_metadata)

                    doc_to_upload = (
                        doc.copy()
                    )

                    doc_to_upload.pop(
                        "review_status",
                        None
                    )
                    
                    if "metadata" in doc_to_upload:
                        try:
                            import json
                            meta_dict = json.loads(doc_to_upload["metadata"]) if isinstance(doc_to_upload["metadata"], str) else doc_to_upload["metadata"]
                            meta_dict.pop("flagged_tokens", None)
                            doc_to_upload["metadata"] = json.dumps(meta_dict) if isinstance(doc_to_upload["metadata"], str) else meta_dict
                        except Exception:
                            pass

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
                        url=doc.get("sharepoint_url", ""),
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
                        doc.get("id", doc.get("file_name"))
                    )

                    st.success(
                        "Document approved and indexed successfully."
                    )
                    
                    st.session_state.selected_doc_index = None
                    st.rerun()

            with b2:

                if st.button(
                    "Reject",
                    key=f"r_{i}",
                    width="stretch"
                ):

                    log_document_status(
                        file_name=doc[
                            "file_name"
                        ],
                        url=doc.get("sharepoint_url", ""),
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
                        doc.get("id", doc.get("file_name"))
                    )
                    
                    # --- DEEP REJECT: Purge from Azure Ecosystem ---
                    # 1. Delete Blob
                    blob_name = doc.get("sharepoint_url", "")
                    if blob_name:
                        delete_blob(blob_name)
                        
                    # 2. Delete Hashes
                    sha256_hash = doc.get("sha256_signature", "")
                    if sha256_hash:
                        dedupe_service = DuplicateDetectionService()
                        dedupe_service.delete_document_hashes(sha256_hash)

                    st.warning(
                        "Document completely rejected and purged from Azure."
                    )

                    st.session_state.selected_doc_index = None
                    st.rerun()