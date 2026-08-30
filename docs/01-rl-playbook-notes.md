# microduck_rl 官方 Playbook 提炼（Dance 任务相关）

来源：`third_party/microduck_rl/AGENTS.md`（commit d424a0c）。只提炼与 Dance 任务直接相关的约束，完整版以 submodule 内原文为准。

## 不可破坏的硬约束

- **观测固定 61 维（actor）**：48 维本体感觉 + 13 维命令块 `[twist(3), head_pose(4), body_pose(6)]`，顺序固定。用不到的命令槽**补零**（保留 obs 项、采样微小范围），绝不删槽位。这是运行时热切换策略的前提，也是 Dance 任务未来上真机的前提。
- **关节布局**：14 个舵机，0–4 左腿（hip_yaw/hip_roll/hip_pitch/knee/ankle），5–8 颈/头（neck_pitch/head_pitch/head_yaw/head_roll），9–13 右腿。非 walk 模型上 passive 关节会交错，**禁止硬编码关节索引**，用 mdp.py 的 `_servo_joint_ids` / `_servo_joint_pos`。
- **无驱动关节一律命名 `passive_*`**；选择器用 `^(?!passive_).*`。
- **执行器是 BAM**（电压控制 XL330 模型）：独立 env cfg 必须注册 `expand_bam_friction_fields` 启动事件；摩擦 DR 要缩放执行器的 `friction_scale`（`dof_frictionloss` 在 BAM 下已清零，随它是无声 no-op）。
- **观测归一化已开启** → 导出必须走 `scripts/export.py`（归一化烘焙进 ONNX），绝不手工转换 checkpoint。
- **策略不带动作滤波**（无 EMA），训练和部署必须一致。
- **域随机化不能跨 reset 累积**（restore-then-apply）。

## 新任务开发流程（官方推荐）

1. 挑最近模板构建：Dance 基于 `make_microduck_velocity*_env_cfg`（DR/观测噪声/延迟自动同步）。不要从 mjlab 裸模板从零搭，否则要自己移植整个 DR + obs-noise + NaN-guard 栈。
2. **训练前先在仿真验证物理假设**：目标/静止姿态必须是稳定平衡（hold ctrl 3s 看倾斜而不只是高度）；目标高度要在仿真里实测，不要跨模型版本搬数值。
3. 配置约定：`ENABLE_*` 开关 + 调好的常量放 cfg 文件顶部；工厂函数 `make_..._env_cfg(play, rough)`；在 `tasks/__init__.py` 注册（含 `_BACKLASH_TASKS`）；独立的 `RslRl...RunnerCfg` 和 `experiment_name`。
4. 写 cfg 测试（CPU）：关节索引解析、奖励权重符号、门控开关。
5. **冒烟测试**：64 envs × 5 iters，能抓住约 95% 的配置错误。长训前必跑。
6. 预期 2–5 轮「奖励 hacking 打地鼠」，正常。

## 奖励设计红线（每条都是踩坑换来的）

- **符号约定**：mjlab-base cost 函数返回 ≥0 → 权重为负；microduck 自否定函数（`*_penalty`/`*_l1` 返回 ≤0）→ 权重为正。**每次训练检查 wandb 里每个 `Episode_Reward/<penalty>` 必须 ≤ 0**。
- RL 优化的是奖励的字面意思：每个没约束住的自由度都会被利用。动作的「定义」要写进硬状态门控，而不是小惩罚。
- **不许有 jackpot**：到达型奖励必须限速/限斜率；跟踪一个 slew 的内部目标。
- 正奖励绝不能在坏状态（摔倒/低位）下被门控获得 → 用 potential-based shaping（付 Δprogress）。
- 正则分两类：motion-blocker（角速度/角动量/姿态 std）对动态任务要压低；smoothness（action_rate/torque_rate）安全但要在技能发现之后（课程从 ~0 引入）。
- 跨 env 抄正则时**比较奖励质量占比，不是权重数值**。
- 跟踪 Gaussian 的 std ≈ 你仍然在乎的误差；收紧前先看误差是否策略可消除（38% 体重的大头走路必然晃，瞬时头部跟踪 std 太紧会把走路税死 → 用 1s EMA 的 L1 只收 DC 偏置）。
- 命令输入如果从不为非零，对应权重永远是死的 → 每个命令槽从 step 0 保持微小非零采样；**零命令行为要显式训练**（`zero_command_prob` 式精确零采样）。

## 课程与训练运维

- 步数 = env steps（`iteration × 24`）。权重调度用 `microduck_mdp.reward_weight`（阶梯函数，把斜坡离散成档位）。
- 通过 manager 改 term cfg（`env.event_manager.get_term_cfg(...)`），写 `env.cfg` 是无声 no-op。
- 预算参考：简单 episodic 技巧 ≈ 1000 iters @4096 envs；步态/重课程恢复类 4000–6000。
- 看训练：mean reward 上升 + episode 长度符合任务预期 + 每个惩罚项 ≤0 + **主任务项确实在涨**（总 reward 可能只靠正则涨）。
- 「失败」时先无头评测实际 checkpoint 再改奖励。报告 rollout 实际表现，不说「能跑了」。

## Dance 任务的推论

- 节拍相位/ tempo / 舞步编号必须塞进现有 13 维命令块（不扩维度），语义文档化。
- 舞蹈是动态任务：body_ang_vel / angular_momentum 类 motion-blocker 正则要比行走任务更低，smoothness 项走课程后引入。
- squat bounce 的 z 目标必须在仿真里实测站立高度后设定，禁止拍脑袋。
- 节拍同步奖励要用 shaping（接近节拍点时付 Δ），避免「停在某个姿态刷分」。
