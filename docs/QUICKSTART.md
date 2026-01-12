# Prompts 和 Metadata 配置快速参考

## 快速开始

### 1. 修改 LLM Prompts

编辑 `config/prompts.toml` 文件：

```bash
# 编辑 Analyst agent 的 system prompt
vim config/prompts.toml
# 找到 [analyst] 部分，修改 system_prompt
```

可修改的 agent：
- `[analyst]` - 分析材料的 agent
- `[architect]` - 设计大纲的 agent
- `[writer]` - 编写内容的 agent
- `[metadata_generation]` - 生成元数据的 agent

### 2. 定制报告元数据模板

编辑 `config/report_metadata.yaml`：

```yaml
title: ""  # 报告标题（自动生成或手动设置）
subtitle: ""  # 报告副标题
abstract: ""  # 报告摘要
info:
  姓名: "你的名字"  # 学生/作者名字
  学号: "学号"  # 学号
  课程: "课程名"  # 课程名
  日期: "日期"  # 日期
  指导教师: "教师名"  # 指导教师
bibliography: ""  # 参考文献
```

## API 参考

### Prompt Loader

```python
from pocketreport.utils import prompt_loader

# 获取某个 agent 的 system prompt
system_prompt = prompt_loader.get_system_prompt("analyst")

# 获取某个 agent 的 user prompt 模板（包含占位符）
template = prompt_loader.get_user_prompt_template("writer")

# 获取带有变量替换的 user prompt
user_prompt = prompt_loader.get_user_prompt(
    "architect",
    topic="AI Report",
    analysis_summary="..."
)

# 清除缓存（用于测试或重新加载配置）
prompt_loader.clear_cache()
```

### Metadata Loader

```python
from pocketreport.utils import metadata_loader

# 加载基础元数据模板
metadata = metadata_loader.load_metadata_template()

# 更新元数据
metadata = metadata_loader.update_metadata(
    title="我的报告",
    subtitle="副标题",
    abstract="摘要内容",
    info={"姓名": "张三"}
)

# 生成 YAML frontmatter（包含 --- 分隔符）
frontmatter = metadata_loader.generate_frontmatter(metadata)

# 将 frontmatter 添加到报告内容
full_report = metadata_loader.append_frontmatter_to_report(
    frontmatter,
    "# Report Content\n\nThis is the content..."
)
```

## 文件位置

```
项目根目录/
├── config/
│   ├── prompts.toml              # LLM prompts 配置
│   └── report_metadata.yaml      # 元数据模板
└── pocketreport/
    └── utils/
        ├── prompt_loader.py      # Prompt 加载器
        └── metadata_loader.py    # Metadata 加载器
```

## 常见任务

### 任务 1：修改 Writer Agent 的 Prompt

```bash
# 编辑配置文件
nano config/prompts.toml

# 找到 [writer] 部分：
# system_prompt = """..."""
# 修改内容并保存

# 无需重启，下次运行时会自动加载
```

### 任务 2：添加自定义字段到 Metadata

编辑 `config/report_metadata.yaml`，添加新字段：

```yaml
title: ""
subtitle: ""
abstract: ""
info:
  # ... 现有字段 ...
  自定义字段: "值"  # 新字段
bibliography: ""
```

然后在代码中访问：

```python
metadata = load_metadata_template()
custom_value = metadata["info"]["自定义字段"]
```

### 任务 3：在代码中使用动态 Prompts

```python
from pocketreport.utils import get_user_prompt

# 从配置加载 prompt，并进行变量替换
prompt = get_user_prompt(
    "analyst",
    raw_content="Your materials here..."
)

# 使用 prompt 调用 LLM
response = llm_client.complete(system_prompt, prompt)
```

### 任务 4：生成包含元数据的完整报告

```python
from pocketreport.utils import (
    load_metadata_template,
    update_metadata,
    generate_frontmatter,
    append_frontmatter_to_report
)

# 1. 加载模板
metadata = load_metadata_template()

# 2. 更新元数据
metadata = update_metadata(
    title="AI Introduction",
    subtitle="A Comprehensive Study",
    abstract="This report covers...",
    info={"姓名": "Student Name"}
)

# 3. 生成 frontmatter
frontmatter = generate_frontmatter(metadata)

# 4. 组合报告内容和 frontmatter
report_content = "# Chapter 1\n\nContent..."
final_report = append_frontmatter_to_report(frontmatter, report_content)

# 5. 保存最终报告
with open("output/report.md", "w", encoding="utf-8") as f:
    f.write(final_report)
```

## 故障排除

### 问题：找不到 `config/prompts.toml`

**解决方案**：确保配置文件在项目根目录的 `config/` 文件夹中：
```bash
ls -la config/prompts.toml
```

### 问题：Prompt 变量替换失败

**解决方案**：检查提供的变量名是否与模板中的占位符匹配：
```python
# ✓ 正确 - 变量名匹配占位符
get_user_prompt("architect", topic="AI", analysis_summary="...")

# ✗ 错误 - 变量名不匹配
get_user_prompt("architect", title="AI")  # 应该是 topic，不是 title
```

### 问题：元数据中文字符显示问题

**解决方案**：确保文件保存为 UTF-8 编码，并在打开文件时指定编码：
```python
with open("report.md", "w", encoding="utf-8") as f:
    f.write(final_report)
```

## 性能提示

1. **Prompt 缓存**：Prompts 会在第一次加载后缓存在内存中，后续加载很快
2. **元数据模板加载**：每次调用 `load_metadata_template()` 都会从文件读取，如果频繁使用，考虑缓存结果
3. **变量替换**：如果 prompt 模板中有大量占位符，使用 `format()` 时会有轻微开销

## 测试

运行集成测试验证所有功能：

```bash
python test_integration.py
```

运行单个 utility 的测试：

```bash
python pocketreport/utils/prompt_loader.py
python pocketreport/utils/metadata_loader.py
```

## 进阶：创建自定义 Prompt 集

如果需要管理多套 prompts（例如不同语言或不同风格），可以：

1. 创建多个 TOML 文件：`config/prompts_en.toml`, `config/prompts_zh.toml`
2. 修改 `prompt_loader.py` 中的 `_get_config_path()` 来支持选择性加载
3. 在主程序中基于配置选择使用哪个文件

## 参考文档

- 详细设计文档：[docs/design.md](docs/design.md)
- 改进总结：[docs/IMPROVEMENTS.md](docs/IMPROVEMENTS.md)
- 主 README：[README.md](README.md)
- Agentic Coding 指南：[AGENTS.md](AGENTS.md)
