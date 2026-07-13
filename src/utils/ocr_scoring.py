import re
from src.config.config import (
    HIGH_VALUE_MULTIPLIER,
    STANDARD_MULTIPLIER,
    STOP_WORD_MULTIPLIER,
    IMPORTANT_WORD_LOW_CONF_THRESHOLD
)

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "when", "where", "how", "who", "which", "this", "that", "these", "those",
    "then", "so", "than", "such", "both", "either", "neither", "not",
    "for", "with", "about", "against", "between", "into", "through", "during", 
    "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", 
    "do", "does", "did", "will", "would", "shall", "should", "may", "might", "must", "can", "could",
    "i", "we", "you", "he", "she", "it", "they", "me", "us", "him", "her", "them", 
    "my", "our", "your", "his", "its", "their", "mine", "ours", "yours", "hers", "theirs",
    "of", "by", "at", "please", "wish", "we", "hereby", "advise"
}

def is_high_value_token(word: str) -> str:
    """
    Returns the type of High-Value Token ('Numeric/ID', 'Entity') 
    or None if it's standard content.
    """
    # Rule A: Numeric/Symbolic (Dates, IDs, Amounts, Emails, Phones)
    if any(char.isdigit() for char in word) or any(sym in word for sym in ['$', '@', '%', '#', '€', '£']):
        return "Numeric/ID"
    
    # Rule B: Entity (Proper Nouns, Acronyms, Companies)
    cleaned = re.sub(r'[^\w\s]', '', word)
    if len(cleaned) >= 2:
        if cleaned.istitle() or cleaned.isupper():
            return "Entity"
            
    return None

def calculate_weighted_confidence(result) -> dict:
    """
    Analyzes OCR results using the Weighted Average methodology.
    Returns the overall score and any flagged high-value tokens.
    """
    total_weighted_confidence = 0.0
    total_weight = 0.0
    total_words = 0
    
    flagged_tokens = []
    
    if not result.pages:
        return {
            "weighted_score": 0.0,
            "flagged_tokens": []
        }

    for page_num, page in enumerate(result.pages, start=1):
        if not page.words:
            continue
            
        for word_obj in page.words:
            word_text = word_obj.content
            if not word_text:
                continue
                
            conf = word_obj.confidence if word_obj.confidence is not None else 0.0
            # Scale to 0-100 if the confidence is 0-1, just in case
            if conf <= 1.0:
                conf = conf * 100
                
            word_len = len(word_text.strip())
            total_words += 1
            
            lower_clean = word_text.strip().lower()
            lower_clean_no_punct = re.sub(r'[^\w\s]', '', lower_clean)
            
            if lower_clean_no_punct in STOP_WORDS or word_len <= 1:
                multiplier = STOP_WORD_MULTIPLIER
            else:
                hvt_type = is_high_value_token(word_text)
                if hvt_type:
                    multiplier = HIGH_VALUE_MULTIPLIER
                    
                    if conf < IMPORTANT_WORD_LOW_CONF_THRESHOLD:
                        flagged_tokens.append({
                            "word": word_text,
                            "confidence": conf
                        })
                else:
                    multiplier = STANDARD_MULTIPLIER
                    
            weight = word_len * multiplier
            
            total_weighted_confidence += (conf * weight)
            total_weight += weight
            
    weighted_score = 0.0
    if total_weight > 0:
        weighted_score = round(total_weighted_confidence / total_weight, 2)
        
    return {
        "weighted_score": weighted_score,
        "flagged_tokens": flagged_tokens
    }
