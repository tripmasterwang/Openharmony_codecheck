# OpenHarmony Integration - 最终使用指南

## ✅ 项目已完成适配

所有功能已实现并通过测试！现在可以使用以下命令处理 OpenHarmony 代码质量问题。

## 快速开始

### 1. 单实例处理

```bash
mini-extra openharmony-single \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i openharmony__vendor_telink-1
```

### 2. 批量处理

```bash
mini-extra openharmony-batch \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i openharmony__vendor_telink-0:10 \
    -w 3
```

这将并行处理实例 0-9（共10个问题），使用 3 个工作线程。

### 3. 全自动处理（🆕 最新功能！）

```bash
mini-extra openharmony \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -w 5
```

**自动发现并处理所有项目的所有 issues！**不需要指定实例范围。

### 3. 可用实例

当前数据集包含 **107 个代码质量问题**，实例 ID 范围：
- `openharmony__vendor_telink-0` 到 `openharmony__vendor_telink-106`

### 4. 两种选择方式（单实例模式）

#### 方式 A：使用实例 ID
```bash
mini-extra openharmony-single -i openharmony__vendor_telink-1
```

#### 方式 B：使用数字索引
```bash
mini-extra openharmony-single -i 1
```

**注意**：数字索引基于字典序排序，不是数字序。建议使用完整的实例 ID。

## 实际示例

### 示例 1：修复 assert 宏使用问题

```bash
mini-extra openharmony-single \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i openharmony__vendor_telink-1
```

**问题详情**：
- 文件：`ble_demo/b91_gatt_sample/app.c`
- 行号：197
- 问题：`assert(status == BLE_SUCCESS);`
- 规则：G.AST.01 断言必须使用宏定义，且只能在调试版本中生效【C】
- 严重程度：严重

**预期修复**：
```c
// 修复前
assert(status == BLE_SUCCESS);

// 修复后
ASSERT(status == BLE_SUCCESS);
```

### 示例 2：查看某个实例的详细信息

```bash
python -c "
from minisweagent.run.extra.openharmony_single import load_openharmony_dataset, format_openharmony_issue

instances = load_openharmony_dataset('dataset1', 'test')
instance = instances['openharmony__vendor_telink-50']

print(format_openharmony_issue(instance))
"
```

## 命令参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|-----|------|--------|
| `--subset` | - | 数据集路径 | `dataset1` |
| `--split` | - | 数据集分割 | `test` |
| `--instance` | `-i` | 实例 ID 或索引 | `0` |
| `--model` | `-m` | 模型名称 | 配置文件中指定 |
| `--config` | `-c` | 配置文件路径 | `config/extra/openharmony.yaml` |
| `--output` | `-o` | 输出轨迹文件 | `~/.config/mini-swe-agent/last_openharmony_single_run.traj.json` |
| `--exit-immediately` | - | 完成后立即退出 | `False` |

## 工作流程

1. **Agent 加载任务**
   - 从 `ISSUE_DESP.js` 读取问题描述
   - 生成自然语言任务

2. **静态分析阶段**
   - 使用 `ls`, `find` 浏览项目结构
   - 使用 `cat`, `head`, `tail` 读取代码
   - 使用 `grep` 搜索相关代码

3. **代码修改阶段**
   - 使用 `sed` 进行精确的行替换
   - 或使用 `cat` + heredoc 重写文件

4. **提交阶段**
   - 执行 `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`
   - Agent 停止工作

## 配置特点

`config/extra/openharmony.yaml` 的关键设置：

```yaml
agent:
  system_template: |
    You are a code quality expert that performs STATIC CODE ANALYSIS ONLY.
    DO NOT run or execute the code.
    DO NOT create test scripts or verification scripts.
  
  step_limit: 100  # 最多 100 步
  cost_limit: 2.0  # 最多 $2

environment:
  timeout: 30  # 命令超时 30 秒
```

## 验证测试

所有功能已通过测试：

```bash
# 测试命令注册
$ mini-extra --help
  openharmony-single: Evaluate on OpenHarmony (single instance)

# 测试参数解析
$ mini-extra openharmony-single --help
  [显示完整帮助信息]

# 测试数据加载
✅ 成功加载 107 个实例
✅ 实例 ID: openharmony__vendor_telink-0 到 -106
✅ 所有文件路径有效
✅ 中文字段名正确解析
```

## 故障排查

### 问题：找不到实例

**错误信息**：
```
Instance openharmony__vendor_telink-XXX not found
```

**解决方法**：
```bash
# 查看所有可用实例
python -c "
from minisweagent.run.extra.openharmony_single import load_openharmony_dataset
instances = load_openharmony_dataset('dataset1', 'test')
print('可用实例：', sorted([iid for iid in instances.keys() if 'vendor_telink' in iid])[:20])
"
```

### 问题：目标文件不存在

**检查文件**：
```bash
ls -la dataset1/openharmony/test/vendor_telink/ble_demo/b91_gatt_sample/app.c
```

### 问题：API 密钥未配置

**配置密钥**：
```bash
mini-extra config set ANTHROPIC_API_KEY your-key-here
```

## 数据集统计

**项目**：vendor_telink  
**问题总数**：107  
**问题类型**：
- 断言使用 (G.AST.01, G.AST.03)
- 循环安全 (G.CTL.03)
- 内存管理 (G.MEM.01)
- 格式规范 (G.FMT.04-CPP)

**严重程度分布**：
- 严重
- 一般
- 建议

## 与 SWE-bench 的对比

| 特性 | SWE-bench | OpenHarmony |
|-----|-----------|-------------|
| 执行环境 | Docker 容器 | 本地文件系统 |
| 工作方式 | 动态测试 | **静态分析** |
| 问题类型 | 功能 bug | 代码规范 |
| 步数限制 | 250 | 100 |
| 成本限制 | $3 | $2 |

## 命令对比

| 特性 | openharmony-single | openharmony-batch | openharmony |
|------|-------------------|-------------------|-------------|
| 处理数量 | 1 个 | 指定范围 | **所有项目所有 issues** |
| 项目发现 | 手动指定 | 手动指定 | **自动发现** |
| 并行处理 | 否 | 是（`-w` 参数） | 是（`-w` 参数） |
| 进度跟踪 | 简单 | 实时详细 | 实时详细 + 项目级别 |
| 适用场景 | 测试、调试 | 部分批量修复 | **全自动生产运行** |
| 输出 | 单个轨迹文件 | 目录结构 + results.json | 同 batch |

## 文档参考

- **命令层次概览**：`OPENHARMONY_COMMANDS_OVERVIEW.md` ⭐⭐ 最新
- **快速参考卡**：`QUICK_REFERENCE.md` ⭐ 推荐
- **批量处理指南**：`OPENHARMONY_BATCH_GUIDE.md`
- **详细使用说明**：`OPENHARMONY_USAGE.md`
- **数据格式适配**：`ADAPTATION_NOTES.md`
- **修改总结**：`MODIFICATIONS_SUMMARY.md`

## 下一步

### 推荐路径
1. **单个测试**：`mini-extra openharmony-single -i 0`
2. **小批量验证**：`mini-extra openharmony-batch -i 0:5 -w 2`
3. **全自动运行**：`mini-extra openharmony -w 5` ✅ 新增

### 高级用法
- **查看命令层次**：阅读 `OPENHARMONY_COMMANDS_OVERVIEW.md`
- **快速参考**：查看 `QUICK_REFERENCE.md`
- **生产部署**：使用 `openharmony` 命令处理所有问题

---

**准备就绪！开始使用吧！** 🚀

