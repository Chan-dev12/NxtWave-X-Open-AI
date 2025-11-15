import requests
from bs4 import BeautifulSoup
import os
import time
import re

MEDIA_FOLDER = "media"
BASE_SIGN_DICTIONARY_URL = "https://indiansignlanguage.org"

# --- Essential Headers to Avoid 403 Forbidden ---
HEADERS = {
    # This header convinces the server you are a standard Chrome browser on Windows
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    # This header tricks the server into thinking the request came from Google search
    'Referer': 'https://www.google.com/' 
}
# -----------------------------------------------

def scrape_sign_video_url(word):
    """
    Searches the ISL Portal for a word and attempts to find the direct video URL.
    This function uses the anti-blocking HEADERS.
    """
    search_url = f"{BASE_SIGN_DICTIONARY_URL}/word/{word.lower()}/"
    
    try:
        # Be a polite scraper and wait
        time.sleep(1) 
        
        # --- Using HEADERS HERE to disguise the script ---
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        response.raise_for_status() # Raises the 403 Forbidden error if blocked
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Logic to find the video source
        video_tag = soup.find('video')
        
        if video_tag and video_tag.has_attr('src'):
            video_src = video_tag['src']
        else:
            # Search for a <source> element within a video container
            video_source_tag = soup.find('source', type=re.compile("video/"))
            if video_source_tag and video_source_tag.has_attr('src'):
                video_src = video_source_tag['src']
            else:
                 return None 

        # Ensure the URL is absolute
        if video_src.startswith('http'):
            return video_src
        elif video_src.startswith('/'):
            return BASE_SIGN_DICTIONARY_URL + video_src
        
        return None
        
    except requests.exceptions.RequestException as e:
        # This catches 403 errors and network errors (like DNS failure)
        print(f"❌ Scraping failed for {word}: Network/Request Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Scraping failed for {word}: Parsing Error: {e}")
        return None


def download_sign_media(word_gloss):
    """
    Searches for the video URL, downloads it, and saves it to the local media folder.
    """
    # 1. Scrape the URL (This is where the headers are critical)
    video_url = scrape_sign_video_url(word_gloss.lower()) 
    
    if not video_url:
        return None
        
    local_filename = f"{word_gloss.upper()}.mp4"
    local_path = os.path.join(MEDIA_FOLDER, local_filename)
    
    # 2. Download the video content
    try:
        print(f"Attempting download from: {video_url}")
        # Headers are not strictly needed here, but you can pass them for consistency if needed
        response = requests.get(video_url, stream=True, timeout=20) 
        response.raise_for_status() 

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"✅ SUCCESSFULLY CACHED ISL SIGN: {local_filename}")
        return local_path
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Download failed for {word_gloss}: {e}")
        return None