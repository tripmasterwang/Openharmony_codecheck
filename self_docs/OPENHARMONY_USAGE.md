# OpenHarmony 集成使用说明

## 概述

本项目已成功集成 OpenHarmony 代码质量问题修复功能，提供与 SWE-bench 类似的体验，但专注于**静态代码分析**而非动态测试。

## 新增功能

### 1. `openharmony-single` 命令

用于处理单个 OpenHarmony 代码质量问题。

### 2. 核心特性

- ✅ **增量式修改**：保留原有所有 SWE-bench 功能
- ✅ **静态分析优先**：短路动态检查，只做代码分析和修改
- ✅ **本地文件系统**：直接在项目目录中工作，无需 Docker
- ✅ **自动 Issue 加载**：从 `ISSUE_DESP.js` 文件读取问题描述

## 使用方法

### 基本命令格式

```bash
mini-extra openharmony-single \
    --subset dataset1 \
    --split test \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i openharmony__vendor_telink-0
```

### 参数说明

| 参数 | 说明 | 默认值 |
|-----|------|--------|
| `--subset` | 数据集路径 | `dataset1` |
| `--split` | 数据集分割 (test/train/dev) | `test` |
| `--model` / `-m` | 使用的模型 | 配置文件中指定 |
| `--instance` / `-i` | 实例 ID 或索引 | `0` |
| `--config` / `-c` | 配置文件路径 | `config/extra/openharmony.yaml` |
| `--output` / `-o` | 输出轨迹文件路径 | `~/.config/mini-swe-agent/last_openharmony_single_run.traj.json` |

### 实例 ID 格式

```
openharmony__<项目名>-<issue_id>
```

例如：
- `openharmony__vendor_telink-0` - vendor_telink 项目的第 0 号 issue
- `openharmony__vendor_telink-5` - vendor_telink 项目的第 5 号 issue

### 使用索引而非 ID

也可以使用数字索引：

```bash
mini-extra openharmony-single -i 0  # 第一个 issue
mini-extra openharmony-single -i 1  # 第二个 issue
```

## 数据集结构

```
dataset1/
└── openharmony/
    └── test/
        └── vendor_telink/
            ├── ISSUE_DESP.js          # Issue 描述文件
            ├── ota_demo/              # 项目代码
            ├── led_demo/
            └── ...
```

### ISSUE_DESP.js 格式

```json
[
  {
    "index": 1,
    "问题编号": "68f2a8798da0d51b47cea54e",
    "缺陷id": "aec2db486699c7c35b0f03eafc574230",
    "缺陷描述": "Do not directly call system assert, please use macro defined ASSERT instead.",
    "规范": "G.AST.01 断言必须使用宏定义，且只能在调试版本中生效【C】",
    "代码行数": 201,
    "文件路径": "ble_demo/b91_gatt_sample/app.c",
    "问题级别": "严重",
    "问题状态(0:未解决，1：已解决 2：已忽略)": 0,
    "创建时间": "    assert(status == BLE_SUCCESS);",
    "代码片段": null
  }
]
```

**注意**：
- `index` 字段从 1 开始（而非 0）
- 列表索引从 0 开始，所以列表第一个元素（索引0）的 `index` 字段为 1
- 实例 ID 基于列表索引：`openharmony__vendor_telink-0`, `openharmony__vendor_telink-1`, etc.

## 与 SWE-bench 的对比

| 特性 | SWE-bench | OpenHarmony |
|-----|-----------|-------------|
| **执行环境** | Docker 容器 | 本地文件系统 |
| **数据来源** | HuggingFace datasets | 本地 JSON 文件 |
| **问题类型** | 功能 bug | 代码质量/规范 |
| **验证方式** | 运行测试 | **静态分析** |
| **修改内容** | 可能需要测试 | **仅修改源码** |

## 配置特点

`config/extra/openharmony.yaml` 的关键特性：

### 1. 强调静态分析

```yaml
system_template: |
  You are a code quality expert that performs STATIC CODE ANALYSIS ONLY.
  DO NOT run or execute the code.
  DO NOT create test scripts or verification scripts.
```

### 2. 禁用动态验证步骤

工作流程修改为：
1. 读取和分析代码文件 ✅
2. 定位问题行 ✅
3. 修改源代码 ✅
4. **~~创建测试脚本~~** ❌（已移除）
5. **~~运行验证~~** ❌（已移除）
6. 提交工作 ✅

### 3. 限制资源消耗

```yaml
step_limit: 100      # 最多 100 步（vs SWE-bench 的 250 步）
cost_limit: 2.0      # 最多 $2（vs SWE-bench 的 $3）
timeout: 30          # 命令超时 30 秒（vs 60 秒）
```

## 示例使用场景

### 场景 1：修复 assert 宏使用问题

```bash
# Issue: "不要直接调用系统 assert，请使用宏定义的 ASSERT"
# 规则: G.AST.01 断言必须使用宏定义，且只能在调试版本中生效【C】

mini-extra openharmony-single \
    --model anthropic/claude-sonnet-4-5-20250929 \
    -i openharmony__vendor_telink-1
```

Agent 会：
1. 读取 `ble_demo/b91_gatt_sample/app.c` 文件
2. 定位第 197 行：`assert(status == BLE_SUCCESS);`
3. 使用 `sed` 替换为宏定义的 ASSERT：
   ```c
   ASSERT(status == BLE_SUCCESS);
   ```
4. 提交修改

### 场景 2：批量处理（未来扩展）

当前版本只支持单个实例，未来可以参考 `swebench.py` 实现批量处理：

```bash
# 未来可能的命令（需要额外开发）
mini-extra openharmony \
    --subset dataset1 \
    --split test \
    --model anthropic/claude-sonnet-4-5-20250929
```

## 实现细节

### 文件结构

```
src/minisweagent/
├── run/
│   ├── mini_extra.py                      # ✅ 已修改：注册新命令
│   └── extra/
│       └── openharmony_single.py          # ✅ 新增：主逻辑
└── config/
    └── extra/
        └── openharmony.yaml               # ✅ 新增：配置文件
```

### 核心逻辑

1. **数据加载**（`load_openharmony_dataset`）：
   - 扫描 `dataset1/openharmony/{split}/` 目录
   - 读取每个项目的 `ISSUE_DESP.js`
   - 生成实例字典

2. **问题格式化**（`format_openharmony_issue`）：
   - 将 JSON 格式转换为自然语言描述
   - 包含文件路径、规则、问题行等信息

3. **执行环境**：
   - 使用 `LocalEnvironment`（非 Docker）
   - 工作目录设置为项目路径

## 测试结果

✅ 命令注册成功
✅ 帮助信息正确显示
✅ 数据集加载正常（107 个 issues）
✅ 实例 ID 格式正确（openharmony__vendor_telink-0 到 -106）
✅ 配置文件语法正确
✅ 真实数据格式适配成功（支持中文字段名）
✅ 数字索引和实例 ID 两种方式都正常工作
✅ 目标文件路径正确且文件存在

## 未来改进方向

1. **批量处理**：实现 `openharmony` 命令（类似 `swebench`）
2. **更多数据集**：支持其他 OpenHarmony 项目
3. **规则库**：集成完整的编码规范说明
4. **评估指标**：自动验证修复是否符合规则
5. **多语言支持**：扩展到 Java、Python 等

## 故障排查

### 问题：找不到 ISSUE_DESP.js

**解决**：确保数据集结构正确：
```bash
ls -la dataset1/openharmony/test/vendor_telink/ISSUE_DESP.js
```

### 问题：实例 ID 不存在

**解决**：查看可用实例：
```bash
python -c "
from minisweagent.run.extra.openharmony_single import load_openharmony_dataset
instances = load_openharmony_dataset('dataset1', 'test')
print(list(instances.keys())[:10])
"
```

### 问题：模型 API 错误

**解决**：配置 API 密钥：
```bash
mini-extra config set ANTHROPIC_API_KEY your-api-key-here
```

## 总结

通过这次集成，我们成功实现了：
- ✅ 保留原有功能（增量式修改）
- ✅ 添加 OpenHarmony 支持
- ✅ 短路动态检查（静态分析优先）
- ✅ 与现有架构完美集成

使用方式与 `swebench-single` 高度一致，学习成本低！


