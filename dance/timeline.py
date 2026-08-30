# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""节拍 → 舞步指令时间线（timeline.json）。

把 beats.json 映射成按段排列的舞步序列：每 8 拍一段，舞步按固定顺序轮换
（后续可改成按段落能量分配）。timeline 是 infer_policy 驱动舞蹈 ONNX 的输入。

舞步库（与 microduck_rl fork 内 Dance 任务的 MOVE 表一一对应，编号不可乱）：
    0 squat_bounce   身体随节拍上下蹲起
    1 weight_shift   左右重心摇摆
    2 head_bob       点头（2× 节拍频率）
    3 step_touch     原地左右踏点步
    4 spin           原地转身

用法：
    uv run dance/timeline.py dance/songs/<name>.beats.json \
        [--moves 0,1,2] [--segment-beats 8] [-o timeline.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MOVE_NAMES = ["squat_bounce", "weight_shift", "head_bob", "step_touch", "spin"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("beats", type=Path, help="beats.json 路径")
    ap.add_argument("--moves", default="0,1,2", help="使用的舞步编号，逗号分隔（默认 0,1,2 温和三件套）")
    ap.add_argument("--segment-beats", type=int, default=8, help="每段几拍换一个舞步（默认 8）")
    ap.add_argument("-o", "--out", type=Path, default=None)
    args = ap.parse_args()

    data = json.loads(args.beats.read_text())
    beat_times: list[float] = data["beat_times"]
    if len(beat_times) < args.segment_beats:
        print("节拍数太少，无法分段", file=sys.stderr)
        return 1

    moves = [int(m) for m in args.moves.split(",")]
    for m in moves:
        if not 0 <= m < len(MOVE_NAMES):
            print(f"未知舞步编号 {m}（合法范围 0–{len(MOVE_NAMES) - 1}）", file=sys.stderr)
            return 1

    segments = []
    n = len(beat_times)
    for seg_idx, start in enumerate(range(0, n, args.segment_beats)):
        end = min(start + args.segment_beats, n - 1)
        move = moves[seg_idx % len(moves)]
        segments.append(
            {
                "move": move,
                "move_name": MOVE_NAMES[move],
                "start_beat": start,
                "end_beat": end,
                "t_start": beat_times[start],
                # 段结束时间 = 下一段第一拍；最后一段用曲长兜底
                "t_end": beat_times[end + 1] if end + 1 < n else data["duration"],
            }
        )

    payload = {
        "name": data["name"],
        "bpm": data["bpm"],
        "beat_times": beat_times,
        "t0": beat_times[0],  # 相位零点：仿真时钟减它即得相位
        "duration": data["duration"],
        "segments": segments,
    }
    out = args.out or args.beats.with_suffix("").with_suffix(".timeline.json")
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"segments={len(segments)}  moves={sorted(set(moves))}  bpm={data['bpm']}")
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
