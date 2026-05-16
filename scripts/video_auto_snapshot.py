#!/usr/bin/env python3
"""Sample a local video and export 10 evenly spaced screenshots.

Usage:
  python3 video_auto_snapshot.py /path/to/video.mp4 --output-dir out/

Optional:
  --count 10
  --window-seconds 2.0
  --contact-sheet out/contact-sheet.jpg
  --json out/result.json
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


FFPROBE = shutil.which("ffprobe")
FFMPEG = shutil.which("ffmpeg")


@dataclass
class Shot:
    index: int
    target_seconds: float
    chosen_seconds: float
    image_path: str
    person_detected: bool
    source: str


def die(msg: str) -> None:
    print(f"[error] {msg}", file=sys.stderr)
    raise SystemExit(1)


def install_hint(tool: str) -> str:
    system = platform.system().lower()
    if tool in {"ffmpeg", "ffprobe"}:
        if system == "darwin":
            return "Install with: brew install ffmpeg"
        if system == "linux":
            return "Install with your package manager, for example: sudo apt-get install ffmpeg"
        if system == "windows":
            return "Install FFmpeg and add ffmpeg.exe / ffprobe.exe to PATH"
    if tool == "python3":
        if system == "darwin":
            return "Install with: brew install python"
        if system == "linux":
            return "Install with your package manager, for example: sudo apt-get install python3"
        if system == "windows":
            return "Install Python 3 from python.org and add it to PATH"
    return "Install the missing dependency and ensure it is available on PATH"


def check_required_dependencies() -> None:
    missing = []
    if not shutil.which("python3"):
        missing.append("python3")
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")
    if not shutil.which("ffprobe"):
        missing.append("ffprobe")
    if missing:
        print("[error] Missing required dependency(s): " + ", ".join(missing), file=sys.stderr)
        for tool in missing:
            print(f"[hint] {tool}: {install_hint(tool)}", file=sys.stderr)
        if platform.system().lower() == "darwin":
            print("[hint] macOS shortcut: brew install python ffmpeg", file=sys.stderr)
        elif platform.system().lower() == "linux":
            print("[hint] Linux shortcut: sudo apt-get install python3 ffmpeg", file=sys.stderr)
        elif platform.system().lower() == "windows":
            print("[hint] Windows shortcut: install Python 3 from python.org and check 'Add Python to PATH'.", file=sys.stderr)
            print("[hint] Windows shortcut: install FFmpeg, then add its bin folder to PATH.", file=sys.stderr)
        raise SystemExit(1)


def print_runtime_notes() -> None:
    if not has_cv2():
        print("[info] OpenCV not found; person-prioritized frame selection will fall back to uniform sampling.", file=sys.stderr)


def run(cmd: List[str]) -> str:
    proc = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.stdout.strip()


def get_duration(video_path: Path) -> float:
    if not FFPROBE:
        die("ffprobe not found on PATH")
    out = run([
        FFPROBE,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ])
    try:
        duration = float(out)
    except ValueError as exc:
        raise SystemExit(f"Could not parse duration from ffprobe output: {out!r}") from exc
    if not math.isfinite(duration) or duration <= 0:
        die(f"Invalid duration: {duration}")
    return duration


def has_cv2() -> bool:
    try:
        import cv2  # type: ignore

        return True
    except Exception:
        return False


def detect_person(frame_path: Path) -> bool:
    if not has_cv2():
        return False
    import cv2  # type: ignore

    img = cv2.imread(str(frame_path))
    if img is None:
        return False
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    if not face_cascade_path.exists():
        return False
    face_cascade = cv2.CascadeClassifier(str(face_cascade_path))
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48))
    return len(faces) > 0


def extract_frame(video_path: Path, second: float, output_path: Path) -> None:
    if not FFMPEG:
        die("ffmpeg not found on PATH")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel", "error",
            "-ss", f"{second:.3f}",
            "-i", str(video_path),
            "-frames:v", "1",
            "-q:v", "2",
            str(output_path),
        ],
        check=True,
    )


def frame_score(frame_path: Path) -> tuple[int, int]:
    """Return (not_black_score, size_score)."""
    if not has_cv2():
        return (1, int(frame_path.stat().st_size))
    import cv2  # type: ignore

    img = cv2.imread(str(frame_path))
    if img is None:
        return (0, 0)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    non_black = int((gray > 10).sum())
    return (non_black, int(frame_path.stat().st_size))


def choose_best_candidate(candidates: List[Path]) -> tuple[Path, bool]:
    scored = []
    for p in candidates:
        person = detect_person(p)
        not_black, size_score = frame_score(p)
        scored.append((person, not_black, size_score, p))
    person_hits = [item for item in scored if item[0]]
    if person_hits:
        person_hits.sort(key=lambda t: (t[1], t[2]), reverse=True)
        return person_hits[0][3], True
    scored.sort(key=lambda t: (t[1], t[2]), reverse=True)
    return scored[0][3], False


def sample_positions(duration: float, count: int) -> List[float]:
    # Avoid the extreme edges a little so we don't over-sample title cards or end slates.
    start = duration * 0.04
    end = duration * 0.96
    if count <= 1:
        return [duration / 2]
    step = (end - start) / (count - 1)
    return [start + step * i for i in range(count)]


def make_contact_sheet(images: List[Path], output_path: Path) -> None:
    if not FFMPEG:
        die("ffmpeg not found on PATH")
    # Build a 5x2 contact sheet with the selected images.
    filter_complex = "tile=5x2:margin=8:padding=6:color=white"
    subprocess.run(
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel", "error",
            *sum((["-i", str(img)] for img in images), []),
            "-filter_complex", filter_complex,
            "-frames:v", "1",
            str(output_path),
        ],
        check=True,
    )


def main() -> int:
    check_required_dependencies()
    print_runtime_notes()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", nargs="?", help="Local video path")
    parser.add_argument("--output-dir", help="Directory for extracted frames")
    parser.add_argument("--count", type=int, default=10, help="Number of screenshots to export")
    parser.add_argument("--window-seconds", type=float, default=1.0, help="Candidate window around each target")
    parser.add_argument("--contact-sheet", help="Optional contact sheet output path")
    parser.add_argument("--json", dest="json_path", help="Optional JSON summary output path")
    args = parser.parse_args()

    if not args.video:
        args.video = input("Video path: ").strip()
    video_path = Path(args.video).expanduser().resolve()
    if not video_path.exists():
        die(f"Video not found: {video_path}")
    if args.count <= 0:
        die("--count must be positive")
    if args.window_seconds < 0:
        die("--window-seconds must be non-negative")

    if not args.output_dir:
        args.output_dir = f"{video_path.stem}-截图"

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    shots_dir = output_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    json_path = Path(args.json_path).expanduser().resolve() if args.json_path else output_dir / "result.json"
    contact_sheet_path = (
        Path(args.contact_sheet).expanduser().resolve() if args.contact_sheet else output_dir / "contact-sheet.jpg"
    )

    duration = get_duration(video_path)
    targets = sample_positions(duration, args.count)
    half_window = args.window_seconds / 2.0
    shots: List[Shot] = []
    exported: List[Path] = []

    for i, target in enumerate(targets, start=1):
        candidate_dir = output_dir / f".cand_{i:02d}"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        if half_window > 0:
            offsets = [
                -half_window,
                -half_window * 0.5,
                0.0,
                half_window * 0.5,
                half_window,
            ]
        else:
            offsets = [0.0]
        candidate_paths: List[Path] = []
        for offset in offsets:
            chosen = min(max(target + offset, 0.0), max(duration - 0.001, 0.0))
            candidate_path = candidate_dir / f"{i:02d}_{chosen:.3f}.jpg"
            extract_frame(video_path, chosen, candidate_path)
            candidate_paths.append(candidate_path)
        best, person = choose_best_candidate(candidate_paths)
        final_path = shots_dir / f"shot_{i:02d}_{target:.3f}.jpg"
        shutil.move(str(best), str(final_path))
        for p in candidate_paths:
            if p.exists() and p != final_path:
                try:
                    p.unlink()
                except OSError:
                    pass
        try:
            candidate_dir.rmdir()
        except OSError:
            pass
        chosen_seconds = float(best.stem.split("_")[-1])
        shot = Shot(
            index=i,
            target_seconds=round(target, 3),
            chosen_seconds=round(chosen_seconds, 3),
            image_path=str(final_path),
            person_detected=person,
            source="person" if person else "fallback",
        )
        shots.append(shot)
        exported.append(final_path)

    if exported:
        make_contact_sheet(exported, contact_sheet_path)

    if json_path:
        payload = {
            "video": str(video_path),
            "duration_seconds": round(duration, 3),
            "count": args.count,
            "output_dir": str(output_dir),
            "shots_dir": str(shots_dir),
            "shots": [asdict(s) for s in shots],
        }
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    summary = {
        "video": str(video_path),
        "duration_seconds": round(duration, 3),
        "output_dir": str(output_dir),
        "shots_dir": str(shots_dir),
        "count": args.count,
        "contact_sheet": str(contact_sheet_path),
        "json": str(json_path),
        "shots": [asdict(s) for s in shots],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print()
    print(f"Saved {len(shots)} screenshots to {output_dir}")
    print(f"Screenshots: {shots_dir}")
    print(f"Contact sheet: {contact_sheet_path}")
    print(f"JSON summary: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
