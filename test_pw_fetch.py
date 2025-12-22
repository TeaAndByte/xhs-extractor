
from playwright.sync_api import sync_playwright
import os

USER_DATA_DIR = "./user_data"
STORAGE_STATE_PATH = os.path.join(USER_DATA_DIR, "state.json")
url = "http://sns-webpic-qc.xhscdn.com/202512221547/936cdf5cd728d854f77024e323fb1ec6/notes_pre_post/1040g3k031m3eu7ms4u005o06makg9bnrajfkao8"

with sync_playwright() as p:
    # Use the same state as the login session
    if os.path.exists(STORAGE_STATE_PATH):
        print("Using saved state.")
        context = p.request.new_context(storage_state=STORAGE_STATE_PATH)
    else:
        print("No saved state, making fresh context.")
        context = p.request.new_context()
    
    response = context.get(url)
    print(f"Status: {response.status}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Size: {len(response.body())}")
