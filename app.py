from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import os
import time
import requests

app = Flask(__name__, static_folder='public')
CORS(app)

USER_DATA_DIR = "./user_data"
STORAGE_STATE_PATH = os.path.join(USER_DATA_DIR, "state.json")

if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

@app.route('/api/proxy')
def proxy_image():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    try:
        # Fetch image with proper XHS headers
        req_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }
        resp = requests.get(url, headers=req_headers, stream=True, timeout=15)
        resp.raise_for_status()
        
        # Pass through the content type and data
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        
        return app.response_class(
            resp.content,
            status=resp.status_code,
            headers=headers
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/login', methods=['POST'])
def login():
    try:
        with sync_playwright() as p:
            # Launch visible browser
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            print("Opening login page...")
            page.goto("https://www.xiaohongshu.com/")
            
            # Wait for user to interact
            print("Waiting for user to login and close the browser...")
            # Wait indefinitely until the user closes the page/browser
            try:
                page.wait_for_event("close", timeout=0) # 0 means no timeout
            except:
                pass # Event might be triggered or context closed
            
            # After user closes window, we save the state
            context.storage_state(path=STORAGE_STATE_PATH)
            return jsonify({"success": True, "message": "Session saved after window closed!"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        with sync_playwright() as p:
            # Use headless=False to avoid detection and let user see/solve captchas
            browser = p.chromium.launch(headless=False)
            
            # Load auth state if exists
            if os.path.exists(STORAGE_STATE_PATH):
                context = browser.new_context(storage_state=STORAGE_STATE_PATH)
            else:
                context = browser.new_context()
            
            page = context.new_page()
            
            # Handle short links redirection if needed, Playwright follows redirects automatically
            page.goto(url)
            
            # Wait specifically for the state to be populated
            try: 
                 page.wait_for_selector('script', state='attached', timeout=5000)
            except:
                 pass
            time.sleep(2) # Give it a moment for any hydration or redirects

            # Extract data
            result = page.evaluate("""() => {
                try {
                    const state = window.__INITIAL_STATE__;
                    if (!state) return { error: 'No __INITIAL_STATE__ found' };
                    
                    if (!state.note || !state.note.noteDetailMap) {
                        // Sometimes structure is different or requires login
                        return { error: 'Note data not found in state. Log in required?' };
                    }
                    
                    // Find the note object
                    const map = state.note.noteDetailMap;
                    const noteIds = Object.keys(map);
                    if (noteIds.length === 0) return { error: 'No note ID in map' };
                    
                    const noteId = noteIds[0];
                    const noteData = map[noteId];
                    if (!noteData || !noteData.note) return { error: 'Invalid note structure' };
                    
                    const note = noteData.note;
                    
                    // Handle imageList being undefined (e.g. video posts)
                    const imageList = note.imageList || [];
                    
                    if (imageList.length === 0) {
                        return { 
                            title: note.title, 
                            desc: note.desc, 
                            images: [],
                            warning: 'No images found. This might be a video post or blocked.' 
                        };
                    }

                    const images = imageList.map(img => {
                         // Use the raw URL to ensure signature validity
                         let originalUrl = img.urlDefault || img.url;
                         // if (originalUrl && originalUrl.includes('!')) {
                         //     originalUrl = originalUrl.split('!')[0];
                         // }
                         return originalUrl;
                    });

                    return {
                        title: note.title,
                        desc: note.desc,
                        images: images
                    };
                } catch (e) {
                    return { error: e.toString() };
                }
            }""")
            
            # Keep browser open if headless=False so user can see what happened? 
            # No, user wants result. We close it.
            browser.close()
            
            if not result:
                return jsonify({"error": "Unknown error during extraction"}), 500
                
            if result.get('error'):
                 return jsonify({"error": result['error']}), 400
                 
            return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # host='0.0.0.0' allows access from other devices (like your phone)
    app.run(host='0.0.0.0', port=5000, debug=True)
