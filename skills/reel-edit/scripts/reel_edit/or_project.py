"""Build the Open Recorder project for a finished reel.

The project lives in the reel's work folder (<workdir>/<reel title>/), not in the reel's final
folder, so that folder keeps only the reel, its other copies, the cover and assets/. It is
named after the reel and exports straight into the reel's folder.

One "Reel" lane: the finished reel (frozen as media/baseline-<hash>.mp4) split at every cut the AI
made, so a trim keeps the captions, graphics and sound design of that footage. The raw takes
stay in assets/: dragging one in from there brings back footage the AI cut, as filmed.
"""
import json
import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
FPS = 30
# tests point these at a scratch folder, so a trial run never touches real history or settings
REGISTRY = Path(os.environ.get("REEL_EDIT_REGISTRY") or SKILL / "history" / "openrecorder-projects.json")
HISTORY = Path(os.environ.get("REEL_EDIT_HISTORY") or SKILL / "history")
OR_CONFIG = os.environ.get("REEL_EDIT_OR_CONFIG")


def read(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def open_recorder():
    try:
        import open_recorder.core as core
        from open_recorder.core.model import new_id
        from open_recorder.project import store
        from open_recorder.project.scan import to_media
    except ImportError as e:
        raise SystemExit(f"Open Recorder is not importable from this Python ({sys.executable}): {e}.\n"
                         "Install it (pip install -e <open-recorder checkout>) or run with the Python it is in.")
    return core, new_id, store, to_media


def project_folder(work) -> Path:
    """The folder name is also the title on Open Recorder's start screen."""
    from reel_edit.project import load
    work = Path(work).resolve()
    title = Path(load(str(work)).output).stem
    # Match Windows' filename rules without requiring the editor just to resolve a path.
    import re
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', title).strip().rstrip('. ')[:80]
    return work / (name or 'Reel')


def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def migrate_project(work, folder):
    """Copy the last registered project once, keeping its edits and old files intact."""
    if (folder / '.openrecorder' / 'project.json').exists():
        return
    entry = read(REGISTRY, {}).get(str(work), {})
    old = Path(entry.get('project') or work / 'openrecorder')
    if old.resolve() == folder.resolve() or not (old / '.openrecorder' / 'project.json').exists():
        return
    shutil.copytree(old, folder)
    def remap(value):
        if isinstance(value, dict):
            return {remap(k): remap(v) for k, v in value.items()}
        if isinstance(value, list):
            return [remap(v) for v in value]
        if isinstance(value, str):
            for source, target in [(str(old.resolve()), str(folder.resolve())),
                                   (old.resolve().as_posix(), folder.resolve().as_posix())]:
                if value.lower().startswith(source.lower() + ('/' if '/' in source else '\\')) or value.lower() == source.lower():
                    return target + value[len(source):]
        return value
    for path in folder.rglob('*.json'):
        data = read(path)
        if data is not None:
            write(path, remap(data))


def nframes(path) -> int:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=nb_frames,duration", "-of", "json", str(path)], capture_output=True, text=True).stdout
    s = json.loads(out)["streams"][0]
    return int(s.get("nb_frames") or round(float(s["duration"]) * FPS))


def show_on_start_screen(folder: Path, aliases=()) -> None:
    """Put the project at the top of Open Recorder's start screen (its recent list)."""
    try:
        from open_recorder.config import Settings
        cfg = Settings.load(OR_CONFIG)
        obsolete = {str(Path(p).resolve()).lower() for p in aliases}
        cfg.recent = {k: v for k, v in cfg.recent.items() if str(Path(k).resolve()).lower() not in obsolete}
        cfg.recent[str(Path(folder).resolve())] = time.time()
        cfg.save()
    except Exception as e:
        print(f"  (could not add it to Open Recorder's recent list: {e!r})")


def clean_old_review(reel_folder: Path) -> None:
    """The built-in cut reviewer this replaced left "Edit cuts.cmd" and _edit/review/ beside the reel."""
    (reel_folder / "Edit cuts.cmd").unlink(missing_ok=True)
    edit = reel_folder / "_edit"
    if (edit / "review").is_dir():
        shutil.rmtree(edit / "review", ignore_errors=True)
    if edit.is_dir() and not any(edit.iterdir()):
        edit.rmdir()


def prepare(work, fresh=False):
    from reel_edit.project import load
    core, new_id, store, to_media = open_recorder()
    work = Path(work).resolve()
    p = load(str(work))
    output = Path(p.output)
    if not output.exists():
        raise SystemExit("Build and check the reel before preparing it for Open Recorder")
    folder = project_folder(work)
    migrate_project(work, folder)
    files = store.ProjectFiles(folder)
    ai_old, mine = read(folder / "project.ai.json"), read(files.project)
    aliases = [p for p in work.glob('openrecorder*') if (p / '.openrecorder' / 'project.json').exists()]
    previous = read(REGISTRY, {}).get(str(work), {}).get('project')
    if previous and Path(previous).resolve() != folder:
        aliases.append(Path(previous))
    digest = fingerprint(output)
    old_map = read(folder / 'map.json', {})
    old_baseline = Path(old_map.get('baseline') or folder / 'media' / 'baseline.mp4')
    unchanged = old_baseline.is_file() and fingerprint(old_baseline) == digest
    if mine and unchanged and not fresh:
        # Do not regenerate clip IDs or discard user cuts on an unchanged render.
        mine['name'] = output.stem
        if ai_old:
            ai_old['name'] = output.stem
            write(folder / 'project.ai.json', ai_old)
        write(files.project, mine)
        register(work, folder, output, aliases)
        print(f'Open Recorder project reused: {output.stem}')
        return folder
    content = lambda project: {k: v for k, v in project.items() if k != 'name'}
    if mine and not fresh and (not ai_old or content(mine) != content(ai_old)):
        raise SystemExit(f"{files.project} has the user's changes in it and was left as it is.\n"
                         "Learn from it first (--learn after the export), or --prepare --fresh to start again\n"
                         "(their version is kept as project.<time>.json).")
    if mine:
        keep = files.project.with_name(f"project.{time.time_ns()}.json")
        shutil.copy2(files.project, keep)
        print("  their previous project kept as", keep)

    take_map = read(work / "takes.json")
    source_root = Path(take_map["folder"])
    if not source_root.exists():
        source_root = output.parent / "assets"
    sources = {f.stem: f for f in source_root.iterdir() if f.suffix.lower() in (".mov", ".mp4", ".mkv")}
    # in a subfolder: a video loose in the project folder would be listed in the media bin twice
    baseline = folder / "media" / f"baseline-{digest[:16]}.mp4"
    baseline.parent.mkdir(parents=True, exist_ok=True)
    if not baseline.exists():
        shutil.copy2(output, baseline)
    total = nframes(baseline)

    proj = core.Project(name=output.stem, sequence=core.Sequence(aspect="9:16", fps=FPS), export_dir=str(output.parent))
    m = to_media(folder, baseline)
    m.key, m.recording, m.role = str(baseline.resolve()), "", ""
    proj.media[m.key] = m
    lane = core.Lane(id=new_id("lane"), name="Reel", kind="video")
    rows = [r for r in take_map["takes"] if not r.get("dropped")]
    pieces, raw = [], {}
    for n, row in enumerate(rows):
        take = row["take"].split(" #")[0]
        if take not in sources:
            raise SystemExit(f"Missing raw take: {take}")
        a = round(row["start"] * FPS)
        b = round(rows[n + 1]["start"] * FPS) if n + 1 < len(rows) else total
        if b <= a:
            continue
        raw[str(sources[take].resolve()).lower()] = take
        pieces.append({"take": take, "reel_s": a / FPS, "reel_e": b / FPS, "raw_from": row["from"], "raw_to": row["to"]})
        lane.clips.append(core.Clip(id=new_id("clip"), media=m.key, start=a / FPS, src_in=a / FPS, src_out=b / FPS,
                                    transform=core.Transform(fit="cover")))
    proj.lanes = [lane]
    store.save(folder, proj)
    write(folder / "project.ai.json", read(files.project))
    write(folder / "map.json", {"name": output.stem, "work": str(work), "output": str(output), "baseline": m.key,
                                "output_sha256": digest,
                                "lane": lane.id, "pieces": pieces, "raw": raw,
                                "captions": [[t, s, e] for t, s, e in p.captions]})
    clean_old_review(output.parent)
    register(work, folder, output, aliases)
    print(f"Open Recorder project ready: {proj.name}, {len(lane.clips)} pieces")
    print(f"  open it: Open Recorder's start screen, or {work / 'Edit in Open Recorder.cmd'}")
    print(f"  the export lands in {output.parent}")
    return folder


def register(work, folder, output, aliases=()):
    exe = Path(sys.executable)
    pyw = exe.with_name("pythonw.exe")
    launch = work / "Edit in Open Recorder.cmd"
    import open_recorder
    module_root = Path(open_recorder.__file__).resolve().parent.parent
    launch.write_text(f'@echo off\r\nset "PYTHONPATH={module_root};%PYTHONPATH%"\r\n'
                      f'start "" "{pyw if pyw.exists() else exe}" -m open_recorder --open "{folder}"\r\n',
                      encoding="utf-8")
    show_on_start_screen(folder, aliases)
    reg = read(REGISTRY, {})
    reg[str(work)] = {**reg.get(str(work), {}), "project": str(folder), "name": output.stem,
                      "reel": str(output), "prepared": time.strftime("%Y-%m-%d %H:%M")}
    reg[str(work)].setdefault("learned_export", None)
    write(REGISTRY, reg)
