# OpenHarmony 数据格式适配说明

## 问题发现

初始实现时基于假设的英文数据格式，但实际 `ISSUE_DESP.js` 文件使用的是**中文字段名**和不同的数据结构。

## 数据格式差异

### 假设的格式（初版）
```json
{
  "id": 0,
  "issue_file": "...",
  "rule_id": "...",
  "rule_summary": "...",
  "description": "...",
  "problem_lines": [...]
}
```

### 实际格式（真实）
```json
{
  "index": 1,
  "问题编号": "68f2a8798da0d51b47cea54e",
  "缺陷id": "aec2db486699c7c35b0f03eafc574230",
  "缺陷描述": "Do not directly call system assert...",
  "规范": "G.AST.01 断言必须使用宏定义...",
  "代码行数": 201,
  "文件路径": "ble_demo/b91_gatt_sample/app.c",
  "问题级别": "严重",
  "问题状态(0:未解决，1：已解决 2：已忽略)": 0,
  "创建时间": "    assert(status == BLE_SUCCESS);",
  "代码片段": null
}
```

## 关键差异点

| 概念 | 假设 | 实际 |
|-----|------|------|
| **ID 字段** | `id` (0-based) | `index` (1-based) |
| **文件路径** | `issue_file` | `文件路径` |
| **规则** | `rule_id` + `rule_summary` | `规范`（合并的） |
| **描述** | `description` | `缺陷描述` |
| **问题位置** | `problem_lines[]` 数组 | `代码行数` + `创建时间`（单个） |
| **严重程度** | `error_level` | `问题级别` |

## 适配修改

### 1. 数据加载逻辑 (`load_openharmony_dataset`)

**修改前**：
```python
for issue in issues:
    instance_id = f"openharmony__{project_name}-{issue['id']}"
    instances[instance_id] = {
        "issue_file": issue["issue_file"],
        "rule_id": issue["rule_id"],
        ...
    }
```

**修改后**：
```python
for list_index, issue in enumerate(issues):
    instance_id = f"openharmony__{project_name}-{list_index}"
    instances[instance_id] = {
        "list_index": list_index,  # 0-based
        "issue_index": issue.get("index", list_index + 1),  # 1-based
        "issue_file": issue.get("文件路径", issue.get("issue_file", "")),
        "rule_id": issue.get("规范", issue.get("rule_id", "")),
        "description": issue.get("缺陷描述", issue.get("description", "")),
        "line_number": issue.get("代码行数", 0),
        "code_content": issue.get("创建时间", ""),
        ...
    }
```

**关键点**：
- 使用 `enumerate(issues)` 获取列表索引（0-based）
- 实例 ID 基于列表索引，确保连续性
- 使用 `.get()` 方法支持中英文字段名的回退
- 保存原始的 `index` 字段用于追溯

### 2. 任务格式化 (`format_openharmony_issue`)

**修改前**：
```python
problem_lines_str = "\n".join([
    f"Line {line['line_no']}: {line['code']}"
    for line in instance["problem_lines"]
])

return f"""...
Problem Lines:
{problem_lines_str}
..."""
```

**修改后**：
```python
return f"""...
Problem Location:
Line {instance['line_number']}: {instance['code_content']}
..."""
```

**关键点**：
- 从数组格式改为单个行号+代码
- 简化了问题描述，更聚焦

## 实例 ID 设计

### 决策：使用列表索引而非原始 index 字段

**原因**：
1. **连续性**：列表索引从 0 开始连续递增，便于管理
2. **一致性**：与数字索引参数 `-i 1` 的语义一致
3. **稳定性**：不依赖数据文件中的 index 字段是否正确

**映射关系**：
```
列表位置 → 列表索引 → index 字段 → 实例 ID
第1个元素 → 0 → 1 → openharmony__vendor_telink-0
第2个元素 → 1 → 2 → openharmony__vendor_telink-1
第3个元素 → 2 → 3 → openharmony__vendor_telink-2
```

## 验证结果

```bash
$ python test_load.py
✅ 成功加载 107 个实例
✅ 找到实例: openharmony__vendor_telink-1
  - List Index: 1
  - Issue Index: 2
  - File: ble_demo/b91_gatt_sample/app.c
  - Line: 197
  - Severity: 严重
```

## 向后兼容性

代码使用 `.get()` 方法同时支持：
- 中文字段名（真实数据）
- 英文字段名（假设格式）

示例：
```python
"issue_file": issue.get("文件路径", issue.get("issue_file", ""))
```

这确保了：
1. 如果数据使用中文字段，优先使用
2. 如果数据使用英文字段，作为备选
3. 如果都没有，使用默认值（空字符串）

## 特殊字段处理

### "创建时间" 字段存储代码内容

这是一个命名与实际内容不符的情况：
```json
"创建时间": "    assert(status == BLE_SUCCESS);"
```

实际上这个字段存储的是**问题代码的内容**，而非时间戳。

在代码中我们将其映射为 `code_content`：
```python
"code_content": issue.get("创建时间", issue.get("code", "")),
```

## 数据统计

从 vendor_telink 项目加载的数据：
- **总问题数**：107 个
- **问题类型**：
  - 断言使用 (G.AST.01)
  - 循环安全 (G.CTL.03)
  - 内存管理 (G.MEM.01)
  - 变量声明 (G.FMT.04-CPP)
  - 等等
- **严重程度**：严重、一般、建议
- **状态**：大部分为未解决（0）

## 命令使用示例

### 使用实例 ID
```bash
mini-extra openharmony-single -i openharmony__vendor_telink-1
```

### 使用数字索引
```bash
mini-extra openharmony-single -i 1
```

两种方式都会选择列表中的第二个元素（index=2 的问题）。

## 总结

通过灵活的字段映射和回退机制，成功适配了真实的中文数据格式，同时保持了代码的健壮性和可扩展性。实例 ID 设计基于列表索引而非原始 index 字段，确保了连续性和易用性。


