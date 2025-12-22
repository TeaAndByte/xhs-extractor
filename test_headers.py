
import requests

url = "http://sns-webpic-qc.xhscdn.com/202512221547/936cdf5cd728d854f77024e323fb1ec6/notes_pre_post/1040g3k031m3eu7ms4u005o06makg9bnrajfkao8"

headers_options = [
    {"name": "Empty Referer", "h": {"User-Agent": "Mozilla/5.0", "Referer": ""}},
    {"name": "XHS Referer", "h": {"User-Agent": "Mozilla/5.0", "Referer": "https://www.xiaohongshu.com/"}},
    {"name": "No Referer Header", "h": {"User-Agent": "Mozilla/5.0"}},
]

for opt in headers_options:
    try:
        resp = requests.head(url, headers=opt["h"], timeout=5)
        print(f"[{opt['name']}] Status: {resp.status_code}")
    except Exception as e:
        print(f"[{opt['name']}] Error: {e}")
