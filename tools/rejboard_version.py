# -*- coding: utf-8 -*-
"""
Re-renders assets/bankai-rejboard.svg with the latest RejBoard release tag.
Run daily by .github/workflows/snake.yml. Needs the standard library and the
`gh` CLI; glyph outlines come from tools/glyph-cache.json.

    GH_TOKEN=... python -I tools/rejboard_version.py assets
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bleach as B  # noqa: E402

REPO = os.environ.get("REJBOARD_REPO", "RejwanShafi25/RejBoard")
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets"

p = subprocess.run(["gh", "api", "repos/%s/releases/latest" % REPO], capture_output=True)
if p.returncode:
    sys.exit(p.stderr.decode()[:400])
tag = json.loads(p.stdout.decode())["tag_name"]
B.rejboard_card(OUT, tag.lstrip("v"))
print("RejBoard card rendered for", tag)
