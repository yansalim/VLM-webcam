import os
import time
from urllib.parse import urlparse
from flask import Flask, request, jsonify, send_from_directory, Response
from pymongo import MongoClient, ASCENDING, DESCENDING

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

PORT = int(os.environ.get("PORT", "3000"))
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/vlm-webcam-responses")
UPSTREAM_API_BASE = os.environ.get("UPSTREAM_API_BASE", "http://localhost:8080")

app = Flask(__name__, static_folder=None)

client = MongoClient(MONGODB_URI)

parsed = urlparse(MONGODB_URI)
db_name = parsed.path.lstrip("/") or "vlm-webcam-responses"


def cors_headers(resp: Response) -> Response:
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return resp


@app.before_request
def log_request():
    request.start_time = time.time()


@app.after_request
def log_response(response):
    try:
        ms = int((time.time() - getattr(request, "start_time", time.time())) * 1000)
        origin = request.headers.get("Origin", "n/a")
        line = f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] {request.method} {request.full_path} {response.status_code} - {ms}ms - origin={origin}"
        print(line)
    except Exception:
        pass
    return cors_headers(response)


@app.route("/db-status", methods=["GET", "OPTIONS"])
def db_status():
    if request.method == "OPTIONS":
        return cors_headers(Response(status=204))
    try:
        client.admin.command("ping")
        return jsonify({"status": "connected", "db": db_name})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/save-response", methods=["POST", "OPTIONS"])
def save_response():
    if request.method == "OPTIONS":
        return cors_headers(Response(status=204))
    try:
        data = request.get_json(silent=True) or {}
        message = data.get("response")
        if not isinstance(message, str) or not message:
            return jsonify({"message": "Invalid payload: expected { response: string }"}), 400
        db = client[db_name]
        col = db["responses"]
        doc = {"message": message, "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        res = col.insert_one(doc)
        return jsonify({"message": "Response saved successfully", "id": str(res.inserted_id)})
    except Exception as e:
        return jsonify({"message": "Error saving response", "error": str(e)}), 500


@app.route("/responses", methods=["GET", "OPTIONS"])
def list_responses():
    if request.method == "OPTIONS":
        return cors_headers(Response(status=204))
    try:
        limit = max(1, min(200, int(request.args.get("limit", 50))))
        skip = max(0, int(request.args.get("skip", 0)))
        order = request.args.get("order", "desc").lower()
        sort_dir = ASCENDING if order == "asc" else DESCENDING
        db = client[db_name]
        col = db["responses"]
        cursor = col.find({}).sort("date", sort_dir).skip(skip).limit(limit)
        items = list(cursor)
        for it in items:
            it["_id"] = str(it.get("_id"))
        return jsonify({"count": len(items), "items": items})
    except Exception as e:
        return jsonify({"message": "Error listing responses", "error": str(e)}), 500


@app.route("/v1/chat/completions", methods=["POST", "OPTIONS"])
def proxy_completions():
    if request.method == "OPTIONS":
        return cors_headers(Response(status=204))
    try:
        import requests
        url = f"{UPSTREAM_API_BASE.rstrip('/')}/v1/chat/completions"
        upstream = requests.post(url, json=request.get_json(silent=True) or {}, timeout=120)
        resp = Response(upstream.content, status=upstream.status_code)
        ct = upstream.headers.get("content-type", "application/json")
        resp.headers["content-type"] = ct
        return resp
    except Exception as e:
        return jsonify({"message": "Upstream proxy error", "error": str(e)}), 502


@app.route("/", methods=["GET"])
def root_index():
    try:
        return send_from_directory(os.getcwd(), "index.html")
    except Exception:
        return Response("index.html not found", status=404)


@app.route("/<path:path>", methods=["GET"])
def static_files(path):
    try:
        return send_from_directory(os.getcwd(), path)
    except Exception:
        return Response("Not found", status=404)


def main():
    app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == "__main__":
    main()

