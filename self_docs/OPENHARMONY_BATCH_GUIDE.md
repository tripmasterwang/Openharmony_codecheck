# OpenHarmony 批量处理指南

## 概述

`openharmony-batch` 命令允许你批量处理多个 OpenHarmony 代码质量问题，支持并行处理和进度跟踪。

## 基本用法

### 1. 使用实例范围

```bash
mini-extra openharmony-batch \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i openharmony__vendor_telink-0:10
```

这将处理 `openharmony__vendor_telink-0` 到 `openharmony__vendor_telink-9`（共10个实例）。

### 2. 使用数字范围

```bash
mini-extra openharmony-batch \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i 0:10
```

这将处理前 10 个实例（索引 0-9）。

### 3. 使用切片语法

```bash
mini-extra openharmony-batch \
    --model anthropic/claude-sonnet-4-5-20250929 \
    --slice 0:10
```

等同于 `-i 0:10`。

## 完整示例

```bash
mini-extra openharmony-batch \
    --subset dataset1 \
    --split test \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i openharmony__vendor_telink-0:10 \
    -w 3 \
    -o results/batch_001
```

**说明**：
- `--subset dataset1`: 使用 dataset1 数据集
- `--split test`: 使用测试集
- `--model`: 指定使用的模型
- `-i openharmony__vendor_telink-0:10`: 处理实例 0-9
- `-w 3`: 使用 3 个并行工作线程
- `-o results/batch_001`: 输出到指定目录

## 参数详解

### 数据选择参数

| 参数 | 简写 | 说明 | 默认值 | 示例 |
|------|-----|------|--------|------|
| `--subset` | - | 数据集路径 | `dataset1` | `--subset dataset1` |
| `--split` | - | 数据集分割 | `test` | `--split test` |
| `--instance` | `-i` | 实例范围 | 无 | `-i 0:10` 或 `-i openharmony__vendor_telink-0:10` |
| `--slice` | - | 切片规范 | 无 | `--slice 0:5` |
| `--filter` | - | 正则过滤器 | 无 | `--filter ".*telink.*"` |
| `--redo-existing` | - | 重新处理已完成的实例 | `False` | `--redo-existing` |

### 基本参数

| 参数 | 简写 | 说明 | 默认值 |
|------|-----|------|--------|
| `--output` | `-o` | 输出目录 | 自动生成（时间戳） |
| `--workers` | `-w` | 并行工作线程数 | `1` |
| `--model` | `-m` | 模型名称 | 配置文件中指定 |
| `--config` | `-c` | 配置文件路径 | `config/extra/openharmony.yaml` |

### 高级参数

| 参数 | 说明 |
|------|------|
| `--model-class` | 模型类（如 'anthropic'） |

## 实例范围语法

### 格式 1：完整实例 ID 范围

```bash
-i openharmony__vendor_telink-0:10
```

- 处理 `openharmony__vendor_telink-0` 到 `openharmony__vendor_telink-9`
- **注意**：右边界不包含（Python 切片语义）

### 格式 2：数字范围

```bash
-i 0:10
```

- 处理索引 0 到 9 的实例
- 按实例 ID 的数字后缀排序

### 格式 3：开放式范围

```bash
-i 10:          # 从索引 10 到末尾
-i :20          # 从开头到索引 19
```

## 并行处理

使用 `-w` 参数指定并行工作线程数：

```bash
# 单线程（顺序处理）
mini-extra openharmony-batch -i 0:10 -w 1

# 3 个并行线程
mini-extra openharmony-batch -i 0:30 -w 3

# 10 个并行线程（处理大量实例）
mini-extra openharmony-batch -i 0:100 -w 10
```

**建议**：
- CPU 核心数的 1-2 倍为宜
- 考虑 API 速率限制
- 监控内存使用

## 输出结构

批量处理会创建以下结构：

```
<output_directory>/
├── results.json                          # 所有实例的结果摘要
├── minisweagent.log                      # 日志文件
├── exit_statuses_<timestamp>.yaml        # 退出状态记录
└── <instance_id>/                        # 每个实例一个目录
    └── <instance_id>.traj.json          # 完整轨迹
```

### results.json 格式

```json
{
  "openharmony__vendor_telink-0": {
    "model_name_or_path": "anthropic/claude-sonnet-4-5-20250929",
    "instance_id": "openharmony__vendor_telink-0",
    "result": "修复结果内容"
  },
  "openharmony__vendor_telink-1": {
    ...
  }
}
```

## 实际使用场景

### 场景 1：处理前 10 个简单问题

```bash
mini-extra openharmony-batch \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i 0:10 \
    -w 2 \
    -o results/first_10
```

### 场景 2：处理特定范围的问题

```bash
mini-extra openharmony-batch \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i openharmony__vendor_telink-20:30 \
    -w 3
```

### 场景 3：重新处理失败的实例

```bash
# 第一次运行
mini-extra openharmony-batch -i 0:50 -o results/run1

# 查看失败的实例，然后重新处理
mini-extra openharmony-batch -i 0:50 -o results/run1 --redo-existing
```

### 场景 4：处理所有实例

```bash
mini-extra openharmony-batch \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i 0:107 \
    -w 5 \
    -o results/full_run
```

## 进度跟踪

批量处理会实时显示进度信息：

```
Processing 10 instances...

[1/10] openharmony__vendor_telink-0  ✓ Submitted (Step 15, $0.12)
[2/10] openharmony__vendor_telink-1  ⟳ Step 8 ($0.08)
[3/10] openharmony__vendor_telink-2  ⟳ Starting...
...
```

## 错误处理

### 跳过已完成的实例

默认情况下，已经成功处理的实例会被跳过：

```bash
# 第一次运行：处理 10 个实例
mini-extra openharmony-batch -i 0:10 -o results/run1

# 第二次运行：只处理失败的实例
mini-extra openharmony-batch -i 0:10 -o results/run1
# 已成功的实例会被自动跳过
```

### 重新处理所有实例

使用 `--redo-existing` 强制重新处理：

```bash
mini-extra openharmony-batch -i 0:10 -o results/run1 --redo-existing
```

## 性能优化建议

### 1. 合理设置并行度

```bash
# 本地测试：1-2 线程
mini-extra openharmony-batch -i 0:5 -w 1

# 生产运行：根据 API 限制
mini-extra openharmony-batch -i 0:100 -w 5
```

### 2. 分批处理

对于大量实例，建议分批处理：

```bash
# 批次 1
mini-extra openharmony-batch -i 0:25 -o results/batch1 -w 5

# 批次 2
mini-extra openharmony-batch -i 25:50 -o results/batch2 -w 5

# 批次 3
mini-extra openharmony-batch -i 50:75 -o results/batch3 -w 5
```

### 3. 监控成本

每个实例的成本限制为 $2（配置在 openharmony.yaml 中）：

- 10 个实例 ≈ $20
- 50 个实例 ≈ $100
- 107 个实例 ≈ $214

## 故障排查

### 问题：实例范围解析错误

**错误**：没有选择到任何实例

**解决**：
```bash
# 检查可用实例
python -c "
from minisweagent.run.extra.openharmony_single import load_openharmony_dataset
instances = load_openharmony_dataset('dataset1', 'test')
print('可用实例:', sorted(instances.keys(), key=lambda x: int(x.split('-')[-1]))[:10])
"

# 使用正确的范围
mini-extra openharmony-batch -i openharmony__vendor_telink-0:10
```

### 问题：并行处理时 API 限制

**现象**：频繁的 API 错误

**解决**：
```bash
# 减少并行度
mini-extra openharmony-batch -i 0:50 -w 2  # 而不是 -w 10
```

### 问题：输出目录已存在

**现象**：警告或错误提示目录已存在

**解决**：
```bash
# 使用新的输出目录
mini-extra openharmony-batch -i 0:10 -o results/run_$(date +%Y%m%d_%H%M%S)

# 或者使用 --redo-existing 覆盖
mini-extra openharmony-batch -i 0:10 -o results/run1 --redo-existing
```

## 与单实例模式的对比

| 特性 | openharmony-single | openharmony-batch |
|------|-------------------|-------------------|
| 处理数量 | 1 个 | 多个 |
| 并行处理 | 否 | 是（-w 参数） |
| 进度跟踪 | 简单 | 详细 |
| 输出格式 | 单个轨迹文件 | 目录结构 + results.json |
| 适用场景 | 测试、调试 | 生产、批量修复 |

## 最佳实践

1. **从小范围开始**
   ```bash
   mini-extra openharmony-batch -i 0:5 -w 1
   ```

2. **验证结果后再扩大规模**
   ```bash
   # 检查前 5 个实例的结果
   # 确认没问题后处理更多
   mini-extra openharmony-batch -i 0:50 -w 3
   ```

3. **使用有意义的输出目录名**
   ```bash
   mini-extra openharmony-batch -i 0:10 -o results/assert_fixes_batch1
   ```

4. **保存运行脚本**
   ```bash
   # run_batch.sh
   #!/bin/bash
   mini-extra openharmony-batch \
       --model anthropic/claude-sonnet-4-5-20250929 \
       -i openharmony__vendor_telink-0:50 \
       -w 5 \
       -o results/production_run_$(date +%Y%m%d)
   ```

## 总结

`openharmony-batch` 命令提供了强大的批量处理能力：
- ✅ 支持灵活的实例范围选择
- ✅ 并行处理加速执行
- ✅ 实时进度跟踪
- ✅ 自动跳过已完成实例
- ✅ 结构化输出便于分析

适合处理大量代码质量问题！🚀


