# VLM Webcam + MongoDB

![demo](./demo.png)

Web app that captures webcam frames, sends them to a VLM server (llama.cpp) at `http://localhost:8080`, and saves the text shown in the “Response” field to MongoDB.

## Overview

- Browser (index.html) captures frames and calls the VLM API (`/v1/chat/completions`).
- The returned text is displayed and posted to the Python server (port 3000) to persist in MongoDB.
- Only the text shown in the “Response” area is saved with payload `{ response: string }`.

Architecture:
- UI (browser) → VLM `http://localhost:8080`
- UI (browser) → Persistence `http://localhost:3000/save-response`
- Persistence (Flask/Python) → MongoDB `mongodb://localhost:27017/vlm-webcam-responses`

## Requirements

- Python 3.9+
- MongoDB running locally
- [llama.cpp](https://github.com/ggml-org/llama.cpp) (VLM server)

Create a `.env` (defaults also work):

```
PORT=3000
MONGODB_URI=mongodb://localhost:27017/vlm-webcam-responses
# Optional: used only if you choose to proxy the VLM API via the Python server
UPSTREAM_API_BASE=http://localhost:8080
```

## Run (Python backend)

1) Start the VLM server (port 8080)

```
llama-server -hf ggml-org/SmolVLM-500M-Instruct-GGUF
# Tip: you can add -ngl 99 for GPU (NVidia/AMD/Intel)
```

2) Ensure MongoDB is running locally

3) Start the Python persistence server (port 3000)

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

4) Open the UI

- Open `index.html` in your browser OR visit `http://localhost:3000` (Flask also serves the static files).
- Keep “Base API” as `http://localhost:8080`.
- Click “Start”. The “Response” field shows model output; each response is saved to MongoDB.

## Server Endpoints (port 3000)

- `POST /save-response`
  - Body: `{ "response": "<text shown in UI>" }`
  - Returns: `{ message, id }`

- `GET /responses`
  - Query params: `limit` (1–200, default 50), `skip` (>=0), `order` (`asc|desc`, default `desc`)
  - Returns: `{ count, items }`

- `GET /db-status`
  - Check MongoDB connection status.

- (Optional) `POST /v1/chat/completions` (proxy)
  - Forwards the request to the VLM configured in `UPSTREAM_API_BASE`.
  - Use this if you want to set the UI “Base API” to `http://localhost:3000` and avoid CORS.

 

## How It Works

1. Browser uses `getUserMedia` to access the camera, renders to `<video>`, and captures frames as base64 using `<canvas>`.
2. At a configured interval, it sends the frame and instruction to `http://localhost:8080/v1/chat/completions`.
3. The text response is displayed and posted to `http://localhost:3000/save-response`.
4. The Python server inserts `{ message: <text>, date: <now> }` into the `responses` collection of the DB specified by `MONGODB_URI`.

## Troubleshooting

- Check DB connectivity: `GET http://localhost:3000/db-status` should return `connected`.
- If the UI cannot call `8080` due to CORS in your environment, either:
  - Serve the UI from Flask at `http://localhost:3000` and keep “Base API = http://localhost:8080`”, or
  - Set “Base API = http://localhost:3000” in the UI to use the `/v1/chat/completions` proxy (Python → 8080).
- The server logs each request, a safe body preview, and the `_id` when a response is saved.
- Ensure MongoDB is running and `MONGODB_URI` is correct.
 

## Customization

- Adjust the interval between requests in the UI.
- Edit the instruction text.
- Data is stored in the `responses` collection of the DB defined in `MONGODB_URI`.
