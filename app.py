# ============================================================
# YAX API - FLASK SERVER (KOYEB EDITION)
# ============================================================
from flask import Flask, request, jsonify
from functools import wraps
from collections import defaultdict
import time, threading, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from garena import AccountGenerator
from config import Config

app = Flask(__name__)

rate_limit_data = defaultdict(list)
rate_lock = threading.Lock()


def check_rate_limit(ip):
    now = time.time()
    with rate_lock:
        rate_limit_data[ip] = [t for t in rate_limit_data[ip] if now - t < 60]
        if len(rate_limit_data[ip]) >= Config.RATE_LIMIT:
            return False
        rate_limit_data[ip].append(now)
    return True


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if not api_key or api_key not in Config.API_KEYS:
            return jsonify({"accounts": [], "success": False, "error": "Invalid API key"}), 401
        ip = request.headers.get("x-forwarded-for", request.remote_addr or "unknown").split(",")[0].strip()
        if not check_rate_limit(ip):
            return jsonify({"accounts": [], "success": False, "error": "Rate limit exceeded"}), 429
        return f(*args, **kwargs)
    return decorated


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "name": "Yax API Generator",
        "version": "2.0.0",
        "status": "online",
        "endpoints": {
            "/api/v2/gen": "Generate accounts (GET)",
            "/api/v2/health": "Health check"
        }
    })


@app.route("/api/v2/health", methods=["GET"])
def health():
    return jsonify({"success": True, "status": "healthy"})


@app.route("/api/v2/gen", methods=["GET"])
def generate():
    try:
        count = int(request.args.get("count", 1))
        region = request.args.get("region", "ID").upper()
        name = request.args.get("name", "User")

        if count < 1 or count > 20:
            return jsonify({
                "accounts": [], "success": False,
                "error": "count must be 1-20",
                "total_created": 0, "total_requested": count, "attempts_made": 0
            }), 400

        if region not in Config.REGION_LANG:
            return jsonify({
                "accounts": [], "success": False,
                "error": f"Invalid region. Available: {list(Config.REGION_LANG.keys())}",
                "total_created": 0, "total_requested": count, "attempts_made": 0
            }), 400

        accounts = []
        attempts_made = 0

        with ThreadPoolExecutor(max_workers=min(count, Config.MAX_WORKERS)) as executor:
            futures = [executor.submit(AccountGenerator.execute_creation, region, name) for _ in range(count)]
            for future in as_completed(futures):
                attempts_made += 1
                try:
                    result = future.result(timeout=60)
                    if result:
                        accounts.append(result)
                except Exception:
                    pass

        return jsonify({
            "accounts": accounts,
            "attempts_made": attempts_made,
            "success": len(accounts) > 0,
            "total_created": len(accounts),
            "total_requested": count
        })
    except Exception as e:
        return jsonify({
            "accounts": [], "success": False, "error": str(e),
            "total_created": 0, "total_requested": 1, "attempts_made": 0
        }), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({"accounts": [], "success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"accounts": [], "success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
