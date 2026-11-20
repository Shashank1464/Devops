import subprocess
import sys
import os

if __name__ == "__main__":
    # Get workspace root directory
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(workspace_dir)

    # Load environment variables from .env file if it exists
    env_path = os.path.join(workspace_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("'\"")

    # Path to virtual env python interpreter
    if sys.platform == "win32":
        venv_python = os.path.join(workspace_dir, "venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(workspace_dir, "venv", "bin", "python")

    # Fallback to system python if venv is missing
    if not os.path.exists(venv_python):
        print("[WARNING] Virtual environment not found at 'venv/'. Attempting system python...")
        venv_python = sys.executable

    print("\n" + "="*60)
    print("                 DEEPSHIELD FORENSIC SUITE")
    print("="*60)
    print(" Launching local dashboard server...")
    print(" Access the application here: http://localhost:8000")
    print(" Press Ctrl+C to terminate the server.")
    print("="*60 + "\n")

    try:
        # Launch Uvicorn server
        subprocess.run([venv_python, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"])
    except KeyboardInterrupt:
        print("\n[INFO] DeepShield server stopped safely.")
    except Exception as e:
        print(f"\n[ERROR] Failed to start server: {e}")
