# OpenHarmony 快速参考卡

## 🚀 快速命令

### 单实例处理
```bash
# 处理第 1 个问题
mini-extra openharmony-single -i 1

# 使用指定模型
mini-extra openharmony-single \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i openharmony__vendor_telink-1
```

### 批量处理
```bash
# 处理前 10 个问题（顺序）
mini-extra openharmony-batch -i 0:10

# 并行处理前 30 个问题（3 线程）
mini-extra openharmony-batch -i 0:30 -w 3

# 指定输出目录
mini-extra openharmony-batch -i 0:10 -o results/batch1
```

## 📊 命令对比

| 命令 | 用途 | 并行 | 适用场景 |
|------|------|------|---------|
| `openharmony-single` | 处理单个问题 | ❌ | 测试、调试 |
| `openharmony-batch` | 批量处理 | ✅ | 生产运行 |

## 🎯 常用参数

### 通用参数
| 参数 | 简写 | 说明 | 示例 |
|------|-----|------|------|
| `--model` | `-m` | 模型名称 | `-m anthropic/claude-sonnet-4-5-20250929` |
| `--output` | `-o` | 输出目录 | `-o results/run1` |
| `--config` | `-c` | 配置文件 | `-c my_config.yaml` |

### 实例选择（batch 专用）
| 参数 | 简写 | 说明 | 示例 |
|------|-----|------|------|
| `--instance` | `-i` | 实例范围 | `-i 0:10` 或 `-i openharmony__vendor_telink-0:10` |
| `--workers` | `-w` | 并行线程数 | `-w 3` |
| `--slice` | - | 切片规范 | `--slice 0:5` |

## 📝 实例范围语法

```bash
# 格式 1: 完整实例 ID 范围
-i openharmony__vendor_telink-0:10    # 实例 0-9

# 格式 2: 数字范围
-i 0:10                                # 前 10 个实例

# 格式 3: 开放式范围
-i 10:                                 # 从第 10 个到结尾
-i :20                                 # 前 20 个实例
```

## 💰 成本估算

| 实例数 | 预估成本 | 建议并行度 |
|--------|---------|----------|
| 1-10 | $2-20 | 1-2 |
| 10-50 | $20-100 | 3-5 |
| 50-107 | $100-214 | 5-10 |

**注意**：每个实例最高成本 $2

## ⏱️ 时间估算

### 单线程
- 10 个实例：10-15 分钟
- 50 个实例：50-75 分钟

### 3 线程并行
- 10 个实例：5-8 分钟
- 50 个实例：20-30 分钟

## 📁 输出结构

### 单实例模式
```
~/.config/mini-swe-agent/
└── last_openharmony_single_run.traj.json
```

### 批量模式
```
<output_directory>/
├── results.json              # 结果摘要
├── minisweagent.log         # 日志
├── exit_statuses_*.yaml     # 状态
└── <instance_id>/
    └── *.traj.json          # 轨迹
```

## 🔍 故障排查

### 查看可用实例
```bash
python -c "
from minisweagent.run.extra.openharmony_single import load_openharmony_dataset
instances = load_openharmony_dataset('dataset1', 'test')
print('总数:', len(instances))
print('前 10 个:', sorted(instances.keys(), key=lambda x: int(x.split('-')[-1]))[:10])
"
```

### 检查 API 密钥
```bash
mini-extra config set ANTHROPIC_API_KEY your-key-here
```

### 查看日志
```bash
# 单实例
cat ~/.config/mini-swe-agent/last_openharmony_single_run.traj.json

# 批量
cat results/minisweagent.log
```

## 📚 完整文档

| 文档 | 内容 |
|------|------|
| `OPENHARMONY_BATCH_GUIDE.md` | 批量处理详细指南 |
| `FINAL_USAGE_GUIDE.md` | 完整使用指南 |
| `OPENHARMONY_USAGE.md` | 单实例详细说明 |
| `QUICK_REFERENCE.md` | 本文档 |

## 🎯 典型工作流

### 工作流 1：测试单个问题
```bash
# 1. 查看问题
mini-extra openharmony-single -i 0

# 2. 检查结果
cat ~/.config/mini-swe-agent/last_openharmony_single_run.traj.json
```

### 工作流 2：批量处理
```bash
# 1. 小范围测试
mini-extra openharmony-batch -i 0:5 -w 2 -o test_run

# 2. 检查结果
cat test_run/results.json

# 3. 扩大范围
mini-extra openharmony-batch -i 0:50 -w 5 -o production_run
```

### 工作流 3：分批处理全部实例
```bash
# 批次 1
mini-extra openharmony-batch -i 0:35 -w 5 -o batch1

# 批次 2
mini-extra openharmony-batch -i 35:70 -w 5 -o batch2

# 批次 3
mini-extra openharmony-batch -i 70:107 -w 5 -o batch3
```

## 🚨 注意事项

1. **成本控制**：每个实例最高 $2，注意总成本
2. **API 限制**：注意 API 速率限制，适当调整并行度
3. **本地环境**：使用本地文件系统，无需 Docker
4. **静态分析**：不运行代码，只进行代码修改

## ✅ 最佳实践

1. ✅ 先用 `openharmony-single` 测试
2. ✅ 小范围试用 `openharmony-batch`
3. ✅ 验证结果后扩大规模
4. ✅ 使用有意义的输出目录名
5. ✅ 监控成本和进度
6. ✅ 定期检查结果质量

---

**准备开始？运行第一个命令吧！** 🚀

```bash
mini-extra openharmony-single -i 0
```

