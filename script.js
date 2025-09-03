const video = document.getElementById('videoFeed');
const canvas = document.getElementById('canvas');
const baseURL = document.getElementById('baseURL');
const instructionText = document.getElementById('instructionText');
const responseText = document.getElementById('responseText');
const intervalSelect = document.getElementById('intervalSelect');
const startButton = document.getElementById('startButton');

instructionText.value = "What do you see?"; // default instruction

let stream;
let intervalId;
let isProcessing = false;

// Returns response text (string)
async function sendChatCompletionRequest(instruction, imageBase64URL) {
    const response = await fetch(`${baseURL.value}/v1/chat/completions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            max_tokens: 100,
            messages: [
                { role: 'user', content: [
                    { type: 'text', text: instruction },
                    { type: 'image_url', image_url: {
                        url: imageBase64URL,
                    } }
                ] },
            ]
        })
    });
    if (!response.ok) {
        const errorData = await response.text();
        return `Server error: ${response.status} - ${errorData}`;
    }
    const data = await response.json();
    return data.choices[0].message.content;
}

// 1. Ask for camera permission on load
async function initCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        video.srcObject = stream;
        responseText.value = "Camera access granted. Ready to start.";
    } catch (err) {
        console.error("Error accessing camera:", err);
        responseText.value = `Error accessing camera: ${err.name} - ${err.message}. Please ensure permissions are granted and you are on HTTPS or localhost.`;
        alert(`Error accessing camera: ${err.name}. Make sure you've granted permission and are on HTTPS or localhost.`);
    }
}

function captureImage() {
    if (!stream || !video.videoWidth) {
        console.warn("Video stream not ready for capture.");
        return null;
    }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.8); // Use JPEG for smaller size, 0.8 quality
}

async function sendData() {
    if (!isProcessing) return; // Ensure we don't have overlapping requests if processing takes longer than interval

    const instruction = instructionText.value;
    const imageBase64URL = captureImage();

    if (!imageBase64URL) {
        responseText.value = "Failed to capture image. Stream might not be active.";
        // Optionally stop processing if image capture fails consistently
        // handleStop();
        return;
    }

    const payload = {
        instruction: instruction,
        imageBase64URL: imageBase64URL
    };

    try {
        const response = await sendChatCompletionRequest(payload.instruction, payload.imageBase64URL);
        responseText.value = response;
    } catch (error) {
        console.error('Error sending data:', error);
        responseText.value = `Error: ${error.message}`;
    }
}

function handleStart() {
    if (!stream) {
        responseText.value = "Camera not available. Cannot start.";
        alert("Camera not available. Please grant permission first.");
        return;
    }
    isProcessing = true;
    startButton.textContent = "Stop";
    startButton.classList.remove('start');
    startButton.classList.add('stop');

    instructionText.disabled = true;
    intervalSelect.disabled = true;

    responseText.value = "Processing started...";

    const intervalMs = parseInt(intervalSelect.value, 10);
    
    // Initial immediate call
    sendData(); 
    
    // Then set interval
    intervalId = setInterval(sendData, intervalMs);
}

function handleStop() {
    isProcessing = false;
    if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
    }
    startButton.textContent = "Start";
    startButton.classList.remove('stop');
    startButton.classList.add('start');

    instructionText.disabled = false;
    intervalSelect.disabled = false;
    if (responseText.value.startsWith("Processing started...")) {
        responseText.value = "Processing stopped.";
    }
}

startButton.addEventListener('click', () => {
    if (isProcessing) {
        handleStop();
    } else {
        handleStart();
    }
});

// Initialize camera when the page loads
window.addEventListener('DOMContentLoaded', initCamera);

// Optional: Stop stream when page is closed/navigated away to release camera
window.addEventListener('beforeunload', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    if (intervalId) {
        clearInterval(intervalId);
    }
});