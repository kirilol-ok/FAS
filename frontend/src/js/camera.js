// Camera Live View Script
const API_BASE_URL = "http://localhost:";

const video = document.getElementById('videoStream');
const overlay = document.getElementById('overlay');
const status = document.getElementById('status');
const statusText = document.getElementById('statusText');

let stream = null;

// Start camera stream automatically
async function startStream() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1920 },
                height: { ideal: 1080 },
                frameRate: { ideal: 30 }
            },
            audio: false
        });

        video.srcObject = stream;
        overlay.style.display = 'none';
        
        status.classList.remove('offline');
        statusText.textContent = 'Live';

    } catch (error) {
        console.error('Error accessing camera:', error);
        overlay.innerHTML = '<span> Camera access denied or not available</span>';
        status.classList.add('offline');
        statusText.textContent = 'Error';
    }
}

// Start stream automatically on page load
window.addEventListener('load', startStream);

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
});