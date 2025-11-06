# OpenHarmony 输出目录结构说明

## ✅ 已修复的架构

### 新的目录结构（2025-11-05 更新）

```
dataset1/openharmony/
├── test/                          # 原始项目（不会被修改）
│   └── vendor_telink/
│       ├── ble_demo/
│       ├── led_demo/
│       └── ISSUE_DESP.js
│
└── test_result/                   # 工作目录（包含修复后的文件）
    └── vendor_telink/            # ✅ 项目名称层级
        └── 20251105_152714_full/  # 时间戳命名的工作目录
            ├── ble_demo/          # 修复后的项目文件
            ├── led_demo/
            ├── ISSUE_DESP.js
            ├── openharmony__vendor_telink-0.traj.json  # ✅ 新增：trajectory 文件
            ├── openharmony__vendor_telink-1.traj.json
            └── ...                # 每个 issue 的 trajectory

openharmony_full_results_TIMESTAMP/   # 运行结果汇总（可选，用于查看）
├── results.json                      # 运行结果摘要
├── minisweagent.log                 # 完整日志
├── exit_statuses_*.yaml             # 退出状态
└── openharmony__vendor_telink-0/    # 每个问题的详细信息
    └── *.traj.json                  # Agent 操作历史（备份）
```

### 关键改进

1. **✅ 项目名称层级**: `test_result` 现在先创建项目文件夹（如 `vendor_telink`），然后再创建时间戳文件夹
2. **✅ Trajectory 文件**: 现在 trajectory 文件也保存在工作目录中，和修复后的项目文件在一起
3. **双重保存**: Trajectory 文件会保存两份：
   - 一份在 `test_result/项目名/时间戳/` 中（和修复后的项目在一起）
   - 一份在 `openharmony_full_results_*/` 中（用于结果汇总）

### 使用建议

1. **查看修复后的项目**：
   ```bash
   cd dataset1/openharmony/test_result/vendor_telink/最新时间戳/
   ```
   在这里可以找到：
   - 修复后的所有项目文件
   - 每个 issue 对应的 trajectory 文件

2. **查看运行结果汇总**：
   ```bash
   cd openharmony_full_results_最新时间戳/
   cat results.json
   cat minisweagent.log
   ```

3. **对比修复前后的差异**：
   ```bash
   diff -r dataset1/openharmony/test/vendor_telink/ \
           dataset1/openharmony/test_result/vendor_telink/最新时间戳/ \
           | grep "^diff" | head -20
   ```

## 修改内容

### 修改的文件

1. **`src/minisweagent/run/extra/openharmony_single.py`**
   - 修改 `prepare_working_directory()`: 添加项目名称层级
   - 修改 `main()`: 保存 trajectory 到工作目录

2. **`src/minisweagent/run/extra/openharmony.py`**
   - 修改 `process_instance()`: 保存 trajectory 到工作目录

3. **`src/minisweagent/run/extra/openharmony_batch.py`**
   - 修改 `process_instance()`: 保存 trajectory 到工作目录

### 代码变更摘要

```python
# 现在 trajectory 会保存两份：
# 1. 输出目录（用于结果汇总）
save_traj(agent, instance_dir / f"{instance_id}.traj.json", ...)

# 2. 工作目录（和修复后的项目文件在一起）✅ 新增
working_traj_path = Path(working_path) / f"{instance_id}.traj.json"
save_traj(agent, working_traj_path, ...)
```

## 验证新结构

运行一个简单测试来验证新结构：

```bash
# 运行单个实例测试
cd /mnt/sdc/wys/swebench/mini-swe-agent
mini-extra openharmony-single -i 0

# 检查新的目录结构
ls -la dataset1/openharmony/test_result/

# 应该看到：
# dataset1/openharmony/test_result/
#   └── vendor_telink/
#       └── 20251105_HHMMSS_single_issue0/
#           ├── [项目文件...]
#           └── openharmony__vendor_telink-0.traj.json  ← 新增
```

