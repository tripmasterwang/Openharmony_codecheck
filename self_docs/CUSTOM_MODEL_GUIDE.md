# 自定义模型配置指南

## DeepSeek V3.2 模型配置（已完成）

### ✅ 配置状态

您的自定义 DeepSeek V3.2 模型已成功配置！

**配置信息**：
- API 地址：`https://api.modelarts-maas.com/v1`
- 模型名称：`deepseek-v3.2-exp`
- API Key：已配置（存储在 `~/.config/mini-swe-agent/.env`）

### 📋 配置详情

配置文件位置：`~/.config/mini-swe-agent/.env`

```bash
OPENAI_API_KEY='oL_8pOaS5wonYsuQ_OpV0kychFTpE6e55DXO6psHo4E1S726yihN7M3Y9M1Mp0QbxhGQ6z9yFQZ0wnPSo86Y4A'
OPENAI_API_BASE='https://api.modelarts-maas.com/v1'
```

## 🚀 使用方法

### 方法 1：直接使用（最简单）

由于已经配置了环境变量，现在可以直接使用：

```bash
# 单实例处理
mini-extra openharmony-single \
    --model openai/deepseek-v3.2-exp \
    -i 0

# 批量处理
mini-extra openharmony-batch \
    --model openai/deepseek-v3.2-exp \
    -i 0:10 \
    -w 3

# 全自动处理
mini-extra openharmony \
    --model openai/deepseek-v3.2-exp \
    -w 5
```

### 方法 2：使用专用配置文件

已创建 DeepSeek 专用配置文件：`src/minisweagent/config/custom/deepseek.yaml`

使用方法：

```bash
# 单实例
mini-extra openharmony-single \
    -c src/minisweagent/config/custom/deepseek.yaml \
    -i 0

# 批量处理
mini-extra openharmony-batch \
    -c src/minisweagent/config/custom/deepseek.yaml \
    -i 0:10 \
    -w 3

# 全自动
mini-extra openharmony \
    -c src/minisweagent/config/custom/deepseek.yaml \
    -w 5
```

**优点**：
- ✅ 不需要每次指定 `--model`
- ✅ 可以自定义 prompt 模板
- ✅ 可以调整步数和成本限制

### 方法 3：设为默认模型

如果想让 DeepSeek 成为默认模型，修改配置文件：

```bash
# 编辑全局配置
nano ~/.config/mini-swe-agent/.env

# 添加以下行
MSWEA_MODEL_NAME=openai/deepseek-v3.2-exp
```

然后就可以直接使用，无需指定模型：

```bash
mini-extra openharmony-single -i 0
```

## 📊 与其他模型的对比

| 模型 | API | 成本 | 速度 | 适用场景 |
|------|-----|------|------|---------|
| **DeepSeek V3.2** | 自定义 | ? | ? | 代码分析 |
| Claude Sonnet 4 | Anthropic | $$$ | 快 | 通用 |
| GPT-4 | OpenAI | $$$$ | 中 | 通用 |

## 🔧 故障排查

### 问题 1：API 连接错误

**错误信息**：
```
AuthenticationError: Invalid API key
```

**解决方法**：
```bash
# 重新设置 API Key
mini-extra config set OPENAI_API_KEY your-new-api-key
```

### 问题 2：模型不存在

**错误信息**：
```
NotFoundError: Model deepseek-v3.2-exp not found
```

**解决方法**：
确认模型名称正确，或联系 API 提供商确认模型名称。

### 问题 3：API Base 配置错误

**解决方法**：
```bash
# 重新设置 API Base
mini-extra config set OPENAI_API_BASE https://api.modelarts-maas.com/v1

# 验证配置
cat ~/.config/mini-swe-agent/.env
```

## 💡 高级配置

### 自定义请求参数

编辑配置文件 `src/minisweagent/config/custom/deepseek.yaml`：

```yaml
model:
  model_name: "openai/deepseek-v3.2-exp"
  model_kwargs:
    temperature: 0.0      # 温度参数（0-2）
    max_tokens: 4096      # 最大生成长度
    top_p: 1.0            # Top-p 采样
    drop_params: true     # 丢弃不支持的参数
```

### 调整步数和成本限制

```yaml
agent:
  step_limit: 150        # 最多 150 步（默认 100）
  cost_limit: 5.0        # 最多 $5（默认 $2）
```

### 自定义 Prompt 模板

```yaml
agent:
  system_template: |
    你是一个专业的代码质量专家。
    你的任务是进行静态代码分析，找出并修复代码质量问题。
    
    请用中文思考，用英文编写命令。
```

## 📝 使用示例

### 示例 1：测试单个问题

```bash
mini-extra openharmony-single \
    --model openai/deepseek-v3.2-exp \
    -i openharmony__vendor_telink-1 \
    -o test_deepseek
```

### 示例 2：批量处理前 10 个问题

```bash
mini-extra openharmony-batch \
    --model openai/deepseek-v3.2-exp \
    -i 0:10 \
    -w 2 \
    -o deepseek_batch_10
```

### 示例 3：全自动处理所有问题

```bash
mini-extra openharmony \
    --model openai/deepseek-v3.2-exp \
    -w 5 \
    -o deepseek_full_run
```

## 🔄 切换回其他模型

### 切换到 Claude

```bash
mini-extra openharmony-single \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i 0
```

### 切换到 GPT-4

```bash
mini-extra openharmony-single \
    --model gpt-4-turbo \
    -i 0
```

## 📚 相关文档

- **OpenHarmony 使用指南**：`FINAL_USAGE_GUIDE.md`
- **命令层次说明**：`OPENHARMONY_COMMANDS_OVERVIEW.md`
- **快速参考**：`QUICK_REFERENCE.md`

## ✅ 快速验证

测试 DeepSeek 模型是否正常工作：

```bash
# 快速测试
mini-extra openharmony-single \
    --model openai/deepseek-v3.2-exp \
    -i 0

# 查看结果
cat ~/.config/mini-swe-agent/last_openharmony_single_run.traj.json
```

---

**🎉 DeepSeek V3.2 模型已配置完成，可以立即使用！**

如有问题，请检查：
1. API Key 是否正确
2. API Base 地址是否正确
3. 网络连接是否正常
4. 模型名称是否正确
