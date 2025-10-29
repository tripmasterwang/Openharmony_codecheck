# Mini-SWE-Agent OpenHarmony 扩展 - 快速开始

## 安装

```bash
git clone https://github.com/tripmasterwang/Openharmony_codecheck.git
cd Openharmony_codecheck
conda create -n harmonycheck python=3.11 -y
pip install -e '.[full]'
```

## 环境配置

在使用前，请确保设置了相应的API密钥：可以在.env中输入密钥，如

```bash
ANTHROPIC_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXX

# DeepSeek 模型（OpenAI 兼容接口）
# 使用: --model openai/deepseek-v3.2-exp
# 价格: ¥0.0008/1K input, ¥0.0012/1K output (约 $0.114/1M input, $0.171/1M output)
OPENAI_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
OPENAI_API_BASE=https://api.modelarts-maas.com/v1

# 模型价格注册文件（使用项目本地路径）
LITELLM_MODEL_REGISTRY_PATH=config/local/model_registry.json

# 全局配置目录（使用项目本地）
MSWEA_GLOBAL_CONFIG_DIR=config/local
```

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
mini-extra openharmony-single \
    --subset dataset1 \
    --split test \
    --model openai/deepseek-v3.2-exp \
    -i openharmony__vendor_telink-0
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

## 参数说明

- `--subset`: 数据集子集名称（如 dataset1）
- `--split`: 数据集分割（如 test, train）
- `--model`: 使用的AI模型
  - Anthropic: `anthropic/claude-sonnet-4-5-20250929`
  - OpenAI/DeepSeek: `openai/deepseek-v3.2-exp`
- `-i`: Issue标识符
  - 单个issue: `openharmony__vendor_telink-0`
  - 多个issues: `openharmony__vendor_telink-0:10` (从0到9)
- `-w`: 并行worker数量（仅用于全量修复）

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
