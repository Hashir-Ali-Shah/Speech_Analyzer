"""
SpeakBetter Local — Desktop Launcher
Launches the FastAPI server in a background thread and opens a PyWebView window.
The user can double-click this file (or a shortcut to it) to start the app.
"""

import threading
import time
import sys
import os
import ctypes

# ── Hide the console window immediately (Windows only) ──────────
# This lets us use python.exe (not pythonw) so all imports/prints work,
# but the black console window is hidden before the user sees it.
if os.name == "nt":
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE

# ── Ensure stdout/stderr exist (safety net) ─────────────────────
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.config import SERVER_HOST, SERVER_PORT


def start_server():
    """Start the FastAPI server using uvicorn."""
    import uvicorn
    from backend.main import app

    uvicorn.run(
        app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="warning",
    )


def wait_for_server(host: str, port: int, timeout: float = 30.0):
    """Block until the server is accepting connections."""
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
    """Entry point: start server, then open desktop window."""
    # Start FastAPI in a daemon thread (dies when main thread exits)
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait for the server to be ready
    print("[SpeakBetter] Starting server...")
    if not wait_for_server(SERVER_HOST, SERVER_PORT):
        print("[SpeakBetter] ERROR: Server failed to start within 30 seconds.")
        sys.exit(1)

    print(f"[SpeakBetter] Server running at http://{SERVER_HOST}:{SERVER_PORT}")

    # Open the desktop window
    import webview

    window = webview.create_window(
        title="SpeakBetter Local",
        url=f"http://{SERVER_HOST}:{SERVER_PORT}",
        width=1280,
        height=860,
        min_size=(900, 600),
        text_select=True,
    )

    # This blocks until the window is closed
    webview.start()

    print("[SpeakBetter] Window closed. Shutting down.")
    sys.exit(0)


if __name__ == "__main__":
    main()
