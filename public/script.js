
const API_BASE = 'http://localhost:5000/api';

const urlInput = document.getElementById('urlInput');
const extractBtn = document.getElementById('extractBtn');
const loginBtn = document.getElementById('loginBtn');
const statusMsg = document.getElementById('statusMsg');
const resultSection = document.getElementById('resultSection');
const imageGrid = document.getElementById('imageGrid');
const noteTitle = document.getElementById('noteTitle');
const downloadAllBtn = document.getElementById('downloadAllBtn');

let currentImages = [];

// Helper to set status
function setStatus(msg, type = 'normal') {
    statusMsg.textContent = msg;
    statusMsg.className = 'status-message'; // reset
    if (type === 'error') statusMsg.classList.add('status-error');
    if (type === 'success') statusMsg.classList.add('status-success');
    if (type === 'loading') statusMsg.classList.add('status-loading');
}

// Login Handler
loginBtn.addEventListener('click', async () => {
    setStatus('Launching login window... Please login in the new window.', 'loading');
    loginBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/login`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            setStatus('Login successful! You can now extract images.', 'success');
        } else {
            setStatus(`Login failed: ${data.message}`, 'error');
        }
    } catch (error) {
        setStatus(`Error: ${error.message}`, 'error');
    } finally {
        loginBtn.disabled = false;
    }
});

// Extract Handler
extractBtn.addEventListener('click', async () => {
    const rawInput = urlInput.value.trim();
    // Extract URL from text (support full share text)
    const urlMatch = rawInput.match(/(https?:\/\/[^\s,，]+)/);
    const url = urlMatch ? urlMatch[0] : rawInput;
    if (!url) {
        setStatus('Please enter a valid URL.', 'error');
        return;
    }

    setStatus('Analyzing link and extracting images... This make take a few seconds.', 'loading');
    extractBtn.disabled = true;
    resultSection.classList.add('hidden');
    imageGrid.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (response.ok) {
            currentImages = data.images;
            renderImages(data);
            setStatus(`Successfully extracted ${data.images.length} images!`, 'success');
        } else {
            setStatus(`Extraction failed: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        setStatus(`Network Error: ${error.message}`, 'error');
    } finally {
        extractBtn.disabled = false;
    }
});

// Render Images
function renderImages(data) {
    noteTitle.textContent = data.title || 'Untitled Note';
    resultSection.classList.remove('hidden');

    data.images.forEach((imgUrl, index) => {
        const card = document.createElement('div');
        card.className = 'image-card';

        // Use backend proxy for display as well to guarantee loading
        const proxyUrl = `${API_BASE}/proxy?url=${encodeURIComponent(imgUrl)}`;

        card.innerHTML = `
            <img src="${proxyUrl}" alt="Image ${index + 1}" loading="lazy">
            <div class="image-overlay">
                <button class="action-btn" onclick="downloadSingle('${imgUrl}', ${index})">
                    <i class="fa-solid fa-download"></i>
                </button>
            </div>
        `;
        imageGrid.appendChild(card);
    });
}

// Download All
downloadAllBtn.addEventListener('click', async () => {
    if (currentImages.length === 0) return;

    downloadAllBtn.innerHTML = '<i class="fa-solid fa-spinner"></i> Zipping...';
    downloadAllBtn.disabled = true;

    const zip = new JSZip();
    const folder = zip.folder("xhs-images");

    try {
        const promises = currentImages.map(async (url, i) => {
            try {
                // Use backend proxy to avoid CORS/Referrer issues during download
                const proxyUrl = `${API_BASE}/proxy?url=${encodeURIComponent(url)}`;
                const response = await fetch(proxyUrl);

                if (!response.ok) throw new Error('Network response was not ok');
                const blob = await response.blob();

                // Try to detect extension from blob type or url
                let ext = 'jpg';
                const type = blob.type;
                if (type === 'image/jpeg') ext = 'jpg';
                else if (type === 'image/png') ext = 'png';
                else if (type === 'image/webp') ext = 'webp';
                else if (type === 'image/gif') ext = 'gif';

                folder.file(`image_${i + 1}.${ext}`, blob);
            } catch (e) {
                console.error("Failed to download image for zip:", url, e);
            }
        });

        await Promise.all(promises);

        const content = await zip.generateAsync({ type: "blob" });
        saveAs(content, "xhs_images.zip");

    } catch (err) {
        alert("Failed to create zip: " + err.message);
    } finally {
        downloadAllBtn.innerHTML = '<i class="fa-solid fa-download"></i> Download All';
        downloadAllBtn.disabled = false;
    }
});

// Download Single
// Download Single
window.downloadSingle = async (url, index) => {
    try {
        const proxyUrl = `${API_BASE}/proxy?url=${encodeURIComponent(url)}`;
        const response = await fetch(proxyUrl);
        if (!response.ok) throw new Error('Network response was not ok');

        const blob = await response.blob();

        // Better extension detection
        let ext = 'jpg';
        const type = blob.type;
        if (type === 'image/jpeg') ext = 'jpg';
        else if (type === 'image/png') ext = 'png';
        else if (type === 'image/webp') ext = 'webp';
        else if (type === 'image/gif') ext = 'gif';
        else if (type === 'image/avif') ext = 'avif';

        saveAs(blob, `xhs_image_${index + 1}.${ext}`);
    } catch (e) {
        console.error("Download failed:", e);
        window.open(url, '_blank'); // Fallback
    }
};
