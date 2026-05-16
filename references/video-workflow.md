# Video Sampling Workflow

## Input

- Prefer a local absolute video path.
- If the user uploads a file, treat it as the video source.
- If no output directory is provided, create `<video-stem>-截图/`.

## Sampling Policy

- Probe the full duration first.
- Select 10 target timestamps spaced evenly across the usable duration.
- Avoid the extreme beginning and ending edges unless the user asks for them.

## Frame Selection

- For each target timestamp, inspect a small window around the target.
- Sample multiple offsets inside the window, not just the exact timestamp.
- Prefer a frame with a visible person or face.
- If no person is detected, use the clearest non-black frame closest to the target.
- If detection fails entirely, still return the nearest usable frame.

## Output

- Export 10 images into `shots/`.
- Report the chosen timestamp for each image.
- Note whether the selected frame was chosen because of person detection or fallback logic.
- Write `result.json` at the output root.
- Write `contact-sheet.jpg` at the output root.
