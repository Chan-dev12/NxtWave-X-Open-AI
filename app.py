from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import wikipedia
from dotenv import load_dotenv 
from openai import OpenAI 
# --- IMPORTING SEPARATED FILES ---
from grammar_convert import convert_to_asl_grammar
from external_media_downloader import download_sign_media # Kept for structure, though logic is disabled
from finger_spelling import get_fingerspelling_paths
# ---------------------------------

# --- 1. INITIAL SETUP ---

load_dotenv()
openai_client = None
try:
    openai_client = OpenAI()
except Exception as e:
    # If key is missing, GPT fallback is gracefully disabled
    print(f"WARNING: GPT fallback disabled. Error: {e}")


app = Flask(__name__)
MEDIA_FOLDER = "media"
UPLOAD_FOLDER = "uploads"

os.makedirs(MEDIA_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["MEDIA_FOLDER"] = MEDIA_FOLDER
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --- 2. GPT FALLBACK FUNCTION (STAYS HERE for direct API call) ---

def generate_gpt_summary(word):
    """Generates a simple explanation of a word using a GPT model."""
    if not openai_client:
        return None
    # ... (Rest of the GPT function is unchanged) ...
    system_prompt = ("You are an AI assistant for a sign language translator app. Your task is to provide a very short, simple, and accessible explanation (max 2 sentences) for a word that does not have a sign video. Focus on defining proper nouns like cities, people, or specific concepts. The output must be pure, clean text.")
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Explain the term: '{word}'"},
            ],
            max_tokens=100,
            temperature=0.3
        )
        summary = response.choices[0].message.content.strip()
        return summary if summary else None
    except Exception as e:
        print(f"Error calling GPT API for '{word}': {e}")
        return None

# --- 3. ROUTES ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert_text():
    # Handles full sentence conversion
    text = request.form.get("text")
    if not text:
        return jsonify({"error": "No input provided."})

    asl_text = convert_to_asl_grammar(text)
    words = asl_text.split()
    video_urls = []

    try:
        with open("word_to_media.json", "r") as f:
            word_map = json.load(f)
    except:
        word_map = {}

    for word in words:
        media_file = word_map.get(word, f"{word}.mp4")
        media_path = os.path.join(MEDIA_FOLDER, media_file)

        if os.path.exists(media_path):
            video_urls.append(f"/media/{media_file}")
        else:
            # --- FINGERSPELLING FALLBACK FOR SENTENCE WORDS (Optional) ---
            fingerspelled_paths = get_fingerspelling_paths(word)
            if fingerspelled_paths:
                video_urls.extend(fingerspelled_paths)
            else:
                print(f"Skipping sign: {word} (No local video or fingerspelling letters found)")
                continue 

    return jsonify({
        "asl_gloss": asl_text,
        "media": video_urls,
        "summary": None, 
        "link": None     
    })

@app.route("/search_convert", methods=["POST"])
def search_convert():
    # Handles concept search (e.g., "Chennai")
    data = request.get_json()
    query = data.get("query", "").strip()
    
    if not query:
        return jsonify({"error": "No query provided."}), 400

    # 1. Attempt Local Video Lookup for the main query word
    media_file_query = f"{query.lower()}.mp4"
    media_path_query = os.path.join(MEDIA_FOLDER, media_file_query)
    
    if os.path.exists(media_path_query):
        return jsonify({
            "asl_gloss": query, 
            "media": [f"/media/{media_file_query}"],
            "summary": f"Local video found for '{query}'.",
            "link": None
        })
    
    summary = None
    wiki_link = None 

    # 2. Intelligent Fallback (GPT/Wikipedia/Rule-Based)
    summary = generate_gpt_summary(query)
    
    if summary:
        summary_source = "AI Explanation"
    else:
        # If GPT fails, check Wikipedia (assuming you don't care about the 429 error)
        try:
            page = wikipedia.page(query, auto_suggest=True, redirect=True)
            summary = wikipedia.summary(query, sentences=2, auto_suggest=True, redirect=True)
            wiki_link = page.url 
            summary_source = "Wikipedia"
        except Exception:
            # If all external lookups fail
            summary = f"No detailed explanation found for '{query}'. Attempting fingerspelling."
            summary_source = "Fingerspelling Fallback"
    
    # Convert the summary/explanation into ASL gloss words
    asl_text = convert_to_asl_grammar(summary or query) # Use summary or original query
    words = asl_text.split()
        
    # Find signs for the words in the resulting summary/ASL text
    media_paths = []
    try:
        with open("word_to_media.json", "r") as f:
            word_map = json.load(f)
    except:
        word_map = {}

    for word in words:
        media_file = word_map.get(word, f"{word}.mp4")
        media_path = os.path.join(MEDIA_FOLDER, media_file)
        
        if os.path.exists(media_path):
            media_paths.append(f"/media/{media_file}")
        else:
            # --- FINGERSPELLING FALLBACK FOR MISSING WORD IN SUMMARY (NEW) ---
            fingerspelled_paths = get_fingerspelling_paths(word)
            if fingerspelled_paths:
                media_paths.extend(fingerspelled_paths)
            else:
                print(f"Skipping sign: {word} (No local file or fingerspelling letters found)")
                continue 

    # --- FINAL CHECK: If no signs were found AT ALL, spell the original query ---
    if not media_paths and summary_source == "Fingerspelling Fallback":
        final_fingerspelled_paths = get_fingerspelling_paths(query)
        media_paths.extend(final_fingerspelled_paths)


    return jsonify({
        "asl_gloss": asl_text,
        "media": media_paths,
        "summary": summary,
        "link": wiki_link 
    })


@app.route("/media/<filename>")
def media(filename):
    return send_from_directory(MEDIA_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)