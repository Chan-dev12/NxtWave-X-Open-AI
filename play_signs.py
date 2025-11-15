import os
import json
import requests
from bs4 import BeautifulSoup

# Folder to store downloaded media
media_folder = "media"
os.makedirs(media_folder, exist_ok=True)

# JSON file to store word-to-media mappings
json_file = "word_to_media.json"

# Load existing word mappings or start fresh
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        word_map = json.load(f)
else:
    word_map = {}

# Function to download GIF or video if it doesn't exist
def download_media(word):
    url = f"https://www.signasl.org/sign/{word}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch {word}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        video_tag = soup.find("video")

        if video_tag:
            source = video_tag.find("source")
            if source:
                media_url = source["src"]
                file_extension = media_url.split('.')[-1]
                media_file = f"{word}.{file_extension}"
                media_path = os.path.join(media_folder, media_file)

                # Download and save the media file
                media_data = requests.get(media_url, headers=headers).content
                with open(media_path, "wb") as f:
                    f.write(media_data)

                # Update the JSON mapping
                word_map[word] = media_file
                with open(json_file, "w") as f:
                    json.dump(word_map, f, indent=2)

                print(f"✅ Downloaded and mapped: {word} → {media_file}")
                return media_path

        print(f"❌ Media not found for: {word}")
    except Exception as e:
        print(f"❌ Error downloading {word}: {e}")

    return None