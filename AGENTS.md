# DuckEMW 项目原则

1. **永远跟上游保持最新**：`third_party/microduck_rl` 是 `pollen-robotics/microduck_rl` 的 fork（remote: upstream）。每次开工前先同步：
   ```bash
   cd third_party/microduck_rl
   git fetch upstream
   git log --oneline develop..upstream/develop   # 有新提交就 merge/rebase 进我们的 develop
   ```
   我们的改动只在 develop 分支的增量 commit 上（Dance 任务相关），与上游文件尽量保持纯新增，降低合并冲突。
2. **续训优先**：同配方只加步数时，一律从上次 checkpoint 续训（`--agent.load-checkpoint model_XXX.pt --agent.resume True`），不从零重跑；只有奖励/观测大改才从零。
3. **迭代节奏**：奖励配方实验用 **2000 迭代**快速试（~1h/¥2），配方定了再跑 **4000 迭代**出正式策略（~2h/¥4）。
4. **成本纪律（用户对费用敏感）**：只用 **4090D**（¥1.88/h）；缺货时等待重试或**先问用户**，绝不擅自换更贵规格（如 vGPU/5090）。训练完成后**不自动关机，等用户指示**；用户明确说不用了才 `off`；长期不用经用户确认后 `release`（关机仍收磁盘费）。训练先冒烟（64 envs × 5 iters）再正式。
5. **验证纪律**：改训练侧代码必须本地 `uv run --with pytest pytest tests/ -q` 全绿；策略效果以 `scripts/dance_to_timeline.py` + `check_beat_align.py` 的部署侧数据为准，不看训练指标下结论。
