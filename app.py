"""小红书笔记图片提取服务。

仅解析用户主动提供的公开笔记/分享链接，并通过受限图片代理返回图片。
不提供登录绕过、验证码绕过或访问私有内容的能力。
"""
from __future__ import annotations

import logging
import os
import re
from urllib.parse import urljoin, urlparse

import requests
from flask import Flask, Response, jsonify, request, send_from_directory
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
DATA_DIR = os.environ.get("XHS_DATA_DIR", os.path.join(BASE_DIR, "user_data"))
STORAGE_STATE_PATH = os.path.join(DATA_DIR, "state.json")

NOTE_HOSTS = ("xiaohongshu.com", "xhslink.com")
IMAGE_HOSTS = ("xhscdn.com", "xhscdn.net")
MAX_IMAGE_BYTES = int(os.environ.get("XHS_MAX_IMAGE_BYTES", str(25 * 1024 * 1024)))
BROWSER_TIMEOUT_MS = int(os.environ.get("XHS_BROWSER_TIMEOUT_MS", "45000"))
LOGIN_ENABLED = os.environ.get("XHS_ENABLE_BROWSER_LOGIN", "true").lower() in ("1", "true", "yes")

os.makedirs(DATA_DIR, mode=0o700, exist_ok=True)

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("xhs-extractor")

app = Flask(__name__, static_folder=PUBLIC_DIR)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


def _host_matches(host: str, allowed_hosts: tuple[str, ...]) -> bool:
    host = (host or "").lower().rstrip(".")
    return any(host == domain or host.endswith("." + domain) for domain in allowed_hosts)


def _validate_http_url(raw_url: str, allowed_hosts: tuple[str, ...]) -> str:
    if not isinstance(raw_url, str) or not raw_url.strip():
        raise ValueError("请提供有效的 URL")

    parsed = urlparse(raw_url.strip())
    if parsed.scheme not in ("http", "https"):
        raise ValueError("仅支持 HTTP 或 HTTPS 链接")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL 格式不正确")
    if parsed.port not in (None, 80, 443):
        raise ValueError("不支持自定义端口")
    if not _host_matches(parsed.hostname, allowed_hosts):
        raise ValueError("链接域名不在允许范围内")

    return parsed.geturl()


def extract_share_url(value: str) -> str:
    """支持直接粘贴 URL，也支持粘贴包含 URL 的分享文案。"""
    if not isinstance(value, str):
        raise ValueError("请粘贴小红书笔记链接")
    match = re.search(r"https?://[^\s，,]+", value.strip())
    candidate = match.group(0) if match else value.strip()
    return _validate_http_url(candidate.rstrip("。；;）)】]"), NOTE_HOSTS)


def validate_note_url(url: str) -> str:
    return _validate_http_url(url, NOTE_HOSTS)


def validate_image_url(url: str) -> str:
    return _validate_http_url(url, IMAGE_HOSTS)


def _json_error(message: str, status: int):
    return jsonify({"success": False, "error": message}), status


def _extract_note_data(page):
    return page.evaluate(
        """() => {
            const state = window.__INITIAL_STATE__;
            const map = state?.note?.noteDetailMap;
            if (!map || typeof map !== 'object') {
                return { error: '未能读取笔记数据，页面可能尚未加载完成，或需要先登录' };
            }

            const entries = Object.entries(map);
            if (!entries.length) return { error: '页面中没有找到笔记详情' };

            const pathParts = location.pathname.split('/').filter(Boolean);
            const possibleId = pathParts[pathParts.length - 1];
            const selected = map[possibleId] ? [possibleId, map[possibleId]] : entries[0];
            const [noteId, detail] = selected;
            const note = detail?.note || detail;

            if (!note || typeof note !== 'object') {
                return { error: '笔记数据结构不完整' };
            }

            const imageList = Array.isArray(note.imageList) ? note.imageList : [];
            const images = imageList.map((image) => {
                const infoUrl = Array.isArray(image?.infoList)
                    ? image.infoList.find(item => item?.url)?.url
                    : null;
                return image?.urlDefault || image?.url || infoUrl || null;
            }).filter(url => typeof url === 'string' && /^https?:\\/\\//i.test(url));

            return {
                noteId: note.noteId || noteId,
                title: note.title || '',
                desc: note.desc || '',
                type: note.type || '',
                author: note.user?.nickname || '',
                images: [...new Set(images)],
                warning: images.length ? '' : '没有找到图片。该笔记可能是视频内容，或平台页面结构已发生变化。'
            };
        }"""
    )


@app.get("/")
def serve_index():
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "success": True,
        "service": "xhs-extractor",
        "login_enabled": LOGIN_ENABLED,
        "login_state_exists": os.path.isfile(STORAGE_STATE_PATH),
    })


@app.get("/<path:path>")
def serve_static(path: str):
    return send_from_directory(PUBLIC_DIR, path)


@app.post("/api/login")
def login():
    """在运行服务的本机打开浏览器登录；云端无桌面环境时应关闭此功能。"""
    if not LOGIN_ENABLED:
        return _json_error("当前部署已禁用浏览器登录。请在本机运行服务完成登录，或使用已有登录状态。", 503)

    browser = None
    context = None
    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=False)
            except Exception as exc:
                logger.warning("无法启动可视化浏览器: %s", exc)
                return _json_error(
                    "无法启动可视化浏览器。请在有桌面环境的本机运行，或先安装 Playwright Chromium。",
                    503,
                )

            context = browser.new_context()
            page = context.new_page()
            page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT_MS)
            logger.info("已打开小红书登录页；登录后请关闭该浏览器标签页以保存登录状态")

            # 用户完成登录后关闭页面，随后保存当前 context 的登录状态。
            page.wait_for_event("close", timeout=0)
            context.storage_state(path=STORAGE_STATE_PATH)
            try:
                os.chmod(STORAGE_STATE_PATH, 0o600)
            except OSError:
                pass

            return jsonify({"success": True, "message": "登录状态已保存"})
    except PlaywrightTimeoutError:
        return _json_error("打开小红书登录页超时，请检查网络后重试", 504)
    except Exception:
        logger.exception("登录流程失败")
        return _json_error("登录流程失败，请查看服务端日志", 500)
    finally:
        if context:
            try:
                context.close()
            except Exception:
                pass
        if browser:
            try:
                browser.close()
            except Exception:
                pass


@app.post("/api/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    try:
        note_url = extract_share_url(data.get("url", ""))
    except ValueError as exc:
        return _json_error(str(exc), 400)

    browser = None
    context = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context_options = {}
            if os.path.isfile(STORAGE_STATE_PATH):
                context_options["storage_state"] = STORAGE_STATE_PATH
            context = browser.new_context(**context_options)
            page = context.new_page()
            page.set_default_navigation_timeout(BROWSER_TIMEOUT_MS)
            page.goto(note_url, wait_until="domcontentloaded")
            try:
                page.wait_for_function(
                    "() => Boolean(window.__INITIAL_STATE__?.note?.noteDetailMap)",
                    timeout=12000,
                )
            except PlaywrightTimeoutError:
                # 继续读取一次，以便返回更具体的页面状态错误。
                pass

            # 短链接可能跳转；最终页面仍必须属于小红书域名。
            validate_note_url(page.url)
            result = _extract_note_data(page)

            if not result or result.get("error"):
                return _json_error((result or {}).get("error", "提取失败"), 422)

            result["success"] = True
            result["sourceUrl"] = page.url
            result["imageCount"] = len(result.get("images", []))
            return jsonify(result)
    except ValueError as exc:
        return _json_error(str(exc), 400)
    except PlaywrightTimeoutError:
        return _json_error("访问笔记超时，请检查网络、登录状态或稍后重试", 504)
    except Exception:
        logger.exception("笔记提取失败")
        return _json_error("提取失败，请确认链接有效，并查看服务端日志", 502)
    finally:
        if context:
            try:
                context.close()
            except Exception:
                pass
        if browser:
            try:
                browser.close()
            except Exception:
                pass


@app.get("/api/proxy")
def proxy_image():
    """受限图片代理：仅允许小红书图片 CDN，且逐跳校验重定向地址。"""
    try:
        image_url = validate_image_url(request.args.get("url", ""))
    except ValueError as exc:
        return _json_error(str(exc), 400)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.xiaohongshu.com/",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }

    current_url = image_url
    try:
        for _ in range(4):
            with requests.get(
                current_url,
                headers=headers,
                stream=True,
                timeout=(5, 20),
                allow_redirects=False,
            ) as upstream:
                if upstream.status_code in (301, 302, 303, 307, 308):
                    location = upstream.headers.get("Location")
                    if not location:
                        return _json_error("图片服务器返回了无效重定向", 502)
                    current_url = validate_image_url(urljoin(current_url, location))
                    continue

                upstream.raise_for_status()
                content_type = upstream.headers.get("Content-Type", "").split(";")[0].lower()
                if not content_type.startswith("image/"):
                    return _json_error("目标地址返回的不是图片", 415)

                content_length = upstream.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_IMAGE_BYTES:
                    return _json_error("图片文件超过大小限制", 413)

                chunks = []
                total = 0
                for chunk in upstream.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > MAX_IMAGE_BYTES:
                        return _json_error("图片文件超过大小限制", 413)
                    chunks.append(chunk)

                return Response(
                    b"".join(chunks),
                    mimetype=content_type,
                    headers={
                        "Cache-Control": "private, max-age=300",
                        "X-Content-Type-Options": "nosniff",
                    },
                )

        return _json_error("图片服务器重定向次数过多", 502)
    except ValueError as exc:
        return _json_error(str(exc), 400)
    except requests.RequestException:
        logger.exception("图片代理请求失败")
        return _json_error("图片下载失败，链接可能已过期或受到平台限制", 502)
    except Exception:
        logger.exception("图片代理发生未知错误")
        return _json_error("图片代理发生错误", 500)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
