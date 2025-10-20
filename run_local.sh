#!/bin/bash
# Mini-SWE-Agent 本地配置启动脚本
# 使用项目目录下的配置文件，而不是 ~/.config

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 设置环境变量，使用项目本地配置
export MSWEA_GLOBAL_CONFIG_DIR="$SCRIPT_DIR/config/local"

# 设置模型注册文件路径（相对于项目根目录）
export LITELLM_MODEL_REGISTRY_PATH="$SCRIPT_DIR/config/local/model_registry.json"

# 静默启动信息（可选）
# export MSWEA_SILENT_STARTUP=1

echo "📍 使用本地配置"
echo "   配置目录: $MSWEA_GLOBAL_CONFIG_DIR"
echo "   模型注册: $LITELLM_MODEL_REGISTRY_PATH"
echo ""

# 执行 mini-extra 命令，传递所有参数
mini-extra "$@"
