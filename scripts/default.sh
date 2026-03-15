#!/bin/bash
# 默认活动启动脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLATFORM_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PLATFORM_DIR"

# 设置 Python 路径
export PYTHONPATH="$PLATFORM_DIR/src:$PYTHONPATH"

# 检查依赖
python -c "import pydantic_settings" 2>/dev/null || {
    echo "缺少依赖，正在安装..."
    pip install pydantic-settings pyyaml
}

# 运行默认活动
python -m thera default "$@"
