# SpotDown - Cross Platform Edition

SpotDown is a powerful, beautiful, glassmorphic Spotify downloader that works on Windows, macOS, and Linux. It uses the `spotdl` Python engine to fetch high-quality audio files completely locally, avoiding rate limits and CORS errors common in web-based downloaders.

## Installation

1. Make sure you have Python 3.8 or newer installed on your computer.
2. Open a terminal (or Command Prompt) in this folder.
3. Install the dependencies by running:
   ```bash
   pip install -r requirements.txt
   ```

## How to Run

Simply run the main Python file:
```bash
python main.py
```

### What happens next?
- A lightweight local web server will spin up on `http://127.0.0.1:5050`.
- Your default web browser will automatically open to the SpotDown interface.
- You can search for songs, and the engine will seamlessly handle the downloads in the background, placing the MP3s directly into your computer's `Downloads` folder!
- To shut down the server, simply go to your terminal and press `Ctrl+C`.

Enjoy downloading!
