#!/usr/bin/env bash
# DuckEMW / microduck_rl —— AutoDL 实例一次性环境配置
# 用法：rsync 或 git clone 代码后，在实例上执行 bash autodl/setup.sh
# 完成后建议 autodl.py save-image 存私有镜像，后续实例免配置。
set -euo pipefail

REPO_DIR=/root/autodl-tmp/microduck_rl   # 数据盘，关机保留
REPO_GIT=https://github.com/emwstudio/microduck_rl.git

echo "==> 1/5 镜像源与环境变量"
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple || true
cat >> /root/.bashrc <<'EOF'
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf
export UV_HTTP_TIMEOUT=600
export UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
EOF
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/root/autodl-tmp/hf UV_HTTP_TIMEOUT=600

# GitHub 拉取慢时，部分机房有学术加速
if [ -f /etc/network_turbo ]; then
  echo "==> 检测到学术加速，启用"
  source /etc/network_turbo || true
fi

echo "==> 2/5 安装 uv"
if ! command -v uv >/dev/null; then
  pip install -U uv -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

echo "==> 3/5 Python 3.12（老镜像 py38 不够用）"
if ! command -v python3.12 >/dev/null; then
  if command -v conda >/dev/null; then
    conda create -y -n py312 python=3.12
    # uv 会自己管理 venv，这里只是保证有 3.12 解释器可被发现
  else
    uv python install 3.12
  fi
fi

echo "==> 4/5 拉取代码并安装依赖（首次约 2GB CUDA wheel，耐心等）"
mkdir -p /root/autodl-tmp
if [ ! -d "$REPO_DIR/.git" ]; then
  git clone "$REPO_GIT" "$REPO_DIR"
else
  git -C "$REPO_DIR" pull --ff-only || true
fi
cd "$REPO_DIR"
uv sync

echo "==> 5/5 冒烟检查"
uv run list-envs | head -30
nvidia-smi | head -12

echo
echo "完成。训练命令示例："
echo "  cd $REPO_DIR"
echo "  uv run train Mjlab-Velocity-Flat-MicroDuck --env.scene.num-envs 64 --agent.max_iterations 5   # 冒烟"
echo "  uv run train Mjlab-Dance-Flat-MicroDuck --env.scene.num-envs 4096 --agent.max_iterations 4000 # 正式"
echo "用完记得：autodl.py off <uuid>（数据盘保留）；save-image 后下次免配置。"
