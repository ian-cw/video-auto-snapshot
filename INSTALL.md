# Install

Copy this folder to your Codex skills directory:

```bash
~/.codex/skills/video-auto-snapshot
```

After that, invoke it with:

```text
$video-auto-snapshot /path/to/video.mp4
```

The skill writes screenshots into `<video-stem>-截图/shots/`, with `result.json` and `contact-sheet.jpg` at the output root.

## Requirements

- Python 3
- FFmpeg
- FFprobe

OpenCV is optional. If it is missing, the skill still runs but falls back to uniform screenshot selection instead of face-aware selection.
