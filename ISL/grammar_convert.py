from transformers import pipeline
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize 
import re 
# from nltk import download as nltk_download # Uncomment if you need to download data

# --- DOWNLOAD NLTK DATA ON FIRST RUN ---
# nltk_download('wordnet')
# nltk_download('punkt')

# --- 1. INITIAL SETUP ---

try:
    # Set device="cuda" if you have a powerful NVIDIA GPU
    asl_pipe = pipeline("text2text-generation", model="google/flan-t5-small", device=-1) 
    USE_AI = True
    print("✅ FLAN-T5 model loaded successfully.")
except Exception as e:
    asl_pipe = None
    USE_AI = False
    print(f"⚠️ FLAN-T5 failed to load. Only using rule-based fallback. Error: {e}")

lemmatizer = WordNetLemmatizer()

removable_words = {
    'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being',
    'a', 'an', 'the', 'to', 'of', 'in', 'on', 'at', 'by',
    'as', 'for', 'about', 'into', 'from', 'that',
    'this', 'those', 'these', 'just', 'do', 'does', 'did',
    'have', 'has', 'had', 'having', 'so', 'because',
    'will', 'would', 'can', 'could', 'should', 'shall', 'may',
    'might', 'must', 'and', 'or', 'but', 'if', 'than', 'then',
    'i', 'me', 'you', 'he', 'she', 'it', 'we', 'us', 'they', 'them' 
}

# --- 2. CONVERSION FUNCTIONS ---

def apply_rule_based_fallback(text):
    """Applies basic filtering, punctuation removal, and lemmatization."""
    cleaned_text = re.sub(r'[^\w\s]', '', text) 
    words = word_tokenize(cleaned_text.lower())
    
    filtered_words = []
    for word in words:
        if word not in removable_words:
            # Lemmatize verbs, then nouns
            base_word = lemmatizer.lemmatize(word, pos='v') 
            if base_word == word:
                 base_word = lemmatizer.lemmatize(word) 
            filtered_words.append(base_word.upper()) 
            
    return ' '.join(filtered_words)

def convert_to_asl_grammar(text):
    """Converts English text to Sign Gloss using AI (primary) or rules (fallback)."""
    if not text:
        return ""
        
    if USE_AI:
        try:
            prompt = f"Convert to ISL grammar: {text}" # Adjusted prompt for ISL focus
            result = asl_pipe(
                prompt, 
                max_new_tokens=50, 
                do_sample=False
            ) 
            asl_text = result[0]['generated_text'].strip().upper()
            print("✅ Hugging Face model used:", asl_text)
            return asl_text
        except Exception as e:
            print(f"⚠️ Hugging Face model execution failed: {e}. Falling back to rule-based conversion.")
            pass

    # Fallback execution
    asl_text = apply_rule_based_fallback(text)
    print("❌ Rule-Based Fallback used:", asl_text)
    return asl_text