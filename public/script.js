const API_BASE = '/api';

const urlInput = document.getElementById('urlInput');
const extractBtn = document.getElementById('extractBtn');
const loginBtn = document.getElementById('loginBtn');
const statusMsg = document.getElementById('statusMsg');
const resultSection = document.getElementById('resultSection');
const imageGrid = document.getElementById('imageGrid');
const noteTitle = document.getElementById('noteTitle');
const noteDesc = document.getElementById('noteDesc');
const imageCount = document.getElementById('imageCount');
const downloadAllBtn = document.getElementById('downloadAllBtn');

let currentImages = [];
let currentTitle = 'xhs-images';

function setStatus(message, type = 'normal') {
    statusMsg.textContent = message;
    statusMsg.className = 'status-message';
    if (type === 'error') statusMsg.classList.add('status-error');
    if (type === 'success') statusMsg.classList.add('status-success');
    if (type === 'loading') statusMsg.classList.add('status-loading');
}

async function readJson(response) {
    try {
        return await response.json();
    } catch {
        return { success: false, error: '服务器返回了非 JSON 响应（HTTP ' + response.status + '）' };
    }
}

function normalizeShareUrl(rawText) {
    const match = rawText.match(/https?:\/\/[^\s，,]+/i);
    return (match ? match[0] : rawText).replace(/[。；;）)\]】]+$/, '');
}

function proxyUrl(url) {
    return API_BASE + '/proxy?url=' + encodeURIComponent(url);
}

function fileExtension(blob) {
    const extensions = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/webp': 'webp',
        'image/gif': 'gif',
        'image/avif': 'avif'
    };
    return extensions[blob.type] || 'jpg';
}

function safeFileName(value) {
    return (value || 'xhs-images')
        .replace(/[\\\/:*?"<>|\x00-\x1f]/g, '_')
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, 60) || 'xhs-images';
}

async function fetchImage(url) {
    const response = await fetch(proxyUrl(url));
    if (!response.ok) {
        const data = await readJson(response);
        throw new Error(data.error || '图片下载失败（HTTP ' + response.status + '）');
    }
    return response.blob();
}

function renderImages(data) {
    currentImages = Array.isArray(data.images) ? data.images : [];
    currentTitle = safeFileName(data.title);
    noteTitle.textContent = data.title || '未命名笔记';
    noteDesc.textContent = data.desc || '';
    noteDesc.hidden = !data.desc;
    imageCount.textContent = currentImages.length + ' 张图片';
    imageGrid.replaceChildren();
    resultSection.classList.remove('hidden');

    if (!currentImages.length) {
        const empty = document.createElement('p');
        empty.className = 'empty-state';
        empty.textContent = data.warning || '这篇笔记没有提取到图片。';
        imageGrid.appendChild(empty);
        downloadAllBtn.disabled = true;
        return;
    }

    downloadAllBtn.disabled = false;

    currentImages.forEach((url, index) => {
        const card = document.createElement('article');
        card.className = 'image-card';

        const image = document.createElement('img');
        image.src = proxyUrl(url);
        image.alt = '笔记图片 ' + (index + 1);
        image.loading = 'lazy';
        image.decoding = 'async';
        image.addEventListener('error', () => {
            image.alt = '图片 ' + (index + 1) + ' 加载失败，可尝试重新提取';
            card.classList.add('image-load-error');
        });

        const overlay = document.createElement('div');
        overlay.className = 'image-overlay';

        const downloadButton = document.createElement('button');
        downloadButton.className = 'action-btn';
        downloadButton.type = 'button';
        downloadButton.title = '下载这张图片';
        downloadButton.setAttribute('aria-label', '下载第 ' + (index + 1) + ' 张图片');
        downloadButton.innerHTML = '<i class="fa-solid fa-download" aria-hidden="true"></i>';
        downloadButton.addEventListener('click', () => downloadSingle(url, index));

        overlay.appendChild(downloadButton);
        card.append(image, overlay);
        imageGrid.appendChild(card);
    });
}

loginBtn.addEventListener('click', async () => {
    loginBtn.disabled = true;
    setStatus('正在启动登录浏览器。请在服务所在电脑完成登录，并关闭登录标签页。', 'loading');

    try {
        const response = await fetch(API_BASE + '/login', { method: 'POST' });
        const data = await readJson(response);
        if (!response.ok || !data.success) {
            throw new Error(data.error || '登录失败');
        }
        setStatus('登录状态已保存，可以开始提取笔记图片。', 'success');
    } catch (error) {
        setStatus(error.message, 'error');
    } finally {
        loginBtn.disabled = false;
    }
});

extractBtn.addEventListener('click', async () => {
    const url = normalizeShareUrl(urlInput.value.trim());
    if (!url) {
        setStatus('请先粘贴小红书笔记链接或分享文案。', 'error');
        return;
    }

    extractBtn.disabled = true;
    resultSection.classList.add('hidden');
    imageGrid.replaceChildren();
    setStatus('正在打开笔记并提取图片，请稍候……', 'loading');

    try {
        const response = await fetch(API_BASE + '/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        const data = await readJson(response);
        if (!response.ok || !data.success) {
            throw new Error(data.error || '提取失败');
        }

        renderImages(data);
        if (data.images && data.images.length) {
            setStatus('提取完成，共找到 ' + data.images.length + ' 张图片。', 'success');
        } else {
            setStatus(data.warning || '笔记已解析，但没有找到图片。', 'normal');
        }
    } catch (error) {
        setStatus('提取失败：' + error.message, 'error');
    } finally {
        extractBtn.disabled = false;
    }
});

async function downloadSingle(url, index) {
    try {
        setStatus('正在下载第 ' + (index + 1) + ' 张图片……', 'loading');
        const blob = await fetchImage(url);
        saveAs(blob, currentTitle + '_' + String(index + 1).padStart(2, '0') + '.' + fileExtension(blob));
        setStatus('第 ' + (index + 1) + ' 张图片下载已开始。', 'success');
    } catch (error) {
        setStatus('下载失败：' + error.message, 'error');
    }
}

downloadAllBtn.addEventListener('click', async () => {
    if (!currentImages.length) return;

    downloadAllBtn.disabled = true;
    downloadAllBtn.innerHTML = '<i class="fa-solid fa-spinner"></i> 正在打包…';
    setStatus('正在下载 ' + currentImages.length + ' 张图片并生成 ZIP……', 'loading');

    const zip = new JSZip();
    const folder = zip.folder(currentTitle);
    let successCount = 0;
    let failureCount = 0;

    try {
        // 分批下载，避免同时请求过多图片。
        for (let start = 0; start < currentImages.length; start += 4) {
            const batch = currentImages.slice(start, start + 4);
            await Promise.all(batch.map(async (url, offset) => {
                const index = start + offset;
                try {
                    const blob = await fetchImage(url);
                    folder.file('image_' + String(index + 1).padStart(3, '0') + '.' + fileExtension(blob), blob);
                    successCount += 1;
                } catch (error) {
                    console.warn('第 ' + (index + 1) + ' 张图片下载失败', error);
                    failureCount += 1;
                }
            }));
            setStatus('已处理 ' + Math.min(start + 4, currentImages.length) + ' / ' + currentImages.length + ' 张图片……', 'loading');
        }

        if (!successCount) {
            throw new Error('所有图片均下载失败，请重新提取或检查网络。');
        }

        const content = await zip.generateAsync({ type: 'blob' });
        saveAs(content, currentTitle + '.zip');
        setStatus(
            failureCount
                ? 'ZIP 已生成：成功 ' + successCount + ' 张，失败 ' + failureCount + ' 张。'
                : 'ZIP 已生成：全部 ' + successCount + ' 张图片已打包。',
            failureCount ? 'normal' : 'success'
        );
    } catch (error) {
        setStatus('批量下载失败：' + error.message, 'error');
    } finally {
        downloadAllBtn.disabled = currentImages.length === 0;
        downloadAllBtn.innerHTML = '<i class="fa-solid fa-download"></i> 下载全部图片';
    }
});

urlInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') extractBtn.click();
});
