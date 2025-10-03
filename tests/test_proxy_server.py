import threading
import time
from wsgiref.simple_server import make_server
import requests


from scripts import proxy_btm_server


def _start_server_in_thread(host="127.0.0.1", port=5180):
    server = make_server(host, port, proxy_btm_server.app)

    def serve():
        server.serve_forever()

    t = threading.Thread(target=serve, daemon=True)
    t.start()
    # give server a moment to start
    time.sleep(0.2)
    return server


def test_proxy_serves_index(tmp_path):
    server = _start_server_in_thread(port=5180)
    try:
        url = "http://127.0.0.1:5180/btm_workout"
        r = requests.get(url, timeout=5)
        assert r.status_code == 200
        assert '<div id="root"' in r.text or "<title>BTM Workout" in r.text
    finally:
        server.shutdown()
