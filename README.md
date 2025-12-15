# Mini-SWE-Agent OpenHarmony 扩展 - 快速开始

## 📦 安装步骤

### 1. 克隆代码

```bash
git clone https://github.com/tripmasterwang/harmocheck.git
cd harmocheck
```

### 2. 创建 Python 环境

```bash
# 使用 conda（推荐）
conda create -n harmonycheck python=3.11 -y
conda activate harmonycheck

# 或使用 venv
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装项目依赖

```bash
pip install -e '.[full]'
```


### 4. 配置 API 密钥

```bash
# 创建配置目录
mkdir -p ~/.config/mini-swe-agent

# 编辑文件，填入你的真实 API 密钥
nano ~/.config/mini-swe-agent/.env  # 或使用其他编辑器

# 键名与config/models.yaml一致，例如:
HUAWEI_API_KEY=<your api>
DEEPSEEK_API_KEY=<your api>
```


### 5. 验证安装

```bash
# 检查命令是否可用
harmocheck --help

# 应该能看到帮助信息，包括：
# -i, --input TEXT     Directory containing code to fix...
# -w, --workers INT    Number of worker threads...
```

## ✅ 完成！

现在你可以使用 `harmocheck` 命令了。

### 示例

为了测试本项目的效果，以OpenHarmony/vendor_telink为案例。
此项目可以克隆在你想克隆的任何位置，本文档只是为了演示，克隆在了项目路径中。

```

cd dataset1/openharmony/test
git clone https://gitee.com/openharmony/vendor_telink.git
cd ../../../

```

运行

```
harmocheck -i ./dataset1/openharmony/test/vendor_telink \
  -d /data2/wangyuansong/project2/harmocheck/dataset1/openharmony/ISSUE_DESP.xlsx \
  -w 5 \
  -m deepseek-v3.2-exp

harmocheck -i ./dataset1/openharmony/test/vendor_telink \
  -d /data2/wangyuansong/project2/harmocheck/dataset1/openharmony/ISSUE_DESP.xlsx \
  -w 5 \
  -m deepseek-reasoner
```

注意，-d参数传入的issue文件是从openharmony数字协作平台直接导出的

### 6. 配置新模型（必须是openAI兼容模型）

在config/models.yaml中配置，目前在
```
models:
  deepseek-v3.2-exp:
    api_base: "https://api.modelarts-maas.com/openai/v1"
    api_key_env: "HUAWEI_API_KEY"
    model_name: "deepseek-v3.2-exp"
  deepseek-reasoner:
    api_base: "https://api.deepseek.com/v1"
    api_key_env: "DEEPSEEK_API_KEY"
    model_name: "deepseek-reasoner"
```