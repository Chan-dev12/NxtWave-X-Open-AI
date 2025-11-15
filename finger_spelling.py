import os

MEDIA_FOLDER = "media"

def get_fingerspelling_paths(word):
    """
    Converts a word into a list of media paths for each letter's sign video.
    Returns empty list if any letter's video (A.mp4, B.mp4, etc.) is missing.
    """
    paths = []
    # Ensure the word is uppercase and remove any non-alphabetic characters
    clean_word = "".join(filter(str.isalpha, word.upper()))
    
    if not clean_word:
        return []
        
    for letter in clean_word:
        # Construct the expected filename: 'C.mp4', 'H.mp4', etc.
        media_file = f"{letter}.mp4"
        media_path = os.path.join(MEDIA_FOLDER, media_file)

        # Check if the video for the letter exists locally
        if os.path.exists(media_path):
            paths.append(f"/media/{media_file}")
        else:
            # If a letter sign is missing (e.g., you don't have 'Q.mp4'), stop the sequence
            print(f"⚠️ Fingerspelling failed: Video not found for letter: {letter}. Skipping word.")
            return [] 
            
    return paths