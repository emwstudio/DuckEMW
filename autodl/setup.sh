#!/usr/bin/env bash
# DuckEMW / microduck_rl —— AutoDL 实例一次性环境配置
# 用法：scp 到实例后执行 bash setup.sh
# 完成后建议 autodl.py save-image 存私有镜像，后续实例免配置。
set -euo pipefail

REPO_DIR=/root/autodl-tmp/microduck_rl   # 数据盘，关机保留
REPO_GIT=https://github.com/emwstudio/microduck_rl.git

# 基础镜像的 conda/python 不在非交互 PATH 里，先补上
export PATH=/root/miniconda3/bin:$PATH

echo "==> 1/5 镜像源与环境变量"
python3 -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple || true
grep -q HF_ENDPOINT /root/.bashrc || cat >> /root/.bashrc <<'EOF'
export PATH=/root/miniconda3/bin:$PATH
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf
export UV_HTTP_TIMEOUT=600
EOF
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/root/autodl-tmp/hf UV_HTTP_TIMEOUT=600

echo "==> 2/5 安装 uv"
if ! command -v uv >/dev/null; then
  python3 -m pip install -q -U uv -i https://pypi.tuna.tsinghua.edu.cn/simple
fi
uv --version

echo "==> 3/5 Python 3.12（uv 自管理，避开老镜像 py38）"
uv python install 3.12

echo "==> 4/5 拉取代码并安装依赖（首次约 2GB CUDA wheel，耐心等）"
mkdir -p /root/autodl-tmp
if [ ! -d "$REPO_DIR/.git" ]; then
  if ! git clone "$REPO_GIT" "$REPO_DIR"; then
    echo "git clone 失败，尝试学术加速后重试"
    [ -f /etc/network_turbo ] && source /etc/network_turbo || true
    git clone "$REPO_GIT" "$REPO_DIR"
  fi
else
  git -C "$REPO_DIR" pull --ff-only || true
fi
cd "$REPO_DIR"
uv sync

echo "==> 5/5 冒烟检查"
uv run list-envs | grep -i dance || uv run list-envs | head -30
nvidia-smi | head -12

echo
echo "完成。训练命令示例："
echo "  cd $REPO_DIR"
echo "  uv run train Mjlab-Dance-Flat-MicroDuck --env.scene.num-envs 64 --agent.max_iterations 5    # 冒烟"
echo "  uv run train Mjlab-Dance-Flat-MicroDuck --env.scene.num-envs 4096 --agent.max_iterations 4000 # 正式"
echo "用完记得：autodl.py off <uuid>（数据盘保留）；save-image 后下次免配置。"
