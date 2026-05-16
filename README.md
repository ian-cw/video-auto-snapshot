# Video Auto Snapshot / 视频自动截图

[![skills.sh](https://skills.sh/b/ian-cw/video-auto-snapshot)](https://skills.sh/ian-cw/video-auto-snapshot)

[English](#english) | [中文](#中文)

## English

Sample a local video, read its duration, and export 10 evenly spaced screenshots.
Prefer frames with people or faces when available.

This repo is designed to be usable by compatible agents and skill runners:

- accept a local path or uploaded video
- probe duration
- sample 10 evenly spaced frames
- prefer a person or face when available
- write screenshots into a dedicated output folder

### Install

Install from `skills.sh` if your agent supports it:

```bash
npx skills add ian-cw/video-auto-snapshot
```

Or clone/copy this repository into the skills directory used by your agent runtime.

### Use

```text
$video-auto-snapshot /path/to/video.mp4
```

### Requirements

- Python 3
- FFmpeg
- FFprobe
- Optional: OpenCV for person-prioritized frame selection

If you do not pass an output directory, the skill creates:

```text
<video-stem>-截图/
  shots/
  result.json
  contact-sheet.jpg
```

### Example

The contact sheet below was generated from `周处除三害.mp4`.

![周处除三害 contact sheet](examples/zhou-chu-chu-san-hai/contact-sheet.jpg)

Selected frames:

![shot 1](examples/zhou-chu-chu-san-hai/shot-01.jpg)
![shot 2](examples/zhou-chu-chu-san-hai/shot-02.jpg)
![shot 3](examples/zhou-chu-chu-san-hai/shot-03.jpg)
![shot 4](examples/zhou-chu-chu-san-hai/shot-04.jpg)

### Contents

- `SKILL.md`: skill instructions
- `agents/openai.yaml`: UI metadata
- `scripts/video-auto-snapshot`: one-line CLI entry
- `scripts/video_auto_snapshot.py`: main implementation
- `references/video-workflow.md`: sampling policy
- `INSTALL.md`: minimal install note

---

## 中文

用于处理本地视频：读取时长，按均匀间隔导出 10 张截图，并在可用时优先选择有人像或人脸的画面。

这个仓库面向兼容的 agent 和 skill runner：

- 传入本地路径或上传视频
- 先探测时长
- 均匀采样 10 帧
- 优先有人像/人脸的帧
- 把截图写到独立输出目录

### 安装

如果你的 agent 支持 `skills.sh`，可以直接安装：

```bash
npx skills add ian-cw/video-auto-snapshot
```

或者把这个仓库克隆/复制到你所用 agent 的 skills 目录。

### 使用

```text
$video-auto-snapshot /path/to/video.mp4
```

### 依赖

- Python 3
- FFmpeg
- FFprobe
- 可选：OpenCV，用于有人像优先的帧选择

如果不传输出目录，会自动创建：

```text
<视频名>-截图/
  shots/
  result.json
  contact-sheet.jpg
```

### 示例

下面的 contact sheet 来自 `周处除三害.mp4`：

![周处除三害 contact sheet](examples/zhou-chu-chu-san-hai/contact-sheet.jpg)

部分截图：

![截图 1](examples/zhou-chu-chu-san-hai/shot-01.jpg)
![截图 2](examples/zhou-chu-chu-san-hai/shot-02.jpg)
![截图 3](examples/zhou-chu-chu-san-hai/shot-03.jpg)
![截图 4](examples/zhou-chu-chu-san-hai/shot-04.jpg)

### 目录内容

- `SKILL.md`：技能说明
- `agents/openai.yaml`：UI 元数据
- `scripts/video-auto-snapshot`：单命令入口
- `scripts/video_auto_snapshot.py`：主实现
- `references/video-workflow.md`：采样规则
- `INSTALL.md`：简短安装说明
