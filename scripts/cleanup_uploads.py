"""
Cleanup script for orphaned uploads.

Usage:
    python scripts/cleanup_uploads.py           # dry run
    python scripts/cleanup_uploads.py --apply   # delete orphans
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.server import create_app
from src.models.profile import Profile
from src.models.article import Article

UPLOAD_PREFIX = "/static/uploads/"
UPLOAD_DIR = PROJECT_ROOT / "static" / "uploads"
ARTICLE_UPLOAD_REGEX = re.compile(r"/static/uploads/([A-Za-z0-9_.-]+)")


def gather_referenced_files() -> set[str]:
    referenced: set[str] = set()

    profile = Profile.objects.first()
    if profile and profile.image_url and profile.image_url.startswith(UPLOAD_PREFIX):
        referenced.add(profile.image_url.replace(UPLOAD_PREFIX, ""))

    for article in Article.objects.only("content"):
        if not article.content:
            continue
        for match in ARTICLE_UPLOAD_REGEX.findall(article.content):
            referenced.add(match)

    return referenced


def main() -> int:
    apply = "--apply" in sys.argv
    app = create_app()
    with app.app_context():
        referenced = gather_referenced_files()

    if not UPLOAD_DIR.exists():
        print("Upload directory not found.")
        return 0

    all_files = {p.name for p in UPLOAD_DIR.iterdir() if p.is_file()}
    orphans = sorted(all_files - referenced)

    print(f"Referenced files: {len(referenced)}")
    print(f"Total files: {len(all_files)}")
    print(f"Orphans: {len(orphans)}")
    if orphans:
        for name in orphans:
            print(f" - {name}")

    if apply and orphans:
        for name in orphans:
            try:
                (UPLOAD_DIR / name).unlink()
            except OSError as exc:
                print(f"Failed to delete {name}: {exc}")
        print("Orphan cleanup complete.")
    elif apply:
        print("No orphans to delete.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
