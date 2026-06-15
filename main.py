import os
import sys
import io
import shutil
import urllib.request
import zipfile
import imageio_ffmpeg
import json
import subprocess
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def ensure_ffmpeg():
    if sys.platform == 'win32':
        app_data = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'SpotDown', 'bin')
        ext = '.exe'
        ffprobe_url = "https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v6.1/ffprobe-6.1-win-64.zip"
    elif sys.platform == 'darwin':
        app_data = os.path.join(os.path.expanduser('~'), '.spotdown', 'bin')
        ext = ''
        ffprobe_url = "https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v6.1/ffprobe-6.1-osx-64.zip"
    else:
        app_data = os.path.join(os.path.expanduser('~'), '.spotdown', 'bin')
        ext = ''
        ffprobe_url = "https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v6.1/ffprobe-6.1-linux-64.zip"

    os.makedirs(app_data, exist_ok=True)
    
    ffmpeg_dest = os.path.join(app_data, f'ffmpeg{ext}')
    ffprobe_dest = os.path.join(app_data, f'ffprobe{ext}')
    
    if not os.path.exists(ffmpeg_dest):
        try:
            ffmpeg_src = imageio_ffmpeg.get_ffmpeg_exe()
            shutil.copy2(ffmpeg_src, ffmpeg_dest)
            if sys.platform != 'win32':
                os.chmod(ffmpeg_dest, 0o755)
        except Exception as e:
            pass
        
    if not os.path.exists(ffprobe_dest):
        try:
            req = urllib.request.Request(ffprobe_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                with zipfile.ZipFile(io.BytesIO(response.read())) as z:
                    for name in z.namelist():
                        if 'ffprobe' in name.lower():
                            with open(ffprobe_dest, 'wb') as f:
                                f.write(z.read(name))
                            break
            if sys.platform != 'win32':
                os.chmod(ffprobe_dest, 0o755)
        except Exception:
            pass
            
    # Also add the spotdl user directory to PATH so yt-dlp can find Deno
    try:
        from spotdl.utils.config import get_spotdl_path
        spotdl_dir = str(get_spotdl_path())
        if spotdl_dir not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + spotdl_dir
    except Exception:
        pass
            
    try:os.environ["PATH"] += os.pathsep + app_data
    except Exception: pass
    return app_data

# WORKER PROCESS FOR SPOTDL
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--spotdl-task':
        task_type = sys.argv[2]
        query = sys.argv[3]
        
        if sys.stdout is None:
            sys.stdout = io.StringIO()
        if sys.stderr is None:
            sys.stderr = io.StringIO()
            
        from spotdl import Spotdl
        from spotdl.utils.config import DEFAULT_CONFIG
        
        ensure_ffmpeg()
        
        temp_dir = os.path.join(get_base_path(), 'temp_downloads')
        os.makedirs(temp_dir, exist_ok=True)
        
        spotdl_instance = Spotdl(
            client_id=DEFAULT_CONFIG.get('client_id'),
            client_secret=DEFAULT_CONFIG.get('client_secret'),
            user_auth=False,
            headless=False,
            downloader_settings={
                'audio_providers': ['youtube'],
                'output': os.path.join(temp_dir, '{artists} - {title}.{ext}'),
                'format': 'mp3',
                'bitrate': '320k',
                'ffmpeg': 'ffmpeg'
            }
        )
        
        if task_type == 'search':
            try:
                from spotdl.utils.spotify import SpotifyClient
                client = SpotifyClient()
                res = client.search(query, type="track", limit=50)
                
                results = []
                if hasattr(res, 'keys') and 'tracks' in res:
                    for t in res['tracks']['items'][:50]: 
                        images = t['album'].get('images', [])
                        cover = images[0]['url'] if images else "https://via.placeholder.com/55"
                        results.append({
                            "name": t['name'],
                            "artist": t['artists'][0]['name'],
                            "cover_url": cover,
                            "url": t['external_urls']['spotify']
                        })
                print("SPOTDL_RESULT_START")
                print(json.dumps({"status": "success", "results": results}))
                print("SPOTDL_RESULT_END")
            except Exception as e:
                print("SPOTDL_RESULT_START")
                print(json.dumps({"status": "error", "message": str(e)}))
                print("SPOTDL_RESULT_END")
        
        elif task_type == 'download':
            try:
                songs = spotdl_instance.search([query])
                if not songs:
                    print("SPOTDL_RESULT_START")
                    print(json.dumps({"status": "error", "message": "Song not found"}))
                    print("SPOTDL_RESULT_END")
                    sys.exit(0)
                
                song = songs[0]
                result = spotdl_instance.download(song)
                if result and len(result) == 2 and result[1]:
                    print("SPOTDL_RESULT_START")
                    print(json.dumps({"status": "success", "file_path": str(result[1])}))
                    print("SPOTDL_RESULT_END")
                else:
                    print("SPOTDL_RESULT_START")
                    print(json.dumps({"status": "error", "message": "Download failed inside engine"}))
                    print("SPOTDL_RESULT_END")
            except Exception as e:
                print("SPOTDL_RESULT_START")
                print(json.dumps({"status": "error", "message": str(e)}))
                print("SPOTDL_RESULT_END")
                
        sys.exit(0)

class Api:
    def __init__(self):
        ensure_ffmpeg()

    def run_worker(self, task_type, query):
        try:
            exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.executable
            
            cmd = [exe_path]
            if not getattr(sys, 'frozen', False):
                cmd.append(__file__)
            cmd.extend(["--spotdl-task", task_type, query])
            
            creationflags = 0
            if sys.platform == 'win32':
                creationflags = 0x08000000 # CREATE_NO_WINDOW
                
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=creationflags
            )
            
            output = process.stdout
            if "SPOTDL_RESULT_START" in output and "SPOTDL_RESULT_END" in output:
                start = output.find("SPOTDL_RESULT_START") + len("SPOTDL_RESULT_START")
                end = output.find("SPOTDL_RESULT_END")
                json_str = output[start:end].strip()
                return json.loads(json_str)
            else:
                print(process.stderr)
                return {"status": "error", "message": "Engine crashed or returned invalid output"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def search(self, query):
        res = self.run_worker('search', query)
        if res.get('status') == 'success':
            return res.get('results', [])
        else:
            print("Error searching:", res.get('message'))
            return []

    def download(self, url):
        return self.run_worker('download', url)

class SpotDownAPIHandler(SimpleHTTPRequestHandler):
    api = Api()

    def do_POST(self):
        if self.path == '/api/search':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            results = self.api.search(data.get('query', ''))
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results).encode('utf-8'))
            
        elif self.path == '/api/download':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            result = self.api.download(data.get('url', ''))
            
            if result.get('status') == 'success':
                file_path = result.get('file_path')
                if file_path and os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/mpeg')
                    self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                    self.end_headers()
                    
                    with open(file_path, 'rb') as f:
                        shutil.copyfileobj(f, self.wfile)
                        
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    return
                else:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "File was downloaded but could not be located"}).encode('utf-8'))
            else:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def start_server():
    os.chdir(get_base_path())
    port = int(os.environ.get('PORT', 5050))
    try:
        httpd = HTTPServer(('0.0.0.0', port), SpotDownAPIHandler)
        print(f"SpotDown Server running at port {port}. Press Ctrl+C to stop.")
        httpd.serve_forever()
    except OSError:
        print(f"Port {port} is already in use. Assuming server is already running.")

if __name__ == '__main__':
    print("Starting SpotDown Cross-Platform Engine...")
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    import time
    time.sleep(0.5)
    
    webbrowser.open('http://127.0.0.1:5050/index.html')
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
