# /// script
# requires-python = ">=3.10"
# dependencies = ["librosa>=0.10", "soundfile>=0.12", "numpy"]
# ///
"""提取歌曲 BPM 与节拍时间戳 → beats.json。

用法：
    uv run dance/beats.py path/to/song.mp3 [-o dance/songs/<name>.beats.json]

输出 JSON：
    name       曲名（取自文件名）
    bpm        全局估计 BPM（已做半速/倍速到 60–180 区间的规整）
    beat_times 每个节拍点的秒数列表
    duration   曲长（秒）

注意：音频文件本身不入库（版权），只提交生成的 beats.json。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def normalize_bpm(bpm: float) -> float:
    """把估计 BPM 规整到 [60, 180]：半速/倍速歧义取人感更自然的档位。"""
    while bpm < 60:
        bpm *= 2
    while bpm > 180:
        bpm /= 2
    return bpm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", type=Path, help="音频文件路径（wav/mp3/flac/ogg）")
    ap.add_argument("-o", "--out", type=Path, default=None, help="输出 beats.json 路径")
    args = ap.parse_args()

    if not args.audio.is_file():
        print(f"找不到音频文件: {args.audio}", file=sys.stderr)
        return 1

    import librosa
    import numpy as np

    y, sr = librosa.load(args.audio, sr=None, mono=True)
    duration = float(len(y) / sr)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    bpm = normalize_bpm(float(np.atleast_1d(tempo)[0]))
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).round(4).tolist()

    name = args.audio.stem
    out = args.out or Path(__file__).parent / "songs" / f"{name}.beats.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": name,
        "bpm": round(bpm, 2),
        "beat_times": beat_times,
        "duration": round(duration, 3),
    }
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"BPM={payload['bpm']}  beats={len(beat_times)}  duration={payload['duration']}s")
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
