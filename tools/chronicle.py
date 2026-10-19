# -*- coding: utf-8 -*-
"""
Renders assets/chronicle-panel.svg (the "Reiatsu" panel) from live GitHub data
in the same Bleach style as the rest of the profile. Run daily by
.github/workflows/snake.yml so the numbers never go stale. Needs only the
Python standard library and the `gh` CLI; glyph outlines come from
tools/glyph-cache.json, so no fonts have to be installed on the runner.

    GH_TOKEN=... python -I tools/chronicle.py assets/chronicle-panel.svg
"""
import collections
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bleach as B  # noqa: E402

USER = os.environ.get("PROFILE_USER", "RejwanShafi25")
DEST = sys.argv[1] if len(sys.argv) > 1 else "assets/chronicle-panel.svg"
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def gh(args):
    p = subprocess.run(["gh"] + args, capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr.decode()[:400])
    return json.loads(p.stdout.decode() or "{}")


def pretty(d):
    y, m, day = d.split("-")
    return "%d %s %s" % (int(day), MONTHS[int(m) - 1], y)


def contributions():
    q = ("query($login:String!){user(login:$login){contributionsCollection"
         "{contributionCalendar{totalContributions weeks{contributionDays"
         "{date contributionCount}}}}}}")
    d = gh(["api", "graphql", "-f", "query=" + q, "-F", "login=" + USER])
    cal = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [x for w in cal["weeks"] for x in w["contributionDays"]]
    best = max(days, key=lambda x: x["contributionCount"])
    run = longest = 0
    for x in days:
        run = run + 1 if x["contributionCount"] > 0 else 0
        longest = max(longest, run)
    return dict(total=cal["totalContributions"], span=len(days),
                active=sum(1 for x in days if x["contributionCount"] > 0),
                longest=longest, best=best["contributionCount"], best_day=best["date"],
                first=days[0]["date"], last=days[-1]["date"])


def languages():
    repos = gh(["api", "users/%s/repos?per_page=100&type=owner" % USER, "--paginate"])
    agg = collections.Counter()
    for r in repos:
        if r.get("fork"):
            continue
        try:
            agg.update(gh(["api", "repos/%s/%s/languages" % (USER, r["name"])]))
        except RuntimeError:
            continue
    total = sum(agg.values()) or 1
    return [(k, 100.0 * v / total) for k, v in agg.most_common(6)]


def render(c, langs, dest):
    s = B.Svg(1200, 380, "Reiatsu. A year of commits, re-rendered daily from live GitHub data." + (
        " %s contributions, %s active days, longest streak %s days." % (c["total"], c["active"], c["longest"]) if c else
        " Waiting for the first sync."))
    B.base(s, 14, 41)
    B.panel_frame(s, 44, 16, 1112, 348)
    s.text("霊圧", 690, 340, 230, "serif", B.ORANGE, anchor="end", opacity=0.07)
    dash = "--"
    cells = [
        ("TOTAL CONTRIBUTIONS", "{:,}".format(c["total"]) if c else dash, "LAST %d DAYS" % c["span"] if c else "SYNC PENDING"),
        ("ACTIVE DAYS", str(c["active"]) if c else dash, "OF %d" % c["span"] if c else ""),
        ("LONGEST STREAK", str(c["longest"]) if c else dash, "DAYS IN A ROW" if c else ""),
        ("BUSIEST DAY", str(c["best"]) if c else dash, pretty(c["best_day"]) if c else ""),
    ]
    for i, (lab, val, sub) in enumerate(cells):
        x, y = 90 + (i % 2) * 300, 70 + (i // 2) * 134
        s.add('<g class="rise d%d">' % (i + 1))
        s.add('<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="%s"/>' % (x - 14, y, x - 8, y, x - 14, y + 96, x - 20, y + 96, B.ORANGE))
        s.text(lab, x, y + 14, 11, "mono", B.GREY, 2.6)
        s.text(val, x, y + 70, 58, "black", B.BONE, 0.5, skew=7)
        s.text(sub, x, y + 92, 11, "mono", B.ORANGE, 2.2)
        s.add("</g>")
    # languages
    lx = 720
    s.text("LANGUAGES BY VOLUME", lx, 62, 12, "black", B.BONE, 3.4, skew=6, cls="rise d2")
    s.add('<line x1="%d" y1="74" x2="1124" y2="74" stroke="%s" stroke-opacity=".25"/>' % (lx, B.BONE))
    if langs:
        top = langs[0][1] or 1
        for i, (name, pct) in enumerate(langs):
            y = 112 + i * 38
            s.add('<g class="rise d%d">' % (3 + min(i, 4)))
            s.text(name.upper(), lx, y, 13, "bold", B.BONE, 1.2, fit=min(B.measure(name.upper(), "bold", 13, 1.2), 150))
            bw = max(8, 190 * pct / top)
            s.add('<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="%s" fill-opacity=".18"/>' % (lx + 168, y - 14, lx + 168 + 190, y - 14, lx + 168 + 184, y + 2, lx + 162, y + 2, B.BONE))
            s.add('<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="url(#og)"/>' % (lx + 168, y - 14, lx + 168 + bw, y - 14, lx + 168 + bw - 6, y + 2, lx + 162, y + 2))
            s.text("%.1f%%" % pct, 1124, y, 12, "mono", B.GREY, 1, anchor="end")
            s.add("</g>")
    else:
        s.text("FIRST SYNC RUNS WHEN THIS REPO IS PUSHED.", lx, 120, 12.5, "mono", B.GREY, 2)
    foot = "RE-RENDERED DAILY FROM LIVE GITHUB DATA"
    if c:
        foot += "  /  %s - %s" % (pretty(c["first"]), pretty(c["last"]))
    s.text(foot, 90, 346, 10.5, "mono", B.GREY2, 2.6)
    B.write(dest, s.render(extra_defs=B.STD_DEFS))


if __name__ == "__main__":
    if "--placeholder" in sys.argv:
        render(None, None, DEST)
    else:
        render(contributions(), languages(), DEST)
