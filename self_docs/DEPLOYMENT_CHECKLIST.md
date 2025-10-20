# 部署清单

## 📦 项目文件清单

### 必需文件

```
mini-swe-agent/
├── src/                              # ✅ 源代码
├── config/                           # ✅ 配置文件
│   ├── local/
│   │   ├── .env                     # ✅ API Keys（需要配置）
│   │   ├── .env.example             # ✅ 配置示例
│   │   └── model_registry.json      # ✅ 模型价格
│   └── extra/
│       └── openharmony.yaml         # ✅ OpenHarmony 配置
├── dataset1/                        # ✅ 数据集
│   └── openharmony/
│       └── test/
│           └── vendor_telink/       # ✅ 原始项目
├── run_local.sh                     # ✅ 本地启动脚本
├── pyproject.toml                   # ✅ 项目依赖
├── README.md                        # ✅ 项目说明
└── LOCAL_DEPLOYMENT_GUIDE.md        # ✅ 部署指南
```

### 可选文件（不需要部署）

```
❌ dataset1/openharmony/test_result/  # 测试结果（不需要）
❌ openharmony_*_results_*/           # 运行结果（不需要）
❌ *.zip                               # 打包文件（不需要）
❌ .git/                               # Git 历史（可选）
❌ __pycache__/                        # Python 缓存（不需要）
```

## 🚀 快速部署流程

### 步骤 1：打包项目

```bash
# 在源服务器上
cd /mnt/sdc/wys/swebench/mini-swe-agent

# 打包（排除不需要的文件）
tar -czf mini-swe-agent-deploy.tar.gz \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='dataset1/openharmony/test_result' \
    --exclude='openharmony_*_results_*' \
    --exclude='*.zip' \
    --exclude='.pytest_cache' \
    src/ config/ dataset1/ run_local.sh pyproject.toml README.md *.md
```

### 步骤 2：传输到目标服务器

```bash
# 方法 1: SCP
scp mini-swe-agent-deploy.tar.gz user@target-server:/home/user/

# 方法 2: SFTP
sftp user@target-server
put mini-swe-agent-deploy.tar.gz

# 方法 3: Git（如果使用版本控制）
git push origin main
# 在目标服务器上
git clone <your-repo>
```

### 步骤 3：在目标服务器上安装

```bash
# 登录目标服务器
ssh user@target-server

# 解压
tar -xzf mini-swe-agent-deploy.tar.gz
cd mini-swe-agent

# 安装依赖
pip install -e .
```

### 步骤 4：配置 API Keys

```bash
# 检查配置示例
cat config/local/.env.example

# 编辑配置文件，填入真实的 API Keys
nano config/local/.env
```

### 步骤 5：测试运行

```bash
# 测试单个实例
./run_local.sh openharmony-single \
    --model openai/deepseek-v3.2-exp \
    -i 0

# 查看输出
ls -la dataset1/openharmony/test_result/
```

## ✅ 验证清单

部署完成后，验证以下项目：

- [ ] 项目文件完整
  ```bash
  ls -la src/minisweagent/run/extra/openharmony*.py
  ```

- [ ] 配置文件存在
  ```bash
  ls -la config/local/
  ```

- [ ] API Keys 已配置
  ```bash
  grep -v "^#" config/local/.env | grep "API_KEY"
  ```

- [ ] 依赖已安装
  ```bash
  python -c "import minisweagent; print(minisweagent.__version__)"
  ```

- [ ] 启动脚本可执行
  ```bash
  ./run_local.sh openharmony-single --help
  ```

- [ ] 配置路径正确
  ```bash
  ./run_local.sh openharmony-single --help | grep "Loading global config"
  # 应该显示项目本地路径，而非 /root/.config/
  ```

## 🔐 安全建议

### 1. 保护 API Keys

```bash
# 设置正确的文件权限
chmod 600 config/local/.env
chmod 644 config/local/.env.example
```

### 2. 不要提交敏感信息

```bash
# 确认 .gitignore 包含
grep "config/local/.env" .gitignore
```

### 3. 使用环境变量（生产环境）

```bash
# 在生产服务器上，可以使用环境变量而非文件
export OPENAI_API_KEY="your-key"
export OPENAI_API_BASE="https://api.modelarts-maas.com/v1"

./run_local.sh openharmony -w 5
```

## 📋 部署前后对比

### 部署前（依赖用户目录）

```bash
运行: mini-extra openharmony -w 5
读取: /root/.config/mini-swe-agent/.env
问题: ❌ 部署到新服务器需要重新配置
```

### 部署后（使用项目本地配置）

```bash
运行: ./run_local.sh openharmony -w 5
读取: /path/to/project/config/local/.env
优点: ✅ 配置跟随项目，直接可用
```

## 🎯 团队协作流程

### 1. 项目管理员

```bash
# 创建配置示例
cp config/local/.env config/local/.env.example
# 在 .env.example 中移除真实 API Keys

# 提交到 Git
git add config/local/.env.example
git commit -m "Add config example"
```

### 2. 团队成员

```bash
# 克隆项目
git clone <repo-url>
cd mini-swe-agent

# 创建自己的配置
cp config/local/.env.example config/local/.env

# 编辑填入 API Keys
nano config/local/.env

# 使用本地配置运行
./run_local.sh openharmony -w 5
```

## 📊 文件大小参考

```bash
配置文件:        ~1 KB
模型注册:        ~1 KB
源代码:          ~100 KB
数据集(test):    ~1 MB
完整项目:        ~2 MB (不含 .git)
```

## 🆘 故障排查

### 问题: 找不到配置文件

```bash
# 检查文件是否存在
ls -la config/local/.env

# 如果不存在，从示例创建
cp config/local/.env.example config/local/.env
```

### 问题: 权限错误

```bash
# 设置正确权限
chmod +x run_local.sh
chmod 600 config/local/.env
```

### 问题: 路径错误

```bash
# 确保在项目根目录运行
cd /path/to/mini-swe-agent
pwd  # 应该显示项目根目录
./run_local.sh openharmony-single -i 0
```

---

**✅ 使用此清单确保部署顺利完成！**
