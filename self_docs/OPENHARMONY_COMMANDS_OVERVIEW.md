# OpenHarmony 命令层次结构

## 概述

mini-swe-agent 为 OpenHarmony 提供了三个层次的命令，从单实例到全自动批处理：

```
openharmony-single    →  单个 issue
openharmony-batch     →  指定范围的 issues
openharmony           →  所有项目的所有 issues
```

## 命令对比

| 命令 | 处理范围 | 项目发现 | 并行处理 | 使用场景 |
|------|---------|---------|---------|---------|
| **openharmony-single** | 1 个 issue | 手动指定 | ❌ | 测试、调试单个问题 |
| **openharmony-batch** | 指定范围的 issues | 手动指定 | ✅ | 批量处理部分问题 |
| **openharmony** | 所有 issues | **自动发现** | ✅ | 全自动处理所有问题 |

## 三层命令详解

### 1️⃣ openharmony-single - 单实例处理

**用途**：处理单个代码质量问题

**示例**：
```bash
# 处理第 1 个 issue
mini-extra openharmony-single -i 1

# 使用完整实例 ID
mini-extra openharmony-single -i openharmony__vendor_telink-1
```

**特点**：
- ✅ 快速测试
- ✅ 交互式调试
- ✅ 查看详细输出
- ❌ 无并行处理

---

### 2️⃣ openharmony-batch - 批量处理

**用途**：处理指定范围的问题

**示例**：
```bash
# 处理前 10 个 issues
mini-extra openharmony-batch -i 0:10

# 并行处理 0-29（3 个线程）
mini-extra openharmony-batch -i 0:30 -w 3

# 使用完整实例 ID 范围
mini-extra openharmony-batch -i openharmony__vendor_telink-0:10
```

**特点**：
- ✅ 灵活的范围选择
- ✅ 并行处理支持
- ✅ 实时进度跟踪
- ✅ 可控的批次大小

**范围语法**：
- `0:10` - 处理实例 0-9
- `openharmony__vendor_telink-0:10` - 同上
- `10:` - 从第 10 个到末尾
- `:20` - 前 20 个实例

---

### 3️⃣ openharmony - 全自动处理

**用途**：处理所有项目的所有问题

**示例**：
```bash
# 基本用法（处理所有 issues）
mini-extra openharmony \
    --model anthropic/claude-sonnet-4-5-20250929

# 并行处理（5 个线程）
mini-extra openharmony -w 5

# 指定输出目录
mini-extra openharmony -o results/full_run

# 只处理特定项目
mini-extra openharmony --project vendor_telink
```

**特点**：
- ✅ **自动发现**所有项目
- ✅ 处理所有 issues
- ✅ 项目级别组织
- ✅ 完整的进度报告
- ✅ 适合生产环境

**工作流程**：
1. 扫描 `dataset1/openharmony/test/` 目录
2. 发现所有包含 `ISSUE_DESP.js` 的项目
3. 加载每个项目的所有 issues
4. 按项目顺序处理所有 issues
5. 生成统一的结果报告

---

## 使用场景建议

### 场景 1：初次测试
```bash
# 第 1 步：测试单个 issue
mini-extra openharmony-single -i 0

# 第 2 步：确认没问题后，小批量测试
mini-extra openharmony-batch -i 0:5 -w 2
```

### 场景 2：部分批量处理
```bash
# 只处理前 50 个问题
mini-extra openharmony-batch -i 0:50 -w 5 -o results/first_50
```

### 场景 3：全自动生产运行
```bash
# 处理所有项目的所有 issues
mini-extra openharmony \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -w 10 \
    -o production_results
```

### 场景 4：多项目环境（未来）
```bash
# 假设将来有多个项目
# test/
# ├── vendor_telink/
# ├── vendor_hisilicon/
# └── vendor_qualcomm/

# 处理所有项目
mini-extra openharmony

# 只处理特定项目
mini-extra openharmony --project vendor_telink
```

---

## 参数对比

### 共同参数

| 参数 | 简写 | 所有命令 | 说明 |
|------|-----|---------|------|
| `--subset` | - | ✅ | 数据集路径 |
| `--split` | - | ✅ | 数据集分割（test/train） |
| `--model` | `-m` | ✅ | 模型名称 |
| `--output` | `-o` | ✅ | 输出目录 |
| `--config` | `-c` | ✅ | 配置文件 |

### 特有参数

| 参数 | single | batch | openharmony |
|------|--------|-------|-------------|
| `--instance` (`-i`) | ✅ 单个ID | ✅ 范围 | ❌ |
| `--workers` (`-w`) | ❌ | ✅ | ✅ |
| `--slice` | ❌ | ✅ | ❌ |
| `--project` | ❌ | ❌ | ✅ |

---

## 输出结构对比

### single 输出
```
~/.config/mini-swe-agent/
└── last_openharmony_single_run.traj.json
```

### batch 输出
```
<output_directory>/
├── results.json
├── minisweagent.log
├── exit_statuses_*.yaml
└── openharmony__vendor_telink-{0..N}/
    └── *.traj.json
```

### openharmony 输出
```
<output_directory>/
├── results.json                     # 所有项目的结果
├── minisweagent.log                # 完整日志
├── exit_statuses_*.yaml            # 状态
└── openharmony__<project>-<id>/   # 按项目组织
    └── *.traj.json
```

---

## 成本和时间估算

### 当前数据集（107 个 issues）

| 命令 | 处理数量 | 预估时间（3线程） | 预估成本 |
|------|---------|-----------------|---------|
| `openharmony-single -i 0` | 1 | 1-2 分钟 | ~$2 |
| `openharmony-batch -i 0:10` | 10 | 5-8 分钟 | ~$20 |
| `openharmony-batch -i 0:50` | 50 | 20-30 分钟 | ~$100 |
| `openharmony` | 107 | 40-60 分钟 | ~$214 |

---

## 推荐工作流程

### 🔰 新手入门
```bash
# 1. 单个测试
mini-extra openharmony-single -i 0

# 2. 小批量验证
mini-extra openharmony-batch -i 0:3 -w 1

# 3. 逐步扩大
mini-extra openharmony-batch -i 0:10 -w 2
```

### 🚀 生产运行
```bash
# 直接全自动处理
mini-extra openharmony \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -w 5 \
    -o production_$(date +%Y%m%d)
```

### 🔧 调试特定问题
```bash
# 单个问题深度调试
mini-extra openharmony-single \
    -i openharmony__vendor_telink-5 \
    -o debug_issue_5
```

---

## 命令选择决策树

```
需要处理多少问题？
│
├─ 1 个
│  └─ openharmony-single
│
├─ 部分（如 10-50 个）
│  └─ openharmony-batch
│
└─ 所有问题
   ├─ 单个项目？
   │  └─ openharmony --project vendor_telink
   │
   └─ 所有项目？
      └─ openharmony
```

---

## 最佳实践

1. **从小到大**：single → batch → openharmony
2. **验证结果**：每一步都检查结果质量
3. **控制并行度**：根据 API 限制调整 `-w` 参数
4. **命名输出目录**：使用有意义的名称如 `results/vendor_telink_run1`
5. **监控成本**：注意总成本，必要时分批处理

---

## 文档索引

| 文档 | 内容 |
|------|------|
| `OPENHARMONY_COMMANDS_OVERVIEW.md` | 本文档 - 命令层次 |
| `FINAL_USAGE_GUIDE.md` | 快速上手指南 |
| `OPENHARMONY_BATCH_GUIDE.md` | batch 命令详解 |
| `OPENHARMONY_USAGE.md` | single 命令详解 |
| `QUICK_REFERENCE.md` | 快速参考卡 |

---

**现在你有三个强大的工具可以使用！** 🚀

- 🔍 调试单个问题：`openharmony-single`
- 📦 批量处理部分：`openharmony-batch`
- 🌐 全自动处理：`openharmony`

