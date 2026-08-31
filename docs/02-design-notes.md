# 02 - 设计取舍与已知偏差记录

## 节拍相位/BPM 处理

- **BPM 以 beat_times 首尾跨度为准**（`dance/beats.py`），不用 librosa tempo 估计器的输出。合成 120 BPM click 上 tempo 估计器报 117.45，首尾跨度法报 119.96。相位按 `t0 + bpm` 锚定，BPM 差 2.5 会在 32 秒累积 ~0.6s 漂移，必须用准。
- 相位零点 `t0` = 第一个节拍时刻，存于 timeline.json。harness 与训练环境共用同一相位公式：`φ = 2π·(t−t0)·BPM/60`。

## weight_shift 的极值在半拍点（已知，暂不修）

- 训练参考 `roll = B·sin(φ/2)`：整拍过零、半拍达极值。即左右重心最低点和节拍点错开半拍。
- `scripts/check_beat_align.py` 对 weight_shift 段比较的是相邻拍中点。
- 若希望极值砸在整拍上，参考应改成 `−B·cos(φ/2)` —— 需要改训练侧并重训，列为后续迭代项。

## 50Hz 控制对齐

- 训练物理：timestep=0.005 + decimation=4（50Hz）。上游 `scripts/infer_policy.py` 沿用场景 XML 默认 0.002（实际 125Hz 控制），是既有偏差、未动。
- `scripts/dance_to_timeline.py` 显式设 `model.opt.timestep=0.005` 匹配训练。

## 测试基线

- microduck_rl fork 测试：189 passed, 1 skipped（CPU）。
- 关键哨兵：`test_dance_command_matches_training_semantics`（harness 与训练命令映射逐值对齐）、`test_fixture_bpm_is_consistent_with_its_beat_times`（数据质量）。

## 本机 macOS 环境问题（不影响云端）

- `.venv` 的 `.pth` 文件会被某个外部进程反复置 `UF_HIDDEN` 标记，导致 editable 安装失效。`tests/conftest.py` 已把 `src/` 插入 sys.path 让 pytest 免疫；`uv run list-envs`/`train` 等入口若失效，先 `chflags -R nohidden .venv`。
