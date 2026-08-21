from pathlib import Path
from app.config import settings

def upload_folder(folder,path):
    if not settings.HF_TOKEN or not settings.HF_REPO_ID:
        raise RuntimeError("HF_TOKEN/HF_REPO_ID missing")
    from huggingface_hub import HfApi
    HfApi(token=settings.HF_TOKEN).upload_folder(
      folder_path=folder,path_in_repo=path,repo_id=settings.HF_REPO_ID,
      repo_type=settings.HF_REPO_TYPE,commit_message=f"Culprit Studio {path}")
    return f"hf://{settings.HF_REPO_ID}/{path}"
