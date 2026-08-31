# DuckEMW

教 MicroDuck（约 800 g、25 cm 双足机器人）**跟着音乐跳 DJ**——RL 训练的节拍条件化舞蹈策略 + 歌曲编舞管线 + 多机器人舞台渲染。

基于 [pollen-robotics/microduck](https://github.com/pollen-robotics/microduck)（机器人本体/runtime）与 [pollen-robotics/microduck_rl](https://github.com/pollen-robotics/microduck_rl)（mjlab/MuJoCo Warp + PPO 训练框架，本仓库以 fork + submodule 方式扩展）。

## 成果（2026-08-31，v10s 策略）

| 指标 | 数值 |
|---|---|
| 高潮深蹲振幅 | 45.0 mm（参考 78%） |
| 高潮摆胯振幅 | 27.5°（峰峰） |
| 甩头/点头锤 | ±32° / ±34°（headbang 每正拍砸中） |
| 踩点精度 | 中位偏差 26 ms，91% 在 100 ms 内 |
| 稳定性 | 全曲 + 12 鸭方阵均**零摔倒** |
| 终版视频 | `stage_v10s_army12_cinematic_4k.mp4`（12 鸭阅兵方阵 + 电影运镜，4K 16:9） |

极限探索结论：单通道极限为深蹲 53 mm / 摆胯 ±22°，但 128 BPM 下不可兼得（XL330 舵机扭矩/转速与重心几何的真实约束，已由 BAM 执行器模型在仿真中验证）。

## 仓库结构

```
├── third_party/microduck_rl   # fork（emwstudio/microduck_rl，develop 分支）
│   └── 新增 Mjlab-Dance-Flat-MicroDuck 任务、舞蹈奖励、stage_show.py
├── dance/
│   ├── beats.py               # librosa 节拍/BPM 提取 → beats.json
│   ├── timeline.py            # 节拍 → 编舞时间线（支持 --map 显式编舞）
│   └── songs/                 # beats/timeline（音频因版权不入库）
├── autodl/setup.sh            # AutoDL 实例一键环境配置
├── docs/                      # playbook 提炼、设计笔记、训练日志（v1-v11 全记录）
└── AGENTS.md                  # 项目铁律（上游同步/修改必重训/成本纪律/验证纪律）
```

## 舞蹈任务设计

- **观测契约**：与官方完全一致（61 维 = 48 本体感觉 + 13 命令块），body_pose 槽语义重载为 `[sin(φ/2), cos(φ/2), tempo, 3-bit 舞步 id]`（2 拍周期相位编码——每拍回绕会让 2 拍周期的摇摆不可观测，这是 v3 踩坑后的关键修复）
- **舞步库**（程序化解析参考，按节拍相位生成）：
  0 squat_bounce / 1 weight_shift / 2 head_bob / 3 climax（深蹲+摆胯+点头锤+甩头 combo）/ 4 call_out（呼喊造型+慢摇）
- **奖励**：参考跟踪（高斯**乘积**复合，塌掉静止妥协盆地）+ 节拍同步（potential-based shaping）+ 官方正则；幅度课程 35%→100% 爬坡

## 快速开始

```bash
# 1. 克隆（含 submodule）
git clone --recurse-submodules https://github.com/emwstudio/DuckEMW
cd DuckEMW/third_party/microduck_rl && uv sync
uv run --with pytest pytest tests/ -q          # 189 个 CPU 测试

# 2. 训练（AutoDL 4090D，~¥2/1000 步；一键环境见 autodl/setup.sh）
uv run train Mjlab-Dance-Flat-MicroDuck --env.scene.num-envs 64 --agent.max_iterations 5     # 冒烟
DANCE_AMP_RAMP_STEPS=24000 uv run train Mjlab-Dance-Flat-MicroDuck \
    --env.scene.num-envs 4096 --agent.max_iterations 1000                                     # 快训

# 3. 歌曲编舞
uv run dance/beats.py dance/songs/<歌>.wav
uv run dance/timeline.py dance/songs/<歌>.beats.json --map 0:4,4:2,8:3

# 4. 验证（本地 CPU MuJoCo）
cd third_party/microduck_rl
uv run scripts/export.py Mjlab-Dance-Flat-MicroDuck --checkpoint-file <model.pt>
uv run python scripts/dance_to_timeline.py --policy dance.onnx \
    --timeline ../../dance/songs/<歌>.timeline.json --record out.mp4 --save-csv out.csv
uv run python scripts/check_beat_align.py out.csv --timeline ../../dance/songs/<歌>.timeline.json

# 5. 舞台视频（N 鸭齐舞，本地渲染）
uv run python scripts/stage_show.py --policy dance.onnx \
    --timeline ../../dance/songs/<歌>.timeline.json \
    --ducks 12 --formation army --camera cinematic --record show.mp4 --width 1920 --height 1080
```

## 成本实录（AutoDL 4090D ¥1.88/h）

11 轮训练 + 环境配置，总计约 **¥35**；单轮快训（1000 步）约 ¥1、正式（4000 步）约 ¥4。详见 `docs/03-training-log.md`。

## 致谢

- [pollen-robotics/microduck](https://github.com/pollen-robotics/microduck) 与 [microduck_rl](https://github.com/pollen-robotics/microduck_rl)——机器人、训练框架与 sim2real 配方（其 AGENTS.md 是本项目的奖励设计圣经）
- [mjlab](https://github.com/mujocolab/mjlab)、[BAM](https://github.com/Rhoban/bam)

License: 代码 Apache 2.0（遵循上游）；3D 模型文件 CC BY-SA-NC（上游资产）。
