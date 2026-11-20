"""Read the user's Open Recorder project back and write down what they changed.

Their clips are mapped back to raw take time (pieces of the frozen reel through map.json, raw
takes they dragged in from assets/ directly) and compared with the AI's cut. What only the
editor can change (reframing, volume, added lanes, B-roll, music, blur) goes into an
"open_recorder" block. Their export becomes the reel: Open Recorder writes "<reel> (2).mp4"
next to the reel, and --learn puts it in the reel's place (the AI's version stays frozen in
the project as media/baseline.mp4).
"""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from reel_edit.or_project import FPS, HISTORY, REGISTRY, open_recorder, project_folder, read, write

EDGE = 1.5 / FPS        # a change this close to an AI cut point counts as moving that edge


def merge(spans):
    out = []
    for a, b in sorted(spans):
        if out and a <= out[-1][1] + 1e-6:
            out[-1][1] = max(b, out[-1][1])
        else:
            out.append([a, b])
    return out


def subtract(a, b):
    out = []
    for s, e in a:
        for x, y in sorted(b):
            if y <= s or x >= e:
                continue
            if x > s:
                out.append([s, min(x, e)])
            s = max(s, y)
        if e - s > 0.5 / FPS:
            out.append([s, e])
    return out


def to_raw(piece, t):
    """Reel time inside a piece -> raw take time (a piece may be retimed, so scale)."""
    span = piece["reel_e"] - piece["reel_s"]
    k = (piece["raw_to"] - piece["raw_from"]) / span if span else 1.0
    return piece["raw_from"] + (t - piece["reel_s"]) * k


def raw_take(proj, m, key):
    """The take a media key is, when it is a raw take file dragged in from assets/."""
    path = (proj.get("media", {}).get(key) or {}).get("path", key)
    return m["raw"].get(str(Path(path).resolve()).lower()) if path else None


def raw_ranges(proj, m):
    """{take: [[from, to], ...]} in raw seconds for every reel or raw-take clip, and the play order."""
    out, order = {}, []
    for lane in proj.get("lanes", []):
        for c in sorted(lane.get("clips", []), key=lambda c: c["start"]):
            key = c.get("media", "")
            if key == m["baseline"]:
                for pc in m["pieces"]:
                    a, b = max(c["src_in"], pc["reel_s"]), min(c["src_out"], pc["reel_e"])
                    if b - a > 0.5 / FPS:
                        out.setdefault(pc["take"], []).append([to_raw(pc, a), to_raw(pc, b)])
                        order.append((c["start"], pc["reel_s"]))
            elif raw_take(proj, m, key):
                out.setdefault(raw_take(proj, m, key), []).append([c["src_in"], c["src_out"]])
    return {k: merge(v) for k, v in out.items()}, order


def extras(ai, his, m):
    out = {}
    if his.get("sequence", {}).get("aspect") != ai.get("sequence", {}).get("aspect"):
        out["aspect"] = {"ai": ai["sequence"].get("aspect"), "his": his["sequence"].get("aspect")}
    box = lambda t: {k: round(t.get(k, 0), 3) for k in ("x", "y", "w", "h")} | {"mask": t.get("mask"), "fit": t.get("fit")}
    base = {"x": 0, "y": 0, "w": 1, "h": 1, "mask": "none", "fit": "cover"}
    known = lambda key: key == m["baseline"] or bool(raw_take(his, m, key))
    for lane in his.get("lanes", []):
        clips = lane.get("clips", [])
        if lane.get("hidden") or lane.get("muted"):
            out.setdefault("lanes_off", []).append({"lane": lane.get("name"), "hidden": lane.get("hidden"), "muted": lane.get("muted")})
        reframed = [round(c["start"], 2) for c in clips if known(c.get("media", "")) and box(c.get("transform", {})) != base]
        if reframed:
            out.setdefault("reframed", []).append({"lane": lane.get("name"), "at": reframed[:10]})
        vols = sorted({round(c.get("volume", 1.0), 2) for c in clips if known(c.get("media", ""))} - {1.0})
        if vols:
            out.setdefault("volume", []).extend(vols)
        added = [c for c in clips if not known(c.get("media", ""))]
        if added:
            names = sorted({Path((his.get("media", {}).get(c.get("media", "")) or {}).get("path", "") or "").name
                            for c in added if c.get("media")} - {""})
            out.setdefault("added", []).append({
                "lane": lane.get("name"), "kind": lane.get("kind"), "new_lane": lane.get("id") != m["lane"],
                "clips": len(added), "secs": round(sum(c["src_out"] - c["src_in"] for c in added), 1),
                "at": [round(c["start"], 2) for c in added][:8], "files": names[:8],
                "boxes": sorted({json.dumps(box(c.get("transform", {})), sort_keys=True) for c in added})[:3]})
    return out


def exports_of(reel: Path) -> list:
    """Exports Open Recorder wrote beside the reel ("<reel> (2).mp4", "(3)"...), oldest first."""
    pat = re.compile(re.escape(reel.stem) + r" \(\d+\)\.mp4$", re.I)
    found = [f for f in reel.parent.glob("*.mp4") if pat.match(f.name)] if reel.parent.exists() else []
    return sorted(found, key=lambda f: f.stat().st_mtime)


def learn(work):
    open_recorder()
    from open_recorder.project.store import ProjectFiles
    entry = read(REGISTRY, {}).get(str(Path(work).resolve()), {})
    folder = Path(entry['project']) if entry.get('project') else project_folder(work)
    m, ai = read(folder / "map.json"), read(folder / "project.ai.json")
    if not m or not ai:
        raise SystemExit("No Open Recorder project was prepared for this reel (run --prepare first)")
    his = read(ProjectFiles(folder).project)
    A, _ = raw_ranges(ai, m)
    H, order = raw_ranges(his, m)
    phrases = []
    for text, s, e in m["captions"]:
        for pc in m["pieces"]:
            a, b = max(s, pc["reel_s"]), min(e, pc["reel_e"])
            if b > a:
                phrases.append((pc["take"], to_raw(pc, a), to_raw(pc, b), text))

    def describe(take, span):
        s, e = span
        whole = any(abs(s - x) < EDGE and abs(e - y) < EDGE for x, y in A.get(take, []))
        bounds = [("head", x) for x, _ in A.get(take, [])] + [("tail", y) for _, y in A.get(take, [])]
        edge = "whole" if whole else next((side for side, t in bounds if min(abs(s - t), abs(e - t)) < EDGE), None)
        words = [t for k, a, b, t in phrases if k == take and min(e, b) - max(s, a) > 0.02]
        return {"take": take, "source_from": round(s, 4), "source_to": round(e, 4), "seconds": round(e - s, 3),
                "edge": edge, "caption_context": words}

    removed = [describe(t, r) for t in A for r in subtract(A[t], H.get(t, []))]
    restored = [describe(t, r) for t in H for r in subtract(H[t], A.get(t, []))]
    reordered = any(b[1] < a[1] for a, b in zip(sorted(order), sorted(order)[1:]))
    ex = extras(ai, his, m)
    reel = Path(m["output"])
    exports = exports_of(reel)
    result = {"name": m["name"], "date": datetime.now(timezone.utc).isoformat(), "learned": False,
              "state": "exported" if exports else "draft", "project": str(folder), "tool": "open-recorder",
              "output": str(reel) if exports else None, "he_cut": removed, "he_restored": restored,
              "reordered": reordered, "open_recorder": ex, "changed": bool(removed or restored or reordered or ex)}
    lines = [f"# What changed in Open Recorder: {m['name']}", f"State: {result['state']}",
             "Source times refer to the original take. Context is caption text, not verified word alignment."]
    for kind, changes in (("REMOVED", removed), ("RESTORED", restored)):
        for c in changes:
            lines.append(f"{kind} {c['take']} {c['source_from']:.3f}-{c['source_to']:.3f}s "
                         f"({c['edge'] or 'internal'}): {' / '.join(c['caption_context'])}")
    if reordered:
        lines.append("REORDERED: pieces play in a different order than the AI's cut")
    lines += [f"OPEN RECORDER {k}: {json.dumps(v, ensure_ascii=False)}" for k, v in ex.items()]
    if not result["changed"]:
        lines.append("The AI cut was accepted unchanged.")
    (folder / "review-diff.txt").write_text("\n".join(lines), encoding="utf-8")
    key = re.sub(r"[^\w-]+", "-", m["name"]).strip("-").lower() + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    write(HISTORY / f"{key}.json", result)
    if exports:
        # their export becomes the reel; the AI's version stays frozen in the project
        os.replace(exports[-1], reel)
        for older in exports[:-1]:
            older.unlink(missing_ok=True)
        print(f"  their export is now {reel.name}")
        youtube = reel.with_name(f"{reel.stem} - YouTube.mp4")
        if youtube.exists():
            print(f"  {youtube.name} is still the AI's cut: rebuild it from the reviewed reel if it should match")
    reg = read(REGISTRY, {})
    entry = reg.setdefault(str(Path(work).resolve()), {"project": str(folder), "name": m["name"]})
    if exports:
        entry["learned_export"] = {"path": str(reel), "mtime": reel.stat().st_mtime}
    write(REGISTRY, reg)
    print(f"{len(removed)} cut, {len(restored)} restored, {len(ex)} other changes -> {HISTORY / (key + '.json')}")
    return result


def pending():
    """Prepared reels with an export waiting beside the reel: [(workdir, export)]."""
    out = []
    for work, entry in read(REGISTRY, {}).items():
        exports = exports_of(Path(entry.get("reel", "")))
        if exports:
            out.append((work, exports[-1]))
    return out
