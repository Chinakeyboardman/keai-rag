# 🧪 测试指南

## 快速开始

### 1. 确保虚拟环境已激活

```bash
cd /Users/chenjiawei/Study/ai/zhihu/13-Embeddings和向量数据库/china-pdf-rag
source venv/bin/activate
```

### 2. 运行测试

#### 基础测试命令

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_config.py -v

# 运行特定测试函数
pytest tests/test_config.py::test_settings_loaded -v
```

#### 代码覆盖率测试

```bash
# 运行测试并显示覆盖率（推荐）
pytest tests/ --cov=src --cov=config -v

# 生成 HTML 覆盖率报告
pytest tests/ --cov=src --cov=config --cov-report=html

# 查看 HTML 报告
open htmlcov/index.html
```

#### 跳过慢速测试

```bash
# 只运行快速测试（跳过向量存储测试）
pytest tests/ -v -k "not vector_store"
```

---

## 📊 当前测试状态

### ✅ 可用的测试

| 测试文件 | 测试数量 | 状态 | 说明 |
|---------|---------|------|------|
| `test_config.py` | 7 | ✅ 全部通过 | 配置模块测试 |
| `test_processors.py` | 5 | ✅ 全部通过 | 文档处理器测试 |
| `test_api_schemas.py` | 8 | ✅ 全部通过 | API 数据模型测试 |
| `test_vector_store.py` | 7 | ⚠️ 部分失败 | 向量存储测试（需要修复） |

### 推荐测试命令

```bash
# 运行稳定的测试（20个测试，100%通过）
pytest tests/ -v -k "not vector_store"

# 运行并查看覆盖率
pytest tests/ -k "not vector_store" --cov=src --cov=config --cov-report=term-missing
```

---

## ❓ 常见问题

### Q1: 为什么命令无法执行？

**A:** 最常见的原因：

1. **虚拟环境未激活**
   ```bash
   # 检查是否激活
   which pytest
   # 应该显示: /path/to/china-pdf-rag/venv/bin/pytest
   
   # 如果不是，激活虚拟环境
   source venv/bin/activate
   ```

2. **不在项目目录**
   ```bash
   # 确保在项目根目录
   cd /Users/chenjiawei/Study/ai/zhihu/13-Embeddings和向量数据库/china-pdf-rag
   ```

3. **pytest 未安装**
   ```bash
   # 安装 pytest
   pip install pytest pytest-cov
   ```

### Q2: 看到很多警告信息

**A:** 这些警告是正常的，不影响测试结果：
- `NotOpenSSLWarning` - SSL 版本警告，可以忽略
- `DeprecationWarning` - 依赖库的弃用警告，可以忽略

### Q3: 测试失败怎么办？

**A:** 使用以下命令查看详细错误：

```bash
# 显示详细错误信息
pytest tests/test_config.py -v --tb=long

# 只运行失败的测试
pytest tests/ --lf -v
```

### Q4: 如何在终端直接运行？

**A:** 在您自己的终端中：

```bash
# 1. 打开终端（Terminal.app 或 iTerm2）

# 2. 进入项目目录
cd /Users/chenjiawei/Study/ai/zhihu/13-Embeddings和向量数据库/china-pdf-rag

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 运行测试
pytest tests/ -v

# 5. 运行覆盖率测试
pytest tests/ --cov=src --cov=config --cov-report=html

# 6. 查看 HTML 报告
open htmlcov/index.html
```

---

## 🎯 测试最佳实践

### 1. 开发前运行测试

```bash
# 确保所有测试通过
pytest tests/ -v -k "not vector_store"
```

### 2. 修改代码后运行相关测试

```bash
# 修改了配置相关代码
pytest tests/test_config.py -v

# 修改了处理器相关代码
pytest tests/test_processors.py -v
```

### 3. 提交代码前运行完整测试

```bash
# 运行所有测试并生成覆盖率报告
pytest tests/ -v --cov=src --cov=config --cov-report=term-missing
```

---

## 📈 测试覆盖率

### 查看覆盖率

```bash
# 在终端显示覆盖率
pytest tests/ --cov=src --cov=config --cov-report=term

# 显示未覆盖的行
pytest tests/ --cov=src --cov=config --cov-report=term-missing

# 生成 HTML 报告（推荐）
pytest tests/ --cov=src --cov=config --cov-report=html
open htmlcov/index.html
```

### 目标覆盖率

- **配置模块**: 90%+
- **处理器模块**: 80%+
- **API 模块**: 70%+
- **核心模块**: 80%+

---

## 🔧 故障排除

### 问题：`ModuleNotFoundError`

```bash
# 解决方案：安装缺失的依赖
pip install -r requirements.txt
```

### 问题：`pytest: command not found`

```bash
# 解决方案：安装 pytest
pip install pytest pytest-cov pytest-asyncio
```

### 问题：测试运行很慢

```bash
# 解决方案：跳过慢速测试
pytest tests/ -v -k "not vector_store" -x
# -x 参数：遇到第一个失败就停止
```

### 问题：权限错误

```bash
# 解决方案：检查文件权限
chmod +x venv/bin/pytest
```

---

## 📝 添加新测试

### 1. 创建测试文件

```python
# tests/test_new_feature.py
import pytest

def test_new_feature():
    """测试新功能"""
    assert True
```

### 2. 运行新测试

```bash
pytest tests/test_new_feature.py -v
```

### 3. 添加到测试套件

测试会自动被 pytest 发现并运行。

---

## 🚀 持续集成

如果要在 CI/CD 中运行测试：

```bash
# GitHub Actions 示例
pytest tests/ -v --cov=src --cov=config --cov-report=xml
```

---

## 📚 更多资源

- [pytest 官方文档](https://docs.pytest.org/)
- [pytest-cov 文档](https://pytest-cov.readthedocs.io/)
- [Python 测试最佳实践](https://docs.python-guide.org/writing/tests/)

---

**提示**: 如果您在终端中无法执行命令，请确保：
1. ✅ 虚拟环境已激活（`source venv/bin/activate`）
2. ✅ 在项目根目录（`pwd` 应该显示项目路径）
3. ✅ pytest 已安装（`which pytest` 应该有输出）

如果以上都确认无误，命令应该可以正常执行！

