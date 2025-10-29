# 模型选择和切换指南

## 📋 已配置的模型

在 `~/.config/mini-swe-agent/.env` 中已配置以下模型：

### 1. Anthropic Claude Sonnet 4
```bash
# 使用方法
--model anthropic/claude-sonnet-4-5-20250929
```

**特点**：
- ✅ 强大的代码理解能力
- ✅ 支持 Prompt Caching（节省成本）
- ✅ 200K 上下文窗口
- 💰 成本：$$$ (高)

### 2. DeepSeek V3.2
```bash
# 使用方法
--model openai/deepseek-v3.2-exp
```

**特点**：
- ✅ OpenAI 兼容接口
- ✅ 自定义 API 地址
- 💰 成本：低

## 🚀 使用示例

### 使用 Claude

```bash
# 单实例
mini-extra openharmony-single \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i 0

# 批量处理
mini-extra openharmony-batch \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i 0:10 \
    -w 3

# 全自动
mini-extra openharmony \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -w 5
```

### 使用 DeepSeek

```bash
# 单实例
mini-extra openharmony-single \
    --model openai/deepseek-v3.2-exp \
    -i 0

# 批量处理
mini-extra openharmony-batch \
    --model openai/deepseek-v3.2-exp \
    -i 0:10 \
    -w 3

# 全自动
mini-extra openharmony \
    --model openai/deepseek-v3.2-exp \
    -w 5
```

## ⚙️ 配置文件说明

查看当前配置：

```bash
cat ~/.config/mini-swe-agent/.env
```

输出示例：

```bash
# ============================================
# Mini-SWE-Agent 模型配置
# ============================================

# Anthropic Claude 模型
ANTHROPIC_API_KEY=sk-ant-api03-...

# DeepSeek 模型（OpenAI 兼容接口）
OPENAI_API_KEY=oL_8pOaS5won...
OPENAI_API_BASE=https://api.modelarts-maas.com/v1
```

## 🔄 切换模型

### 方法 1：命令行指定（推荐）

每次使用时通过 `--model` 参数指定：

```bash
# 使用 Claude
mini-extra openharmony-single --model anthropic/claude-sonnet-4-5-20250929 -i 0

# 使用 DeepSeek
mini-extra openharmony-single --model openai/deepseek-v3.2-exp -i 0
```

### 方法 2：设置默认模型

编辑 `~/.config/mini-swe-agent/.env`，取消注释并设置：

```bash
# 设置 Claude 为默认
MSWEA_MODEL_NAME=anthropic/claude-sonnet-4-5-20250929

# 或设置 DeepSeek 为默认
MSWEA_MODEL_NAME=openai/deepseek-v3.2-exp
```

然后可以直接使用：

```bash
mini-extra openharmony-single -i 0  # 使用默认模型
```

### 方法 3：使用专用配置文件

为每个模型创建配置文件：

```bash
# 使用 Claude 配置
mini-extra openharmony-single \
    -c src/minisweagent/config/extra/openharmony.yaml \
    -i 0

# 使用 DeepSeek 配置
mini-extra openharmony-single \
    -c src/minisweagent/config/custom/deepseek.yaml \
    -i 0
```

## 🆕 添加新模型

### 添加 OpenAI 官方 API

如果需要使用 OpenAI 官方 API（注意：这会覆盖 DeepSeek 配置）：

1. **临时切换**：

```bash
# 临时设置环境变量
export OPENAI_API_KEY="your-openai-key"
export OPENAI_API_BASE="https://api.openai.com/v1"

# 使用 GPT-4
mini-extra openharmony-single --model gpt-4-turbo -i 0
```

2. **永久添加**：

编辑 `~/.config/mini-swe-agent/.env`：

```bash
# 如果需要同时使用 OpenAI 和 DeepSeek
# 可以在命令执行前临时切换，或者使用不同的环境变量名
```

### 添加其他 OpenAI 兼容的 API

1. 编辑 `~/.config/mini-swe-agent/.env`：

```bash
# 示例：添加另一个 API
# ANOTHER_API_KEY=your-key
# ANOTHER_API_BASE=https://your-api.com/v1
```

2. 使用时设置环境变量：

```bash
OPENAI_API_KEY="your-key" OPENAI_API_BASE="https://your-api.com/v1" \
mini-extra openharmony-single --model openai/your-model -i 0
```

## 📊 模型对比和选择建议

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| **首次测试** | DeepSeek | 成本可能更低 |
| **生产环境** | Claude Sonnet 4 | 性能强大，支持 Caching |
| **成本敏感** | DeepSeek | 取决于提供商定价 |
| **复杂问题** | Claude Sonnet 4 | 更强的推理能力 |
| **大批量处理** | Claude Sonnet 4 + Caching | 利用 Prompt Caching 降低成本 |

## 🔧 常见问题

### Q1: 如何查看当前使用的模型？

```bash
# 查看配置文件
cat ~/.config/mini-swe-agent/.env | grep MODEL_NAME

# 或在命令中明确指定
mini-extra openharmony-single --model <model-name> -i 0
```

### Q2: 模型调用失败怎么办？

**检查步骤**：

1. 验证 API Key：
```bash
cat ~/.config/mini-swe-agent/.env | grep API_KEY
```

2. 测试网络连接：
```bash
curl -I https://api.modelarts-maas.com/v1
```

3. 检查模型名称是否正确

### Q3: 如何比较不同模型的效果？

使用相同的测试集：

```bash
# 测试 Claude
mini-extra openharmony-single \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i 0 \
    -o results/claude_test

# 测试 DeepSeek
mini-extra openharmony-single \
    --model openai/deepseek-v3.2-exp \
    -i 0 \
    -o results/deepseek_test

# 比较结果
diff results/claude_test/openharmony__vendor_telink-0/*.traj.json \
     results/deepseek_test/openharmony__vendor_telink-0/*.traj.json
```

### Q4: 可以同时使用多个模型吗？

可以！通过设置不同的输出目录：

```bash
# 并行运行不同模型（使用不同终端）
# 终端 1: Claude
mini-extra openharmony-batch \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i 0:50 \
    -w 3 \
    -o results/claude_run

# 终端 2: DeepSeek
mini-extra openharmony-batch \
    --model openai/deepseek-v3.2-exp \
    -i 50:100 \
    -w 3 \
    -o results/deepseek_run
```

## 📚 相关文档

- **自定义模型配置**：`CUSTOM_MODEL_GUIDE.md`
- **快速参考**：`QUICK_REFERENCE.md`
- **命令层次**：`OPENHARMONY_COMMANDS_OVERVIEW.md`

## ✅ 快速命令参考

```bash
# Claude Sonnet 4
mini-extra openharmony --model anthropic/claude-sonnet-4-5-20250929 -w 5

# DeepSeek V3.2
mini-extra openharmony --model openai/deepseek-v3.2-exp -w 5

# 查看配置
cat ~/.config/mini-swe-agent/.env

# 修改配置
nano ~/.config/mini-swe-agent/.env
```

---

**现在你可以灵活地在不同模型之间切换！** 🚀

推荐做法：
1. 先用 DeepSeek 测试几个实例
2. 对比 Claude 的结果
3. 根据效果和成本选择最适合的模型


