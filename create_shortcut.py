import os
import sys
import subprocess
import tempfile


def create_shortcut():
    project_root = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable

    vbs_path = os.path.join(project_root, "SpeechLab.vbs")
    vbs_content = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.CurrentDirectory = "{project_root}"\n'
        f'WshShell.Run """" & "{python_exe}" & """ desktop.py", 0, False\n'
    )

    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)

    print(f"[OK] VBS launcher created: {vbs_path}")
    print(f"[OK] Python path embedded: {python_exe}")

    try:
        desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
        shortcut_path = os.path.join(desktop, "SpeechLab.lnk")

        icon_path = os.path.join(project_root, "assets", "icon.ico")

        ps_content = (
            '$WshShell = New-Object -ComObject WScript.Shell\n'
            f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")\n'
            f'$Shortcut.TargetPath = "wscript.exe"\n'
            f'$Shortcut.Arguments = \'"{vbs_path}"\'\n'
            f'$Shortcut.WorkingDirectory = "{project_root}"\n'
            '$Shortcut.Description = "SpeechLab - Offline Speech Analysis"\n'
            f'$Shortcut.IconLocation = "{icon_path}"\n'
            '$Shortcut.Save()\n'
        )

        tmp_ps1 = os.path.join(tempfile.gettempdir(), "create_speechlab_shortcut.ps1")
        with open(tmp_ps1, "w", encoding="utf-8") as f:
            f.write(ps_content)

        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", tmp_ps1],
            capture_output=True, text=True
        )

        if os.path.exists(tmp_ps1):
            os.unlink(tmp_ps1)

        if result.returncode != 0 and result.stderr.strip():
            print(f"[DEBUG] PowerShell: {result.stderr.strip()}")

        if os.path.exists(shortcut_path):
            print(f"[SUCCESS] Desktop shortcut created: {shortcut_path}")
            print("\nYou can now launch the app by:")
            print("  1. Double-clicking 'SpeechLab' on your desktop")
            print(f"  2. Double-clicking SpeechLab.vbs in {project_root}")
        else:
            print("[WARNING] Shortcut file was not found after creation.")
            print(f"You can still launch by double-clicking: {vbs_path}")

    except Exception as e:
        print(f"[ERROR] Shortcut creation failed: {e}")
        print(f"You can still launch by double-clicking: {vbs_path}")


if __name__ == "__main__":
    create_shortcut()
