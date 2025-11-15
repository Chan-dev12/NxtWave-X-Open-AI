# NxtWave-X-Open-AI
# SignLink

**Text → Sign-Language (3D) pipeline**

SignLink converts written text into sign-language animations using a modular pipeline: text processing → sign lookup / NLP mapping → animation sequencing → Blender retargeting → exportable video/interactive avatar.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Quick Demo](#quick-demo)
4. [Architecture & Pipeline](#architecture--pipeline)
5. [Prerequisites](#prerequisites)
6. [Installation](#installation)
7. [How to use](#how-to-use)
8. [Animation sources / Options](#animation-sources--options)
9. [Blender retargeting guide (short)](#blender-retargeting-guide-short)
10. [Folder structure](#folder-structure)
11. [Development notes & tips](#development-notes--tips)
12. [Contributing](#contributing)
13. [License](#license)

---

## Project Overview

SignLink is an open, extensible project that turns input text into sign-language animation videos (or interactive avatar playback). It focuses on realistic handshape, facial expression, and body posture by supporting multiple animation sources and easy retargeting to Blender rigs.

This repository contains: core text-processing, a mapping table (text → sign tokens), animation library management, utilities for importing/exporting animations, and helper scripts for Blender retargeting.

> Note: This project is *language-agnostic* but initial examples are built for Indian Sign Language (ISL) and American Sign Language (ASL) tokens. You can extend the token mapping to any sign language.

---

## Key Features

* Text normalization & tokenization tuned for sign-language mapping
* Sign lookup and sequencing (supports multi-word signs and glosses)
* Animation library manager (FBX / BVH / GLB)
* Optional API integrations for animation generation (DeepMotion, etc.)
* MediaPipe/MoveNet extractor utilities (video → keypoints → Blender-ready format)
* Blender helper scripts for retargeting and batch import
* Export pipeline for MP4/GIF and WebGL (.glb) playback

---

## Quick Demo

```bash
# Example: start a simple local server that maps text to animations
pip install -r requirements.txt
python app.py --port 5000
# POST /api/sign with JSON {"text":"hello, how are you"}
# response: path to generated video file or animation sequence
```

---

## Architecture & Pipeline

1. **Text processing**: normalize input, remove punctuation, split sentences, map words/phrases to gloss tokens.
2. **Sign lookup**: consult `signlib/` for existing animations. If a token has no animation, fall back to fingerspelling or a placeholder animation.
3. **Sequence builder**: resolves timing, transition clips, and facial-expression overlays.
4. **Animation retargeter**: imports chosen animations into Blender and retargets them onto the user avatar rig (Rigify/Mixamo/Custom).
5. **Render/Export**: renders final MP4 (or exports glTF for web).

---

## Prerequisites

* Python 3.10+ (recommended)
* Blender 3.5+ for retargeting scripts (Blender must be installed separately)
* Node.js (optional) if you serve a web UI
* (Optional) DeepMotion / paid API credentials for automatic mocap → FBX

---

## Installation

```bash
git clone https://github.com/your-org/signlink.git
cd signlink
python -m venv env
source env/bin/activate  # macOS / Linux
# On Windows: env\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` includes:

* flask / fastapi (API server)
* numpy, pandas
* mediapipe (for keypoint extraction)
* transforms3d / pyquaternion (helpers)
* moviepy (video export)

---

## How to use

### 1) Add animations to the library

Put your animation files into `signlib/` with the naming convention:

```
signlib/<language>/<gloss_name>.<ext>
# e.g. signlib/isl/hello.fbx
```

Each animation file should be a short motion clip (1–3 seconds).

### 2) Start API server

```bash
python app.py
# or for FastAPI
uvicorn app:app --reload --port 8000
```

### 3) Convert text to sign

HTTP POST example:

```http
POST /api/sign
Content-Type: application/json

{"text":"hello, how are you"}
```

Response will return a JSON payload with either:

* a path to the rendered MP4, or
* an ordered list of animation files and timing metadata for client-side playback

---

## Animation sources / Options

You have three practical options to populate `signlib/`:

1. **Manual authoring (Blender)** – Create animations by hand in Blender for max control.
2. **Motion capture via API** – Use DeepMotion (or similar) to upload video of a signer and receive FBX/BVH files.
3. **Keypoint extraction (MediaPipe) + procedural retarget** – Extract skeleton + hand landmarks and convert to Blender bones (requires coding, free).

Choose option 2 if you want speed and natural motion; choose 1 if you need precise, linguistically-correct signing; choose 3 if you want a free but engineering-heavy approach.

---

## Blender retargeting guide (short)

1. Use a consistent armature naming scheme (or provide a bone map JSON) to retarget automatically.
2. For hand animation fidelity, use a detailed hand rig with finger bones (Rigify or a custom hand rig).
3. Use Blender's `NLA` strips to sequence clips and add blending between clips.
4. Use the `retarget.py` helper script (in `tools/`) which:

   * loads the FBX/BVH
   * maps source bones to target armature using `bone_map.json`
   * applies root motion corrections and scaling

Example usage:

```bash
blender --background --python tools/retarget.py -- --source signlib/isl/hello.fbx --target avatars/my_avatar.blend --out out/hello_retargeted.blend
```

---

## Folder structure

```
/
├─ app.py                # main server (text -> sequence manager)
├─ requirements.txt
├─ signlib/              # store animations per language
│  ├─ isl/
│  └─ asl/
├─ tools/
│  ├─ retarget.py        # blender retarget helper
│  ├─ mediapipe_extract.py
│  └─ deepmotion_upload.py
├─ assets/
│  ├─ avatars/
│  └─ sample_videos/
├─ data/
│  ├─ token_map.json
│  └─ bone_map.json
└─ README.md
```

---

## Development notes & tips

* **Timing & prosody matter**: sign-language meaning depends on timing and facial cues — store expression overlays (brow raise, eye gaze) separately and blend them with the base animation.
* **Fallbacks**: implement automatic fingerspelling fallback for unknown tokens.
* **Transition clips**: small transition animations (neutral pose → sign pose) make sequences much more natural.
* **Testing with native signers**: validate accuracy with native signers early and often.

---

## Contributing

Contributions welcome — open a PR or raise an issue. Please follow these rules:

1. Add new signs into `signlib/<language>/` and include a short JSON file describing the gloss and metadata (author, source, duration).
2. For scripts, write tests where possible.
3. If adding an external API integration, put credentials in `.env` and add a README for the integration.

---

## License

MIT License — see `LICENSE`.

---
