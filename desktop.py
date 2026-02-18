import threading
import time
import sys
import os
import ctypes

if os.name == "nt":
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.config import SERVER_HOST, SERVER_PORT


def start_server():
    import uvicorn
    from backend.main import app

    uvicorn.run(
        app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="warning",
    )


def wait_for_server(host: str, port: int, timeout: float = 30.0):
    import socket

    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.3)
    return False


def main():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    print("[SpeechLab] Starting server...")
    if not wait_for_server(SERVER_HOST, SERVER_PORT):
        print("[SpeechLab] ERROR: Server failed to start within 30 seconds.")
        sys.exit(1)

    print(f"[SpeechLab] Server running at http://{SERVER_HOST}:{SERVER_PORT}")

    import webview

    window = webview.create_window(
        title="SpeechLab",
        url=f"http://{SERVER_HOST}:{SERVER_PORT}",
        width=1280,
        height=860,
        min_size=(900, 600),
        text_select=True,
    )

    webview.start()

    print("[SpeechLab] Window closed. Shutting down.")
    sys.exit(0)


if __name__ == "__main__":
    main()
