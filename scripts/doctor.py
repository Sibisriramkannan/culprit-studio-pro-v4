import os,shutil,sys,requests
print("Python:",sys.version.split()[0])
print("FFmpeg:","OK" if shutil.which("ffmpeg") else "MISSING")
for x in ["GEMINI_API_KEY","HUGGINGFACE_API_KEY","NVIDIA_API_KEY","PIXVERSE_API_KEY","MINIMAX_API_KEY","HF_TOKEN","HF_REPO_ID"]:
    print(x, "OK" if os.getenv(x) else "MISSING")
try: print("Local API health:",requests.get("http://127.0.0.1:8000/api/health",timeout=2).json())
except: print("Local API health: server not running (normal if doctor was run before uvicorn)")
