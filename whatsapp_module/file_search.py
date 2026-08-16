import os
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import CONFIG


def get_file_types_for_keyword(keyword: str) -> list:
    """resume->pdf/docx | photo->jpg/png | video->mp4/mkv | else all"""
    k = (keyword or "").lower()
    if any(x in k for x in ["resume", "cv"]):
        return [".pdf", ".doc", ".docx"]
    if any(x in k for x in ["photo", "image", "pic", "picture"]):
        return [".jpg", ".jpeg", ".png", ".webp"]
    if any(x in k for x in ["video", "movie", "clip", "reel"]):
        return [".mp4", ".mkv", ".mov", ".avi"]
    return []


def _is_everything_available() -> bool:
    path = CONFIG["EVERYTHING_PATH"]
    return os.path.exists(path)


def _normalize_result(path: str) -> dict:
    try:
        stat = os.stat(path)
        return {
            "name": os.path.basename(path),
            "path": path,
            "size_kb": round(stat.st_size / 1024, 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "mtime": stat.st_mtime,
        }
    except OSError:
        return {
            "name": os.path.basename(path),
            "path": path,
            "size_kb": 0,
            "modified": "unknown",
            "mtime": 0,
        }


def _search_with_everything(keyword: str, file_types: list) -> list:
    es_path = CONFIG["EVERYTHING_PATH"]
    limit = str(CONFIG["MAX_SEARCH_RESULTS"])

    type_filter = ""
    if file_types:
        type_filter = " (" + " | ".join([f"ext:{ext.lstrip('.')}" for ext in file_types]) + ")"

    query = f"{keyword}{type_filter}"
    cmd = [es_path, "-n", limit, query]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        results = [_normalize_result(p) for p in lines[: CONFIG["MAX_SEARCH_RESULTS"]]]
        return sorted(results, key=lambda x: x.get("mtime", 0), reverse=True)
    except Exception as e:
        print(f"⚠️ Everything search failed: {e}")
        return []


def _scan_one_root(root: str, keyword: str, file_types: list, max_results: int) -> list:
    out = []
    keyword_l = keyword.lower()
    exclude = CONFIG["EXCLUDE_DIR_NAMES"]

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude]
        if len(out) >= max_results:
            break

        for name in filenames:
            if keyword_l not in name.lower():
                continue
            ext = os.path.splitext(name)[1].lower()
            if file_types and ext not in file_types:
                continue
            full = os.path.join(dirpath, name)
            out.append(_normalize_result(full))
            if len(out) >= max_results:
                break
    return out


def _search_with_fallback(keyword: str, file_types: list) -> list:
    max_results = CONFIG["MAX_SEARCH_RESULTS"]
    roots = CONFIG["SEARCH_ROOTS"]
    results = []

    with ThreadPoolExecutor(max_workers=CONFIG["FALLBACK_WORKERS"]) as pool:
        futures = {
            pool.submit(_scan_one_root, r, keyword, file_types, max_results): r
            for r in roots
            if os.path.exists(r)
        }
        for fut in as_completed(futures):
            try:
                results.extend(fut.result())
            except Exception:
                pass
            if len(results) >= max_results:
                break

    # De-dup and sort
    dedup = {}
    for r in results:
        dedup[r["path"]] = r
    uniq = list(dedup.values())
    uniq.sort(key=lambda x: x.get("mtime", 0), reverse=True)
    return uniq[:max_results]


def search_files(keyword: str, file_types: list = None) -> list:
    """Returns [{name, path, size_kb, modified}] sorted by modified date."""
    if not keyword or not keyword.strip():
        return []

    types = [t.lower() for t in (file_types or get_file_types_for_keyword(keyword))]

    if _is_everything_available():
        results = _search_with_everything(keyword, types)
        if results:
            return results

    return _search_with_fallback(keyword, types)
