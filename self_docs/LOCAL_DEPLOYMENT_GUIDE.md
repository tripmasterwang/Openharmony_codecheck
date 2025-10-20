# 本地部署指南

## 📋 概述

所有配置现在都可以存储在项目目录中，方便部署到其他服务器，无需依赖 `~/.config/` 目录。

## 📂 配置文件位置

### 项目本地配置（推荐用于部署）

```
config/local/
├── .env                    # API Keys 和环境变量
└── model_registry.json     # 模型价格配置
```

### 系统全局配置（默认）

```
~/.config/mini-swe-agent/
├── .env
└── model_registry.json
```

## 🚀 使用方法

### 方法 1：使用启动脚本（推荐）

使用项目提供的 `run_local.sh` 脚本：

```bash
# Single 模式
./run_local.sh openharmony-single \
    --model openai/deepseek-v3.2-exp \
    -i 0

# Batch 模式
./run_local.sh openharmony-batch \
    --subset dataset1 \
    --split test \
    --model openai/deepseek-v3.2-exp \
    -i openharmony__vendor_telink-0:10 \
    -w 3

# Full 模式
./run_local.sh openharmony \
    --subset dataset1 \
    --split test \
    --model openai/deepseek-v3.2-exp \
    -w 5
```

**优点**：
- ✅ 自动使用项目本地配置
- ✅ 无需手动设置环境变量
- ✅ 便于部署和分享

### 方法 2：手动设置环境变量

```bash
export MSWEA_GLOBAL_CONFIG_DIR="$(pwd)/config/local"
export LITELLM_MODEL_REGISTRY_PATH="$(pwd)/config/local/model_registry.json"

# 然后正常使用命令
mini-extra openharmony-single --model openai/deepseek-v3.2-exp -i 0
```

### 方法 3：使用默认全局配置

如果不设置环境变量，系统会使用 `~/.config/mini-swe-agent/` 中的配置（默认行为）。

## 📦 部署到其他服务器

### 1. 打包项目

```bash
# 打包整个项目（包含配置）
tar -czf mini-swe-agent-deployment.tar.gz \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='dataset1/openharmony/test_result' \
    --exclude='openharmony_*_results_*' \
    .
```

### 2. 在新服务器上解压

```bash
# 解压
tar -xzf mini-swe-agent-deployment.tar.gz -C /path/to/deployment

cd /path/to/deployment
```

### 3. 安装依赖

```bash
pip install -e .
```

### 4. 配置 API Keys（如果需要）

编辑 `config/local/.env`，更新你的 API Keys：

```bash
nano config/local/.env
```

### 5. 使用启动脚本运行

```bash
./run_local.sh openharmony --model openai/deepseek-v3.2-exp -w 5
```

## 🔧 配置文件说明

### config/local/.env

包含所有 API Keys 和环境变量：

```bash
# API Keys
ANTHROPIC_API_KEY=your-claude-key
OPENAI_API_KEY=your-deepseek-key
OPENAI_API_BASE=https://api.modelarts-maas.com/v1

# 路径配置（使用相对路径）
LITELLM_MODEL_REGISTRY_PATH=config/local/model_registry.json
MSWEA_GLOBAL_CONFIG_DIR=config/local

# 默认模型（可选）
MSWEA_MODEL_NAME=openai/deepseek-v3.2-exp
```

### config/local/model_registry.json

包含自定义模型的价格信息：

```json
{
  "openai/deepseek-v3.2-exp": {
    "max_tokens": 8192,
    "max_input_tokens": 64000,
    "max_output_tokens": 8192,
    "input_cost_per_token": 1.142857142857143e-07,
    "output_cost_per_token": 1.7142857142857143e-07,
    "litellm_provider": "openai",
    "mode": "chat"
  }
}
```

## 🔄 优先级说明

配置加载优先级（从高到低）：

1. **环境变量** - `MSWEA_GLOBAL_CONFIG_DIR` 
2. **项目本地配置** - `config/local/` （使用 run_local.sh 时）
3. **系统全局配置** - `~/.config/mini-swe-agent/` （默认）

## 📝 使用示例

### 完整的部署和运行流程

```bash
# 1. 克隆或复制项目到新服务器
git clone <your-repo> /opt/mini-swe-agent
cd /opt/mini-swe-agent

# 2. 安装依赖
pip install -e .

# 3. 检查配置文件
ls -la config/local/
cat config/local/.env

# 4. 更新 API Keys（如果需要）
nano config/local/.env

# 5. 使用本地配置运行
./run_local.sh openharmony \
    --subset dataset1 \
    --split test \
    --model openai/deepseek-v3.2-exp \
    -w 5

# 完成！
```

## ⚙️ 环境变量参考

| 变量名 | 作用 | 默认值 |
|--------|------|--------|
| `MSWEA_GLOBAL_CONFIG_DIR` | 配置目录 | `~/.config/mini-swe-agent` |
| `LITELLM_MODEL_REGISTRY_PATH` | 模型价格配置 | 从 .env 读取 |
| `ANTHROPIC_API_KEY` | Claude API Key | - |
| `OPENAI_API_KEY` | OpenAI/DeepSeek API Key | - |
| `OPENAI_API_BASE` | OpenAI API Base URL | `https://api.openai.com/v1` |
| `MSWEA_MODEL_NAME` | 默认模型 | 命令行指定 |

## 🎯 最佳实践

### 开发环境

使用全局配置（~/.config/）：
```bash
mini-extra openharmony-single -i 0
```

### 生产/部署环境

使用本地配置（项目目录）：
```bash
./run_local.sh openharmony-single -i 0
```

### CI/CD 环境

设置环境变量：
```bash
export MSWEA_GLOBAL_CONFIG_DIR=/app/config
export ANTHROPIC_API_KEY=$CI_ANTHROPIC_KEY
export OPENAI_API_KEY=$CI_OPENAI_KEY

mini-extra openharmony ...
```

## 🔒 安全提示

⚠️  **API Keys 是敏感信息！**

1. **不要提交到 Git**：
   ```bash
   echo "config/local/.env" >> .gitignore
   ```

2. **使用示例文件**：
   ```bash
   cp config/local/.env config/local/.env.example
   # 在 .env.example 中移除真实的 API Keys
   ```

3. **使用环境变量（CI/CD）**：
   ```bash
   # 在 CI/CD 中设置 secrets，不写在配置文件中
   ```

## 📚 相关文档

- **模型配置指南**：`MODEL_SELECTION_GUIDE.md`
- **自定义模型配置**：`CUSTOM_MODEL_GUIDE.md`
- **快速参考**：`QUICK_REFERENCE.md`

## ✅ 验证配置

检查是否使用本地配置：

```bash
# 方法 1: 使用启动脚本
./run_local.sh openharmony-single --help
# 应该显示: Loading global config from '.../config/local/.env'

# 方法 2: 手动设置环境变量
export MSWEA_GLOBAL_CONFIG_DIR="$(pwd)/config/local"
mini-extra openharmony-single --help
```

---

**现在项目可以完全独立部署，不依赖用户目录！** 🎉

