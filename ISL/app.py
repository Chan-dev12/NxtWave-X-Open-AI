from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import wikipedia
from dotenv import load_dotenv 
from openai import OpenAI 
from external_media_downloader import download_sign_media 
from grammar_convert import convert_to_asl_grammar


# --- 1. INITIAL SETUP ---

load_dotenv()
openai_client = None
try:
    # Initialize client using the OPENAI_API_KEY from .env
    openai_client = OpenAI()
except Exception as e:
    print(f"WARNING: OpenAI client initialization failed. GPT fallback will not work. Error: {e}")


app = Flask(__name__)
MEDIA_FOLDER = "media"
UPLOAD_FOLDER = "uploads"

os.makedirs(MEDIA_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["MEDIA_FOLDER"] = MEDIA_FOLDER
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --- 2. GPT FALLBACK FUNCTION ---

def generate_gpt_summary(word):
    """Generates a simple, accessible explanation of a word using a GPT model."""
    if not openai_client:
        return None

    system_prompt = (
        "You are an AI assistant for a sign language translator app. "
        "Your task is to provide a very short, simple, and accessible "
        "explanation (max 2 sentences) for a word that does not have a sign video. "
        "Focus on defining proper nouns like cities, people, or specific concepts. "
        "The output must be pure, clean text."
    )

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

        if not os.path.exists(media_path):
            print(f"--- Missing sign video for: {word}. Attempting external search and cache. ---")
            
            # AUTOMATIC CACHING LOGIC
            downloaded_path = download_sign_media(word) 
            
            if downloaded_path:
                media_file = os.path.basename(downloaded_path)
            else:
                print(f"Skipping sign: {word} (No local file or external source found)")
                continue 

        video_urls.append(f"/media/{media_file}")

    return jsonify({
        "asl_gloss": asl_text,
        "media": video_urls,
        "summary": None, 
        "link": None     
    })

@app.route("/search_convert", methods=["POST"])
def search_convert():
    data = request.get_json()
    query = data.get("query", "").strip()
    
    
    if not query:
        return jsonify({"error": "No query provided."}), 400

    # 1. Attempt Local Video Lookup
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

    # 2. GPT Fallback
    summary = generate_gpt_summary(query)
    
    if summary:
        summary_source = "AI Explanation"
    else:
        # 3. Wikipedia Fallback
        try:
            page = wikipedia.page(query, auto_suggest=True, redirect=True)
            summary = wikipedia.summary(query, sentences=2, auto_suggest=True, redirect=True)
            wiki_link = page.url 
            summary_source = "Wikipedia"
        except wikipedia.exceptions.PageError:
            summary = f"Could not find an external explanation for '{query}'. Using basic glossary search."
            summary_source = "Rule-Based"
        except Exception as e:
            print("Wikipedia lookup failed:", e)
            summary = f"An error occurred during external lookup for '{query}'. Using basic glossary search."
            summary_source = "Error"

    # Convert the summary/explanation into ASL gloss words
    if summary and summary_source != "Error":
        asl_text = convert_to_asl_grammar(summary)
        words = asl_text.split()
    else:
        asl_text = convert_to_asl_grammar(query)
        words = asl_text.split()
        
    # Find signs for the words in the resulting summary/ASL text and CACHE MISSING ONES
    media_paths = []
    try:
        with open("word_to_media.json", "r") as f:
            word_map = json.load(f)
    except:
        word_map = {}

    for word in words:
        media_file = word_map.get(word, f"{word}.mp4")
        media_path = os.path.join(MEDIA_FOLDER, media_file)
        
        # CORE CACHING LOGIC
        if not os.path.exists(media_path):
            print(f"--- Missing sign video for: {word}. Attempting external search and cache. ---")
            
            downloaded_path = download_sign_media(word) 
            
            if downloaded_path:
                media_file = os.path.basename(downloaded_path)
            else:
                continue 
        
        media_paths.append(f"/media/{media_file}")

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