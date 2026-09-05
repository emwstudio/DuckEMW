# DuckEMW

教 MicroDuck（约 800 g、25 cm 双足机器人，14 个 XL330 舵机）挑战两件事：**平地极速冲刺** 和 **跟着音乐跳 DJ**——RL 训练的奔跑/舞蹈策略 + 评估/出片管线。

基于 [pollen-robotics/microduck](https://github.com/pollen-robotics/microduck)（机器人本体/runtime）与 [pollen-robotics/microduck_rl](https://github.com/pollen-robotics/microduck_rl)（mjlab/MuJoCo Warp + PPO 训练框架，本仓库以 fork + submodule 方式扩展）。

## 极速项目（2026-09-05，running 策略）

出厂行走基线 **0.4 m/s** → 峰值冲刺 **2.06 m/s**（HUD 实测读数；直立门控瞬时峰值 **2.196 m/s**）。

| 口径 | 本仓库 | 对照 |
|---|---|---|
| 直立瞬时峰值 | **2.196 m/s**（model_13250，512 env 电池取 max，倾斜 <45° 门控） | Max Sumrall 视频遥测峰值 1.88（X 平台公开） |
| 百米均速（10s 窗） | 1.659 m/s | Hannes von Essen 发布版 1.651 / 前沿 1.683 |
| 素材片 | `final_4k_v2.mp4`（4K@50fps，HUD 实时读数冲到 2.06，贴地跟拍） | 参考视频在 `artifacts/references/` |

- **方法**：PPO（rsl_rl）+ mjlab（MuJoCo Warp GPU 并行仿真），512 envs 并行，从零 13,500 轮大训（Hannes 配方 TARGET 2.5 / CAP 2.6）；奖励骨架 = forward_progress 主导 + 腾空相 + 航向保持 + anti-violence 正则（action_rate / 冲击 / 滑移）。
- **关键教训**（详见 `docs/03-training-log.md`）：纪录是「早就破了才发现」——只盯均值/p90 会看不见瞬时峰值，**评估指标决定你能看见什么**；激进续训（weight 8/cap 3.0）反而把均值打回 1.48；同 seed 渲染存在 2.06–2.20 的混沌漂移（warp GPU 非比特确定），属正常。
- 冲刺任务 `Mjlab-Sprint-Flat-MicroDuck`（徒脚极速）、评估 `eval_sprint_speed.py`、出片 `sprint_show.py` 均在 submodule `develop` 分支；纪录大训复现自 [Vottivott/microduck-playground](https://github.com/Vottivott/microduck-playground)（Hannes 的 running 配方）。

## 舞蹈项目（2026-08-31，v10s 策略）

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
│   └── 新增 Mjlab-Sprint-Flat-MicroDuck / Mjlab-Dance-Flat-MicroDuck 任务、
│       eval_sprint_speed.py（速度电池+直立峰值口径）、sprint_show.py、stage_show.py
├── dance/
│   ├── beats.py               # librosa 节拍/BPM 提取 → beats.json
│   ├── timeline.py            # 节拍 → 编舞时间线（支持 --map 显式编舞）
│   └── songs/                 # beats/timeline（音频因版权不入库）
├── autodl/setup.sh            # AutoDL 实例一键环境配置
├── docs/                      # playbook 提炼、设计笔记、训练日志（舞蹈 v1-v11 + 极速全程）
└── AGENTS.md                  # 项目铁律（上游同步/修改必重训/成本纪律/验证纪律）
```

## 任务设计要点

- **观测契约**：与官方完全一致（61 维 = 48 本体感觉 + 13 命令块），全策略家族热插拔。舞蹈任务把 body_pose 槽语义重载为 `[sin(φ/2), cos(φ/2), tempo, 3-bit 舞步 id]`（2 拍周期相位编码——每拍回绕会让 2 拍周期的摇摆不可观测，这是 v3 踩坑后的关键修复）
- **冲刺**：速度命令课程（command-speed curriculum）+ 50% 初速出生 + 短回合爆发；直立门控瞬时峰值口径防止「摔倒前扑」刷假纪录
- **舞蹈**：参考跟踪（高斯**乘积**复合，塌掉静止妥协盆地）+ 节拍同步（potential-based shaping）+ 官方正则；幅度课程 35%→100% 爬坡；舞步库 0 squat_bounce / 1 weight_shift / 2 head_bob / 3 climax / 4 call_out

## 快速开始

```bash
# 1. 克隆（含 submodule）
git clone --recurse-submodules https://github.com/emwstudio/DuckEMW
cd DuckEMW/third_party/microduck_rl && uv sync
uv run --with pytest pytest tests/ -q          # CPU 测试全绿

# 2. 冲刺训练（AutoDL 4090D，一键环境见 autodl/setup.sh）
uv run train Mjlab-Sprint-Flat-MicroDuck --env.scene.num-envs 64 --agent.max_iterations 5   # 冒烟
uv run train Mjlab-Sprint-Flat-MicroDuck --env.scene.num-envs 4096 --agent.max_iterations 2000

# 3. 速度评估（512 env 电池：均值/p90/直立瞬时峰值）
uv run scripts/eval_sprint_speed.py --checkpoint <model.pt> --vx 2.2 --num-envs 512

# 4. 舞蹈训练与验证（节拍条件化策略 + 歌曲编舞 + 本地 CPU MuJoCo 彩排）
uv run train Mjlab-Dance-Flat-MicroDuck --env.scene.num-envs 4096 --agent.max_iterations 1000
uv run dance/beats.py dance/songs/<歌>.wav
uv run scripts/export.py Mjlab-Dance-Flat-MicroDuck --checkpoint-file <model.pt>
uv run python scripts/dance_to_timeline.py --policy dance.onnx \
    --timeline ../../dance/songs/<歌>.timeline.json --record out.mp4 --save-csv out.csv

# 5. 出片（冲刺跟拍 / 舞台 N 鸭齐舞）
uv run python scripts/sprint_show.py --policy sprint.onnx   # 成片输出到 artifacts/sprint_show/
uv run python scripts/stage_show.py --policy dance.onnx \
    --timeline ../../dance/songs/<歌>.timeline.json \
    --ducks 12 --formation army --camera cinematic --record show.mp4 --width 1920 --height 1080
```

## 成本实录（AutoDL 4090D ¥1.88/h）

- 极速项目：基线测量 + 4 轮配方迭代 + 13.5k 轮大训 + 评估/出片，约 **¥70**
- 舞蹈项目：11 轮训练 + 环境配置，约 **¥35**；单轮快训（1000 步）约 ¥1、正式（4000 步）约 ¥4

详见 `docs/03-training-log.md`（两项目全程逐轮记录）。`artifacts/`（checkpoint、ONNX、评估 JSON、成片）体积大不入库。

## 致谢

- [pollen-robotics/microduck](https://github.com/pollen-robotics/microduck) 与 [microduck_rl](https://github.com/pollen-robotics/microduck_rl)——机器人、训练框架与 sim2real 配方（其 AGENTS.md 是本项目的奖励设计圣经）
- [Vottivott/microduck-playground](https://github.com/Vottivott/microduck-playground)（Hannes von Essen）——running 极速配方与评估电池口径
- [mjlab](https://github.com/mujocolab/mjlab)、[BAM](https://github.com/Rhoban/bam)

License: 代码 Apache 2.0（遵循上游）；3D 模型文件 CC BY-SA-NC（上游资产）。
