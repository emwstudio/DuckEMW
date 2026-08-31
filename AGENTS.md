# DuckEMW 项目原则

1. **永远跟上游保持最新**：`third_party/microduck_rl` 是 `pollen-robotics/microduck_rl` 的 fork（remote: upstream）。每次开工前先同步：
   ```bash
   cd third_party/microduck_rl
   git fetch upstream
   git log --oneline develop..upstream/develop   # 有新提交就 merge/rebase 进我们的 develop
   ```
   我们的改动只在 develop 分支的增量 commit 上（Dance 任务相关），与上游文件尽量保持纯新增，降低合并冲突。
2. **成本纪律**：AutoDL 实例用完立即 `off`；长期不用 `release`（关机仍收磁盘费）；`release` 前确认产物已拉回。训练先冒烟（64 envs × 5 iters）再正式。
3. **验证纪律**：改训练侧代码必须本地 `uv run --with pytest pytest tests/ -q` 全绿；策略效果以 `scripts/dance_to_timeline.py` + `check_beat_align.py` 的部署侧数据为准，不看训练指标下结论。
