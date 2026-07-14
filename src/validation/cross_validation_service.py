from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from src.config.config import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_ADMIN_KEY
from datetime import datetime

def cross_validate_claim(claim_metadata: dict, user_id: str = "default_global") -> list:
    """
    Cross-references a claim against the Ground Truth policy in the Master Index.
    Returns a list of breach reasons. If empty, the claim is valid.
    """
    print("\n[Cross-Validation] 🔍 Started cross-validation against Policy Master Index...")
    breaches = []
    
    # Helper to get field from root or nested metadata
    def get_field(key):
        val = claim_metadata.get(key)
        if val is None and "metadata" in claim_metadata and isinstance(claim_metadata["metadata"], dict):
            val = claim_metadata["metadata"].get(key)
        return val
        
    policy_number = get_field("policy_number") or get_field("policy_ref_umr")
    
    if not policy_number or str(policy_number).strip().lower() in ["n/a", "null", "none", ""]:
        print("[Cross-Validation] ❌ Missing Policy Number on Claim. Cannot cross-validate.")
        return ["Missing Policy Number on Claim"]

    print(f"[Cross-Validation] 📡 Querying Policy Master Index for policy: {policy_number}")
    # 1. Fetch Policy from Master Index
    try:
        search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name="policy-master-index",
            credential=AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY)
        )
        
        results = list(search_client.search(search_text=str(policy_number), search_fields=["policy_number"], top=1))
    except Exception as e:
        print(f"[Cross-Validation] ⚠️ Error querying Master Index: {e}")
        return [f"Failed to query Master Index: {e}"]
    
    if not results:
        print(f"[Cross-Validation] ❌ Policy '{policy_number}' not found in Master Index!")
        return [f"Policy '{policy_number}' not found in Master Index"]
        
    policy = results[0]
    print(f"[Cross-Validation] ✅ Found matching policy in Master Index. Beginning Adjudication...")
    
    # 2. Identity Check
    print("[Cross-Validation] 👤 Running Identity Check...")
    claim_insured_raw = str(get_field("insured_name") or get_field("claimant_name") or get_field("policy_insured") or "").strip()
    policy_insured_raw = str(policy.get("insured_name") or "").strip()
    
    claim_insured = claim_insured_raw.replace(" ", "").lower()
    policy_insured = policy_insured_raw.replace(" ", "").lower()
    
    # Strict exact match (ignoring spaces and case)
    if claim_insured and policy_insured and claim_insured not in ["n/a"]:
        if claim_insured != policy_insured:
            print(f"[Cross-Validation] ❌ Identity Mismatch: Claim ({claim_insured_raw}) vs Policy ({policy_insured_raw})")
            breaches.append(f"Identity Mismatch: Claim says '{claim_insured_raw}' but Policy says '{policy_insured_raw}'")
        else:
            print("[Cross-Validation] ✅ Identity Check passed.")
    else:
        print("[Cross-Validation] ⚠️ Identity Check skipped (missing data).")

    # 3. Financial Check
    print("[Cross-Validation] 💰 Running Financial Limits Check...")
    claim_amount_str = str(get_field("settlement_amount") or get_field("paid_amount_100") or get_field("net_settlement_amount") or get_field("claim_amount") or "0")
    
    try:
        claim_amount = float(claim_amount_str.replace(",", "").replace("$", "").replace("£", "").strip())
        policy_limit = float(policy.get("policy_limit") or 0.0)
        
        if policy_limit > 0 and claim_amount > policy_limit:
            print(f"[Cross-Validation] ❌ Limit Breach: Claim ({claim_amount}) > Policy Limit ({policy_limit})")
            breaches.append(f"Limit Breach: Claim amount ({claim_amount}) exceeds Policy Limit ({policy_limit})")
        else:
            print(f"[Cross-Validation] ✅ Financial Check passed (Claim: {claim_amount}, Limit: {policy_limit}).")
    except ValueError:
        print("[Cross-Validation] ⚠️ Financial Check skipped (could not parse amount).")
        
    # 4. Temporal Check
    print("[Cross-Validation] ⏳ Running Temporal Coverage Check...")
    loss_date_str = str(get_field("date_of_loss") or get_field("loss_date_from") or "")
    if loss_date_str and loss_date_str.lower() != "n/a":
        try:
            # Basic parsing attempt (assuming YYYY-MM-DD from Gemini)
            loss_date = datetime.strptime(loss_date_str, "%Y-%m-%d").date()
            effective = datetime.strptime(policy.get("policy_effective_date")[:10], "%Y-%m-%d").date() if policy.get("policy_effective_date") else None
            expiration = datetime.strptime(policy.get("policy_expiration_date")[:10], "%Y-%m-%d").date() if policy.get("policy_expiration_date") else None
            
            breached = False
            if effective and loss_date < effective:
                print(f"[Cross-Validation] ❌ Temporal Breach: Loss ({loss_date}) before Effective Date ({effective})")
                breaches.append(f"Temporal Breach: Loss Date ({loss_date}) occurred before Policy Effective Date ({effective})")
                breached = True
            if expiration and loss_date > expiration:
                print(f"[Cross-Validation] ❌ Temporal Breach: Loss ({loss_date}) after Expiration Date ({expiration})")
                breaches.append(f"Temporal Breach: Loss Date ({loss_date}) occurred after Policy Expiration Date ({expiration})")
                breached = True
                
            if not breached:
                 print("[Cross-Validation] ✅ Temporal Check passed.")
        except:
            print("[Cross-Validation] ⚠️ Temporal Check skipped (could not parse date).")
    else:
        print("[Cross-Validation] ⚠️ Temporal Check skipped (missing loss date).")
            
    # 5. Dynamic Custom Attribute Checks
    print("[Cross-Validation] ⚙️ Running User-Defined Custom Attribute Checks...")
    
    try:
        from src.config.config_service import load_custom_attributes
        custom_attrs = load_custom_attributes(user_id)
        
        for attr in custom_attrs:
            if attr.get("active"):
                key = attr["name"]
                claim_val = str(get_field(key) or "").strip().lower()
                
                policy_custom_data = {}
                try:
                    import json
                    policy_custom_data = json.loads(policy.get("metadata", "{}"))
                except:
                    pass
                
                # Check root of Azure Search document, then root of Gemini extraction, then nested metadata dict
                val = policy.get(key) or policy_custom_data.get(key)
                if val is None and "metadata" in policy_custom_data and isinstance(policy_custom_data["metadata"], dict):
                    val = policy_custom_data["metadata"].get(key)
                    
                policy_val = str(val or "").strip().lower()
                
                # Compare the fields
                if claim_val and claim_val not in ["n/a", "null", "none", ""]:
                    if claim_val != policy_val:
                        print(f"[Cross-Validation] ❌ Custom Breach: Claim '{key}' ({claim_val}) != Policy '{key}' ({policy_val})")
                        breaches.append(f"Custom Validation Breach: Claim '{key}' ({claim_val}) does not match Policy Master Index ({policy_val})")
                    else:
                        print(f"[Cross-Validation] ✅ Custom Check '{key}' passed.")
    except Exception as e:
        print(f"[Cross-Validation] ⚠️ Error running custom attribute checks: {e}")

    print(f"[Cross-Validation] 🏁 Cross-validation ended. Found {len(breaches)} breach(es).")
    return breaches
