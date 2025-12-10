# Mini-SWE-Agent OpenHarmony 扩展 - 快速开始

## 📦 安装步骤

### 1. 克隆代码

```bash
git clone https://github.com/tripmasterwang/harmocheck.git
cd Openharmony_codecheck
```

### 2. 创建 Python 环境

```bash
# 使用 conda（推荐）
conda create -n harmonycheck python=3.11 -y
conda activate harmonycheck

# 或使用 venv
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装项目依赖

```bash
pip install -e '.[full]'
```

### 4. 配置 API 密钥(这一步的.env文件问wys要)

**方法 1：使用系统全局配置（推荐用于 harmocheck）**

这是最简单的方法，配置一次后可以在任何目录使用 `harmocheck`：

```bash
# 创建配置目录
mkdir -p ~/.config/mini-swe-agent

# 复制模型注册文件
cp config/local/model_registry.json ~/.config/mini-swe-agent/

# 创建 .env 文件（替换 YOUR_PROJECT_PATH 为实际项目路径）
cat > ~/.config/mini-swe-agent/.env << EOF
# Anthropic Claude 模型（可选）
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# DeepSeek 模型（OpenAI 兼容接口，推荐）
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_API_BASE=https://api.modelarts-maas.com/v1

# 模型价格注册文件（使用绝对路径）
LITELLM_MODEL_REGISTRY_PATH=$HOME/.config/mini-swe-agent/model_registry.json

# 全局配置目录
MSWEA_GLOBAL_CONFIG_DIR=$HOME/.config/mini-swe-agent

# 默认模型（可选，设置后无需每次指定 -m 参数）
MSWEA_MODEL_NAME=openai/deepseek-v3.2-exp
EOF

# 编辑文件，填入你的真实 API 密钥
nano ~/.config/mini-swe-agent/.env  # 或使用其他编辑器
```

**必需的 API 密钥：**

- **DeepSeek**（推荐）：需要 `OPENAI_API_KEY` 和 `OPENAI_API_BASE`
  - 获取方式：访问 [DeepSeek 官网](https://www.deepseek.com/) 或使用华为云 ModelArts
- **Anthropic Claude**：需要 `ANTHROPIC_API_KEY`
  - 获取方式：访问 [Anthropic 官网](https://www.anthropic.com/)

**⚠️ 可能遇到的问题：**

**问题 1：`Request not allowed` 错误**

如果遇到此错误，说明系统正在尝试使用 Anthropic API，但你的 API key 可能无效或没有权限。解决方法：

1. **设置默认模型**（推荐）：在 `.env` 文件中添加：
   ```bash
   MSWEA_MODEL_NAME=openai/deepseek-v3.2-exp
   ```

2. **或在命令行指定模型**：
   ```bash
   harmocheck -i ./ -o ./output -m openai/deepseek-v3.2-exp -w 5
   ```

**问题 2：模型成本追踪警告**

如果看到 `Error calculating cost for model...` 警告，说明模型注册表未正确加载。解决方法：

在 `.env` 文件中添加模型注册表路径：
```bash
# 使用系统全局配置时
LITELLM_MODEL_REGISTRY_PATH=$HOME/.config/mini-swe-agent/model_registry.json

# 或使用项目本地配置时
LITELLM_MODEL_REGISTRY_PATH=/path/to/mini-swe-agent/config/local/model_registry.json
```

**注意**：确保已复制 `model_registry.json` 文件到配置目录：
```bash
# 如果使用系统全局配置
cp config/local/model_registry.json ~/.config/mini-swe-agent/
```

### 5. 验证安装

```bash
# 检查命令是否可用
harmocheck --help

# 应该能看到帮助信息，包括：
# -i, --input TEXT     Directory containing code to fix...
# -o, --output TEXT    Directory to save fixed code
# -w, --workers INT    Number of worker threads...
```

## ✅ 完成！

现在你可以使用 `harmocheck` 命令了。

### 示例

为了测试本项目的效果，以OpenHarmony/vendor_telink为案例

```

cd dataset1/openharmony/test
git clone https://gitee.com/openharmony/vendor_telink.git
cd ../../../

```

然后把为您准备的issue文件放入vendor_telink项目中。注意，此issue文件是openharmony数字协作平台直接导出的

```
cp dataset1/openharmony/ISSUE_DESP.xlsx dataset1/openharmony/test/vendor_telink
```

运行

```
harmocheck -i ./dataset1/openharmony/test/vendor_telink -o ./harmocheck_results -w 5 -m openai/deepseek-v3.2-exp
```
