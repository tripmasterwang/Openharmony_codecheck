# Mini-SWE-Agent OpenHarmony 扩展 - 快速开始

## 📦 安装步骤

### 1. 克隆代码

```bash
git clone https://github.com/tripmasterwang/Openharmony_codecheck.git
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

### 4. 配置 API 密钥

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

**方法 2：使用项目本地配置**

适合只在项目目录中使用的情况：

```bash
# 复制配置示例文件
cp config/local/.env.example config/local/.env

# 编辑配置文件，填入你的 API 密钥
nano config/local/.env  # 或使用其他编辑器
```

**必需的 API 密钥：**

- **DeepSeek**（推荐）：需要 `OPENAI_API_KEY` 和 `OPENAI_API_BASE`
  - 获取方式：访问 [DeepSeek 官网](https://www.deepseek.com/) 或使用华为云 ModelArts
- **Anthropic Claude**：需要 `ANTHROPIC_API_KEY`
  - 获取方式：访问 [Anthropic 官网](https://www.anthropic.com/)

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

### 快速开始示例

```bash
# 1. 进入你的代码仓库目录（必须包含 ISSUE_DESP.js 或 ISSUE_DESP.xlsx）
cd /path/to/your/code/repo

# 2. 运行修复命令（使用 5 个线程并行处理）
harmocheck -i ./ -o ./harmocheck_results -w 5

# 3. 等待处理完成，修复后的代码会保存在 ./harmocheck_results 目录中
```

## 📋 完整安装检查清单

- [ ] ✅ 已克隆代码仓库
- [ ] ✅ 已创建并激活 Python 环境（Python 3.10+）
- [ ] ✅ 已安装项目依赖（`pip install -e '.[full]'`）
- [ ] ✅ 已配置 API 密钥（在 `~/.config/mini-swe-agent/.env` 或 `config/local/.env`）
- [ ] ✅ 已复制 `model_registry.json` 到配置目录（如果使用方法1）
- [ ] ✅ 已验证命令可用（`harmocheck --help`）
- [ ] ✅ 已准备包含 `ISSUE_DESP.js` 或 `ISSUE_DESP.xlsx` 的代码仓库

## 使用方法

### 0. 安装测试案例

为了测试本项目的效果，以OpenHarmony/vendor_telink为案例

```bash
cd dataset1/openharmony/test
git clone https://gitee.com/openharmony/vendor_telink.git
cd ../../../
```

然后把为您准备的issue文件放入vendor_telink项目中。注意，此issue文件是openharmony数字协作平台直接导出的

```bash
mv dataset1/openharmony/ISSUE_DESP.xlsx dataset1/openharmony/test/vendor_telink
```

### 1. 修复单个Issue（openharmony-single）

修复指定项目中的单个issue：

```bash
# 使用 DeepSeek 官方（自动）
mini-extra openharmony-single --model openai/deepseek-v3.2-exp -i 0

# 使用第三方（显式指定）
mini-extra openharmony-single \
    --model openai/deepseek-v3.2-exp \
    --model-class litellm \
    -i 0
```

**说明**：此命令会修复 `dataset1/openharmony/test/vendor_telink` 中的代码，自动寻找 `ISSUE_DESP.js` 文件，并尝试修复index为0的issue。

### 2. 批量修复Issues（openharmony-batch）

修复指定项目中的多个issue：

```bash
mini-extra openharmony-batch \
    --subset dataset1 \
    --split test \
    --model openai/deepseek-v3.2-exp \
    -i openharmony__vendor_telink-0:10
```

**说明**：此命令会修复 `dataset1/openharmony/test/vendor_telink` 中的代码，自动寻找 `ISSUE_DESP.js` 文件，并依次修复index为0到9的所有issues。

### 3. 全量修复（openharmony）

修复所有项目中的所有issues：

```bash
mini-extra openharmony \
    --subset dataset1 \
    --split test \
    --model openai/deepseek-v3.2-exp \
    -w 5
```

**说明**：
- 此命令会修复 `dataset1/openharmony/test` 中所有项目的所有issues
- `-w 5` 表示使用5个并行进程
- 对于每个项目，会自动寻找 `ISSUE_DESP.js` 文件并修复其中描述的所有问题
- 完成一个项目后，会自动进入下一个项目

### 4. 在任意目录中使用 HarmoCheck（推荐）

`harmocheck` 是一个独立的命令行工具，可以在任何包含 `ISSUE_DESP.js` 或 `ISSUE_DESP.xlsx` 的代码仓库目录中使用：

```bash
# 进入代码仓库目录
cd /path/to/your/code/repo

# 使用 5 个线程并行修复所有问题
harmocheck -i ./ -o ./harmocheck_results -w 5

# 使用默认模型（从环境变量读取）
harmocheck -i ./ -o ./harmocheck_results -w 3

# 指定模型
harmocheck -i ./ -o ./harmocheck_results -w 5 -m openai/deepseek-v3.2-exp

# 只修复特定问题（索引从 0 开始）
harmocheck -i ./ -o ./harmocheck_results --issue 0
```

**说明**：
- `-i` / `--input`: 输入目录（必须包含 `ISSUE_DESP.js` 或 `ISSUE_DESP.xlsx`）
- `-o` / `--output`: 输出目录（修复后的代码保存位置）
- `-w` / `--workers`: 并行工作线程数（默认 1，建议 3-5）
- `-m` / `--model`: 指定使用的模型（可选，默认从环境变量 `MSWEA_MODEL_NAME` 读取）
- `--issue`: 只修复指定索引的问题（可选，不指定则修复所有问题）

**特点**：
- ✅ 自动检测并转换 `ISSUE_DESP.xlsx` 为 `ISSUE_DESP.js`
- ✅ 支持多线程并行处理，大幅提升处理速度
- ✅ 自动排除输出目录，避免递归复制
- ✅ 显示实时进度条，不显示详细对话内容
- ✅ 无需用户交互，自动执行所有修复

## 参数说明

### 通用参数

- `--model` / `-m`: 使用的AI模型
  - Anthropic: `anthropic/claude-sonnet-4-5-20250929`
  - OpenAI/DeepSeek: `openai/deepseek-v3.2-exp`
- `-w` / `--workers`: 并行worker数量（用于批量处理和 harmocheck）

### openharmony-single / openharmony-batch 参数

- `--subset`: 数据集子集名称（如 dataset1）
- `--split`: 数据集分割（如 test, train）
- `-i` / `--instance`: Issue标识符
  - 单个issue: `openharmony__vendor_telink-0`
  - 多个issues: `openharmony__vendor_telink-0:10` (从0到9)

### harmocheck 参数

- `-i` / `--input`: 输入目录（包含 ISSUE_DESP.js 或 ISSUE_DESP.xlsx 的目录）
- `-o` / `--output`: 输出目录（修复后的代码保存位置）
- `--issue`: 只修复指定索引的问题（0-based，可选）

## 输出结果

修复结果会保存在对应的输出目录中，包括：
- 修改后的代码文件
- 修复日志和轨迹
- 测试结果（如果有）

## 更多信息

详细文档请参考：
- [快速参考](./self_docs/QUICK_REFERENCE.md)
- [本地部署指南](./self_docs/LOCAL_DEPLOYMENT_GUIDE.md)
- [适配说明](./self_docs/ADAPTATION_NOTES.md)
- [OpenHarmony批量处理指南](./self_docs/OPENHARMONY_BATCH_GUIDE.md)
