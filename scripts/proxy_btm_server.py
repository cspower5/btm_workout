#!/usr/bin/env python3
"""
Simple WSGI server to serve the built frontend under /btm_workout and proxy
requests to /api/* to the remote API. This avoids CORS issues for Puppeteer E2E
and provides an SPA fallback (serve index.html for non-api requests).

Usage:
  python scripts/proxy_btm_server.py --host 127.0.0.1 --port 5174

Logs to stdout. Keep this script inside the repo so it can be edited and run
from CI if needed.
"""
import argparse
import logging
import os
from urllib.parse import urljoin

import requests

HERE = os.path.dirname(os.path.dirname(__file__))
DIST_DIR = os.path.join(HERE, "client", "dist")
REMOTE_API = os.environ.get("BTM_REMOTE_API", "https://btm-workout.onrender.com")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("proxy_btm_server")


def read_file_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD")
    path = environ.get("PATH_INFO", "")
    qs = environ.get("QUERY_STRING")
    logger.info("%s %s?%s", method, path, qs)

    # Proxy /api/* to remote API
    if path.startswith("/api/"):
        target = urljoin(REMOTE_API, path)
        if qs:
            target = target + "?" + qs
        try:
            resp = requests.request(
                method,
                target,
                headers=_forward_headers(environ),
                data=_read_body(environ),
                timeout=10,
            )
            status = f"{resp.status_code} {resp.reason}"
            headers = [(k, v) for k, v in resp.headers.items()]
            # Ensure CORS permissive headers so the browser can make requests
            headers.append(("Access-Control-Allow-Origin", "*"))
            headers.append(("Access-Control-Allow-Headers", "Content-Type"))
            start_response(status, headers)
            return [resp.content]
        except Exception as e:
            logger.exception("Proxy request failed")
            status = "502 Bad Gateway"
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, headers)
            return [str(e).encode("utf-8")]

    # Serve static assets from client/dist. If path is /btm_workout or startswith it,
    # strip the prefix and try to serve static file. For SPA routes serve index.html.
    # Try to serve any static file that exists in the dist directory. This
    # handles requests such as /assets/... and /favicon.svg regardless of the
    # URL layout (GitHub Pages emits absolute paths like /btm_workout/assets/...).
    static_rel = path.lstrip("/")
    if static_rel:
        file_path = os.path.join(DIST_DIR, static_rel)
        if os.path.isfile(file_path):
            try:
                data = read_file_bytes(file_path)
                mime = _guess_mime(file_path)
                status = "200 OK"
                headers = [("Content-Type", mime), ("Content-Length", str(len(data)))]
                logger.info("Serving static file %s", file_path)
                start_response(status, headers)
                return [data]
            except Exception:
                logger.exception("Failed to read static file %s", file_path)
                status = "500 Internal Server Error"
                start_response(status, [("Content-Type", "text/plain; charset=utf-8")])
                return [b"Internal Server Error"]

    # If path is under /btm_workout, serve index.html as SPA fallback
    if path == "/btm_workout" or path.startswith("/btm_workout/"):
        index_path = os.path.join(DIST_DIR, "index.html")
        if os.path.isfile(index_path):
            data = read_file_bytes(index_path)
            status = "200 OK"
            headers = [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(data))),
            ]
            logger.info("Serving SPA index for %s", path)
            start_response(status, headers)
            return [data]
        else:
            start_response(
                "404 Not Found", [("Content-Type", "text/plain; charset=utf-8")]
            )
            return [b"Not Found"]

    # Anything else: 404
    start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"Not Found"]


def _forward_headers(environ):
    headers = {}
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            name = key[5:].replace("_", "-").title()
            headers[name] = value
    # Ensure Host header is target host
    return headers


def _read_body(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except Exception:
        length = 0
    if length:
        return environ["wsgi.input"].read(length)
    return None


def _guess_mime(path):
    if path.endswith(".html"):
        return "text/html; charset=utf-8"
    if path.endswith(".js"):
        return "application/javascript"
    if path.endswith(".css"):
        return "text/css"
    if path.endswith(".svg"):
        return "image/svg+xml"
    if path.endswith(".png"):
        return "image/png"
    if path.endswith(".json"):
        return "application/json"
    if path.endswith(".ico"):
        return "image/x-icon"
    return "application/octet-stream"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5174)
    args = parser.parse_args()

    from wsgiref.simple_server import make_server

    logger.info(
        "Serving %s at http://%s:%s/btm_workout", DIST_DIR, args.host, args.port
    )
    with make_server(args.host, args.port, app) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Stopping server")


if __name__ == "__main__":
    main()
