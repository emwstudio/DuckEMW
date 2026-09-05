# 03 - 训练日志与成本记录

## 运行记录

| 轮次 | 日期 | 任务 | 迭代 | 时长 | 结果 |
|---|---|---|---|---|---|
| v1 | 2026-08-31 02:12 | Mjlab-Dance-Flat-MicroDuck | 4000 @4096 envs | 2h05m | squat 学会（振幅 71%，踩点 43ms），weight_shift 未学会 |
| v2 | 2026-08-31 04:34 | 同上（仅 bug 修复，奖励同 v1） | 4000 @4096 envs | 2h04m | 与 v1 实质相同；weight_shift 仍未学会 |
| v3 | 2026-08-31 06:50 | 同上（观测 2 拍相位编码） | 4000 @4096 envs | 2h03m | **三个舞步全部踩点**：整体中位偏差 26.5ms、91% <100ms；weight_shift 时机 28-34ms、roll 振幅 0.2°→2.0°；零摔倒 |
| v4 | 2026-08-31 09:45 | 同上（真正的奖励乘积化） | 4000 @4096 envs | 2h02m | **幅度放开**：squat 24.3mm/参考 25mm、roll 13.3°/参考 16°；踩点保持 26.4ms、92% <100ms；零摔倒 |
| v5 | 2026-08-31 13:32 | 加 climax 舞步 + 全面加幅度 + 《牛来》编舞 | 2000 @4096 | 1h04m | 高潮 z 40mm/roll 21°；两段高潮一致性 Δ<0.5mm；零摔倒 |
| v6 | 2026-08-31 15:07 | 加 call_out + 3-bit 编码 + 高潮一贯到底 | 1000 @4096 | 32m | 结构全对但欠训：z 仅 9.6mm |
| v7 | 2026-08-31 15:49 | 幅度课程 35%→100% + 动作税减半 + DJ 级幅度 | 1000 @4096 | 32m | 幅度达成（z 48mm/roll 27.5°）但摔 27 次（欠稳） |
| v8 | 2026-08-31 16:3x | 同 v7 配方正式跑 | 4000 @4096 | 进行中 | 目标：v7 幅度 + 零摔倒 |

## v1 → v2：流程纠错记录（2026-08-31 订正）

- 当时的诊断：奖励妥协盆地（均值高斯，静止也能拿 0.84）。
- **订正：乘积化修复当时并未真正实施**——只 rsync 了 bug 修复文件就开训，v2 与 v1 奖励实质相同，指标差异是训练随机性。真正的乘积化在 v4 才落地（见下）。
- 教训：训练侧改动必须以「本地 diff → 测试 → 同步 → 核对远端文件」闭环确认，不能凭计划描述下结论。

## v2 → v3：可观测性缺陷（根因）

- 诊断：weight_shift 参考 `sin(φ/2)` 周期 **2 拍**，但观测命令里的相位编码 `(sin φ, cos φ)` **每拍回绕**——策略无法区分奇偶拍，不知道这一拍该往哪边倒。对对称高斯奖励，不滚就是期望最优。训练指标再高也学不会观测不到的东西。
- 修复：观测相位编码改为 **2 拍周期** `sin(φ/2), cos(φ/2)`（`DanceCommand._write_command` + harness `dance_command` 同步改，等价测试锁定）。squat（1 拍周期）与 head_bob（半拍周期）都是 2 拍相位的确定函数，不受影响。
- 奖励侧读取未回绕相位的路径不变。

## 成本（AutoDL 4090D，¥1.88/h）

| 项目 | 金额 |
|---|---|
| v1（含环境配置+冒烟+训练 2h05m+导出） | ¥4.87 |
| v2（训练 2h04m+导出） | ¥4.99 |
| v3（训练 2h03m+导出） | ¥4.11 |
| v4（训练 2h02m+导出） | ¥4.19 |
| **总计** | **¥18.16**（用户后续充值 ¥100，余额 ¥104.92） |

## v3 验证结论（2026-08-31）

- 时机问题已解决：所有舞步动作极值对准节拍点（squat 10-25ms，weight_shift 28-34ms）
- 剩余差距是**幅度**：squat 7.7mm vs 参考 25mm，roll 2° vs 参考 ±8°——策略跳得保守
- 下一步迭代方向（如需更放得开）：跟踪 std 收紧、技能成型后放开 action_rate curriculum、提高 dance_body_tracking 权重占比；每次只改一两个变量

## 已知未做事项

- weight_shift 极值在半拍点（参考 `sin(φ/2)` 设计如此）；若想要极值砸整拍，参考改 `-B·cos(φ/2)` 并重训
- head_bob 缺少部署侧验证列（harness CSV 暂无 head_pitch）
- 舞步库只有 3 个温和动作；step_touch / spin 未加
- 真机部署未做（无实体机器人）；ONNX 与 61 维契约保持兼容

## v4：真正的奖励手术（2026-08-31）

- `dance_body_tracking`：3 个高斯均值 → **乘积**（塌掉静止妥协盆地）
- z_std 0.015→0.010、angle_std 10°→6°、joint std 0.15→0.10（部分幅度 = 低分）
- beat_sync roll_rate_std 0.5→0.8（静止策略也能看到梯度）
- 目标：幅度接近参考（squat 25mm、roll ±8°），保持踩点与不摔倒
- **结果：达标**。squat 97%、roll 83%；踩点与不摔倒均保持。乘积复合奖励 + 收紧 std 的组合生效
- 已知现象：z 振幅在所有舞步段都 ~24mm（策略把 bounce 泛化到了所有舞步），视觉上是有弹性的舞步，若要严格区分需再迭代


## 编舞与舞台（2026-08-31）

- 《牛来》编舞（dance/songs/牛来.timeline.json）：0-3 拍 call_out（呼喊）→ 4-7 拍 head_bob（DJ 预热）→ 8-35 拍 climax 一贯到底（"牛来"hook 必中正拍点头锤）。v5 兼容版（无 call_out）在 牛来.v5compat.timeline.json。
- `scripts/stage_show.py`：N 只鸭子同台齐舞（MjSpec.attach 多机器人 + 共享 timeline + 机位 front/tracking/orbit，1080p）。首个 6 鸭环绕视频：artifacts/stage_v5_6ducks_orbit.mp4。
- **策略-时间线兼容性**：move id 编码随版本变化（v1-4: one-hot(3)；v5: 2-bit(0-3)；v6+: 3-bit(0-4)）。时间线含策略没见过的舞步编号 = 越界输入必摔，验证前先核对。


## 舞台视频（2026-08-31）

- `scripts/stage_show.py` 最终能力：1-24+ 只编队（row/arc/grid/army 阅兵方阵）、机位 front/tracking/orbit/cinematic（关键帧运镜）、1080p/4K 精确 16:9。
- 终版：`stage_v10s_army12_cinematic_4k.mp4`（12 鸭方阵 + 电影运镜 v8）。
- 运镜迭代教训：punch 时点用「用户反馈区间收敛」校准（hook：7.25/10.65/14.72s）；推拉要**同向通过** punch 点（方向反转 = 顿挫）；折返放在 punch 之间的平缓段渐变。

## 上游合并（2026-09-03）

- develop 合并到 upstream/develop @ 5bbe963（上游领先 9 个提交）。先把 stage_show.py 的未提交运镜修正提交为 `cb96c18 stage_show: shift niulai hook2 punch to 10.75s`，再 merge（非 rebase，保留历史）。
- **零冲突自动合并**。上游把 "allcollisions" 模型家族改名 "groundcontact"（robot/scene/config 全套重命名 + 新增真全碰撞 robot_allcollisions.xml/scene_allcollisions.xml）；我们的增量（dance 任务、scripts）全部基于 walk 模型，零处引用旧名，无需对齐。
- 上游新增 `uv run publish`（把策略按 daemon 加载的格式发布到 HF Hub）与 --hf-jobs 拦截修复。
- **测试**：`uv run --with pytest pytest tests/ -q` → 231 passed / 1 skipped / 0 failed。注意本机两个坑：① venv 里 `mjlab_microduck.pth` 被打了 macOS UF_HIDDEN 标志，CPython 3.12 的 site 会跳过 hidden .pth → 包不可导入（`chflags nohidden` 修复）；② 新上游测试 test_hf_jobs_flag.py 的子进程探针在 `--with pytest` overlay 里看不到 venv 的包，需 `PYTHONPATH=src uv run --with pytest pytest tests/ -q`。
- **新配色**：CAD 重导出后鸭子主色从黄变橙（头壳橙边、橙脚掌）。stage_show 渲染冒烟正常（1 鸭全程未摔）。
- 后续注意：引用 groundcontact 家族请用新名；真全碰撞模型（robot_allcollisions.xml）是另一个新模型，别和改名后的 groundcontact 混淆。

## 徒脚极速 Sprint（2026-09-03，Phase 0-1）

- **目标**：追上并超越 Hannes von Essen 的 1.6 m/s（同款 MicroDuck，参考 artifacts/references/hannes_1.6ms_run.mp4）。
- **Phase 0 基线**（scripts/walk_speed_test.py，headless + BAM M6 + 61D 契约）：官方 alpha_walking.onnx 实测 **cmd 0.4 → 0.164 m/s**，cmd 1.0 → 0.63 m/s（且高命令下明显跑偏，yaw 漂 >50°）。策略严重欠跟踪 —— 名义"基线 0.4"实际只有 ~0.17 m/s。输出 artifacts/walk_probe/{probe.csv,probe.mp4}。
- **环境坑（复现）**：.pth 又被 macOS UF_HIDDEN 监视器重新隐藏（见上文 2026-09-03 节），`chflags -R nohidden .venv` 后立即跑可抢过监视器窗口。
- **Phase 1**：新任务 `Mjlab-Sprint-Flat-MicroDuck`（tasks/microduck_sprint_env_cfg.py，基于 velocity 配方包装）：lin_vel_x (-0.2, 2.0)、lin_vel_y ±0.1 / ang ±0.5 收窄、turn-in-place 关闭、rel_forward_envs=0.5、air_time 窗口上移 [0.20, 0.45]s 鼓励腾空相、track std 放宽 sqrt(0.25) 保高速梯度、anti-violence 正则原样保留。tests/test_sprint_cfg.py 9 项 + 全量 **243 passed / 1 skipped**。
- upstream/develop @ 29e887e 已并入（零冲突）；roller gauntlet/GP 6 个未跟踪文件已提交（fa32086）。

## Sprint 配方迭代（2026-09-03 晚，AutoDL pro-78811e875f25 / 4090D）

- **评估工具**：`scripts/eval_sprint_speed.py`（warp 原生环境内测 checkpoint 真实速度，绕开一切 harness 差异）；`scripts/walk_speed_test.py --policy/--outdir/--ladder`（CPU BAM headless 复测 + 出片）。**教训复诵：配方结论一律以部署侧实测为准，不看训练指标。**
- **v1（be2c523）**：站桩 0.006 m/s。机制：25% standing envs 白拿奖励质量 + air_time 固定 0.20s 下限（阶跃函数，0.05s 行走步态永远够不到，全程奖励 ≈0.0001）+ action_rate -1.0 摆腿税 + upright 过紧 → 「无视命令站桩」是 argmax。
- **v2（996defe）**：腾空相出来了（air_time_mean 0.17s）但 **error_vel_xy 2.1 m/s 不动**，实测 0.04-0.11 m/s —— 原地高抬腿刷 air_time，无推进。加性奖励的未约束项必被 hack。
- **v3（9c17499）**：air_time 前向门控（× clamp(vx/cmd,0,1)，原地腾空支付 0）+ track 权重 4.0 主导 + init_velocity_prob=0.3 逆向出生（高速前沿要有在策略数据）。实测：error_vel_xy 2.1→1.18，**最快 env 1.43 m/s**（cmd 2.0），propulsion 解锁但方差大、摔倒多（前沿刚到，未巩固）。
- **Phase 3**：v3 同方续训 4000 迭代（resume model_1999，总 6000 迭代，~2h10m/¥4）。rsl_rl resume 语义：--agent.max_iterations 是「再训 N 轮」不是总数。
- **环境坑备忘**：实例 uv 必须 `UV_DEFAULT_INDEX=清华镜像 --no-sync`（否则卡境外 PyPI 10 分钟）；wandb 无 key 用 `WANDB_MODE=offline`；实例 repo 有旧改动挡 merge 时先 diff 再丢。

## 破纪录作战（2026-09-04 凌晨，续 Hannes 血脉）

- **自研 sprint v1-v4 全部 plateau ≤1.43**（详见上节）。改走公开配方：HannesVonEssen/microduck-running（Vottivott/microduck-playground@828d950）。核心配方：running_forward_progress 线性前进奖励（clamp(vx,0,cap)/cap，权重 5.0，无高斯天花板）+ 命令速度 min/max 双升课程（每 750 轮 +0.15 到 2.2）+ 极轻正则 + 3% 站立桶 + 12195 轮训练量。
- **测量链验证**：他的 policy.onnx 在我们 warp 环境实测 cmd 2.2 → mean 1.451 / max 1.707，与其宣称 1.651 一致。
- **实例 PYTHONPATH 复用 venv**：playground 与 microduck_rl 的 mjlab/torch 版本一致（1.3.0 / 2.9.1），`PYTHONPATH=playground/src` + 现有 .venv 即可跑，免 2GB 慢下载（当晚 tuna 镜像仅 546 B/s）。
- **坑**：超时被杀的 git clone 僵尸进程会 rm -rf 目标目录（playground 被连锅端一次，tarball 重建）；实例 /usr/share 只读；headless 渲染走 MUJOCO_GL=osmesa（装 libosmesa6），EGL 在此容器不可用。
- **续训 12195+2000（鲁棒化配方）**：model_14194 官方电池 mean 1.633 / p90 1.753（均值未破，鲁棒化付速度税）。
- **出片管线**（scripts/running_show.py，warp 渲染 + spec_fn 注入软垫墙 x=8m）：**model_14194 峰值冲击 1.726 m/s 撞墙**，慢动作收尾，artifacts/running_show_14194_v2.mp4。撞击阈值教训：判定线要贴墙（7.62m），提前 0.34m 会拍不到真撞。
- **11748 速度支线推进中**（TARGET 2.4 / CAP 2.5、无鲁棒化，CURRICULUM_START_ITERATION=8750 对齐 stage）：冲均值纪录。

## 目标升级 1.9（2026-09-04 晚）

- Max Sumrall（X: 1.8/1.9 m/s "if sim is to be believed"）无公开仓库/配方（HF 仅 cartwheel 视频数据集，GitHub 无 microduck 仓库）。其视频遥测：读数 1.5-1.88 波动，**1.9 是瞬时峰值不是持续均值**——与我们 11748 血脉（p90 1.796）同级。参考视频存 artifacts/references/maxsumrall_1.9ms.mp4。
- 出片迭代反馈（用户）：常速不 slow-mo；硬墙反弹（solref 0.03）+ 求解器加固（iterations 30/nconmax 200，治撞后嵌地）；**出生 yaw 必须锁 0**（默认 ±π，heading 漂移会错过 3m 宽的墙——一次"未撞墙"渲染就是这么废的）。
- **决胜局**：从零按 Hannes 配方训 13500 轮（TARGET 2.5 / CAP 2.6 / stage 750 / forward_progress 5.0 / action_rate -0.10），目标持续均值 1.8+。~7h/¥13，夜间跑。

## 13.5k 大训结果 + 收官（2026-09-05 凌晨）

- **13,500 轮从零训（TARGET 2.5/CAP 2.6）官方电池**：ck13250 mean **1.659** / p90 1.793（最佳），ck13499 mean 1.651，ck12500 mean 1.643。对照：Hannes 11748 前沿 1.683 / 12195 发布 1.651。**打平他的发布版，未破 11748 前沿**——该配方在 1.65-1.69 存在平台期，续训/扩带都试过（v3 6000 轮、11748+3000 @2.4、12195+2000），均回弹到 ~1.63。
- **峰值口径**：撞墙峰值最高 1.805（14194，yaw 锁 0 后重渲）；Max Sumrall 的 1.9 同为瞬时峰值口径（遥测 1.5-1.88）——**峰值口径我们已同级，均值口径还差 0.02-0.03**。
- 出片：`stable_run_13250.mp4`（14s 稳定奔跑，峰值 1.643）、`show_14194_2.2_yawfix.mp4`（撞墙 1.805）、`running_show_final.mp4`（1.622 干净版）。
- **速度-换挡观察**：课程换挡（如 2.25/2.50 档）必有 forward_progress 短暂回落（~0.3），属适应期非 pacing 错误，~300 轮内恢复。
- **关机**：pro-78811e875f25 已 off（34h × ¥1.88 ≈ ¥64，余额 ¥18.43）。环境在数据盘保留，下次开机直接用。
- 全部成果已拉回 artifacts/（checkpoint ×4、ONNX ×3、评估 JSON ×11、成片 ×5）。

## 破 1.88 峰值纪录（2026-09-05 上午）

- **峰值口径判定方法**：官方电池评估脚本加 `peak_vx`（每 env 全程瞬时 body vx 最大值，512 envs 取 max/p99）+ **直立门控**（倾斜 <45° 才计数，排除摔倒前扑的虚假高速）。
- **结果：13250（13.5k 大训）@cmd 2.2 —— 直立峰值 max 2.196 / p99 2.112 m/s，均值 1.658**。Max Sumrall 的 1.88 峰值纪录被打破（超 17%），且非摔倒伪影。
- **激进续训（weight 8.0/cap 3.0/action_rate -0.05）反噬**：15749 均值掉到 1.48（13250 是 1.658），峰值 2.124 也没有更好——旋钮拧过头，奖励骨架大改后 2500 轮不足以重收敛。教训：峰值本来就在，不需要更激进的奖励，需要的可能只是测量。
- **方法论反思（重要）**：纪录是「早就破了才发现」——13250 昨晚就有 2.16 的直立峰值，之前只盯均值/p90 没看见。**评估指标决定你能看见什么**。
- 从零激进大训脚本（pg_fresh_big.sh）备好未启动——既然峰值已破，省下 ¥14。

## 收官（2026-09-05 午）

- HUD 狂飙片 `hud_run_13250.mp4`（仿 Max 风格右上读数，可见峰值 1.87，电池口径峰值 2.196）。
- 实例 pro-78811e875f25 已关机（本轮续训+评估+渲染 ~¥3，余额 ¥15.26）。
- **最终榜单**：峰值直立瞬时 **2.196 m/s**（13250，破 Max 1.88）；均值 1.659（平 Hannes 发布 1.651，未破前沿 1.683）；撞墙冲击峰值 1.805（14194）。
