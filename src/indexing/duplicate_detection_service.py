import hashlib
from datasketch import MinHash
from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
import os

class DuplicateDetectionService:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.table_name = "DocumentHashes"
        self.table_client = None

        if self.connection_string:
            try:
                table_service_client = TableServiceClient.from_connection_string(self.connection_string)
                
                # Ensure the table exists
                try:
                    table_service_client.create_table(self.table_name)
                except ResourceExistsError:
                    pass
                
                self.table_client = table_service_client.get_table_client(table_name=self.table_name)
            except Exception as e:
                print(f"Failed to initialize DuplicateDetectionService: {e}")

    def generate_sha256_hash(self, file_content: bytes) -> str:
        """Generates a SHA-256 hash for the raw file contents."""
        sha256_hash = hashlib.sha256()
        sha256_hash.update(file_content)
        return sha256_hash.hexdigest()

    def generate_minhash(self, text: str) -> str:
        """Generates a MinHash signature string for near-duplicate text detection."""
        if not text:
            return ""
        # Create MinHash with 128 permutations
        m = MinHash(num_perm=128)
        # We split by whitespace for simple word tokenization
        for word in text.split():
            m.update(word.encode('utf8'))
        
        # Convert the hash values to a comma-separated string for easy storage
        return ",".join(map(str, m.hashvalues))

    def is_exact_duplicate(self, file_content: bytes) -> bool:
        """Checks Azure Table Storage (Layer 1) to see if this SHA-256 hash exists."""
        if not self.table_client:
            print("DuplicateDetectionService is not connected to Azure.")
            return False

        file_hash = self.generate_sha256_hash(file_content)
        
        try:
            # We use the hash as the RowKey for O(1) lookup
            # PartitionKey can be a static "Files" for simplicity
            self.table_client.get_entity(partition_key="Files", row_key=file_hash)
            return True  # Entity exists, it's a duplicate!
        except ResourceNotFoundError:
            return False # Not found, it's a new file

    def generate_phash(self, file_content: bytes, filename: str) -> str:
        """Generates a Perceptual Hash (pHash) for image files."""
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return ""
            
        try:
            import imagehash
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(file_content))
            return str(imagehash.phash(image))
        except Exception as e:
            print(f"Failed to generate pHash: {e}")
            return ""

    def is_near_duplicate(self, text: str, file_content: bytes = None, filename: str = "") -> bool:
        """Checks Azure Table Storage (Layer 2) for MinHash or pHash collisions."""
        if not self.table_client:
            return False
            
        min_hash = self.generate_minhash(text) if text else ""
        p_hash = self.generate_phash(file_content, filename) if file_content else ""
        
        if not min_hash and not p_hash:
            return False
            
        try:
            filters = []
            if min_hash:
                filters.append(f"MinHashSignature eq '{min_hash}'")
            if p_hash:
                filters.append(f"PHashSignature eq '{p_hash}'")
                
            query = " or ".join(filters)
            entities = list(self.table_client.query_entities(query_filter=query))
            return len(entities) > 0
        except Exception as e:
            print(f"Failed to query near duplicates: {e}")
            return False

    def is_data_level_duplicate(self, metadata: dict) -> bool:
        """Checks Azure AI Search (Layer 3) to see if the core data already exists."""
        doc_num = metadata.get("document_number")
        entity_name = metadata.get("entity_name")
        
        # We only consider it a data duplicate if it has BOTH a specific ID and Vendor
        if not doc_num or doc_num == "N/A" or not entity_name or entity_name == "N/A":
            return False
            
        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents import SearchClient
            from src.config.config import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_QUERY_KEY
            
            search_client = SearchClient(
                endpoint=AZURE_SEARCH_ENDPOINT,
                index_name="generic-documents-index",
                credential=AzureKeyCredential(AZURE_SEARCH_API_QUERY_KEY)
            )
            
            # Using Lucene full-text query syntax to find matching fields
            search_text = f'document_number:"{doc_num}" AND entity_name:"{entity_name}"'
            results = list(search_client.search(search_text=search_text, query_type="full", top=1))
            return len(results) > 0
        except Exception as e:
            print(f"Failed to query Azure AI Search for data duplicate: {e}")
            return False

    def log_document(self, file_content: bytes, document_id: str, text: str = "", filename: str = ""):
        """Logs a newly processed document's signatures into Azure Table Storage."""
        if not self.table_client:
            return

        file_hash = self.generate_sha256_hash(file_content)
        min_hash = self.generate_minhash(text)
        p_hash = self.generate_phash(file_content, filename)

        entity = {
            "PartitionKey": "Files",
            "RowKey": file_hash,
            "DocumentId": document_id,
            "MinHashSignature": min_hash,
            "PHashSignature": p_hash
        }

        try:
            self.table_client.upsert_entity(entity=entity)
        except Exception as e:
            print(f"Failed to log document hashes to Azure: {e}")
