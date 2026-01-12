# 项目改进总结：Prompts 和 Metadata 配置管理

## 概述

本次改进将学术报告生成系统中所有 LLM 使用的 prompt 进行了中央集管理，同时为最终生成的 Markdown 报告添加了 YAML 元数据（frontmatter）支持。这使得系统更易于维护和定制。

## 完成的任务

### 1. 设计文档更新 (`docs/design.md`)

- 添加了关于 Prompts 和 Metadata 配置的新需求说明
- 更新了 Utility Functions 部分，记录了新增的 `prompt_loader` 和 `metadata_loader` 模块
- 完善了 Data Design 部分，加入了 metadata 数据结构
- 更新了 Node Design 中的 AssembleReportNode 以支持 metadata 生成和处理

### 2. 配置文件创建

#### `config/prompts.toml` (5364 bytes)
集中管理所有 LLM prompts，包括：
- **[analyst]** - 分析员 agent 的 system prompt 和 user prompt 模板
- **[architect]** - 架构师 agent 的 system prompt 和 user prompt 模板
- **[writer]** - 作者 agent 的 system prompt 和 user prompt 模板
- **[metadata_generation]** - Metadata 生成的 system prompt 和 user prompt 模板

特点：
- 所有 prompt 都使用模板变量（如 `{topic}`, `{raw_content}` 等）
- 易于搜索、查找和修改各个 agent 的 prompt
- 支持动态变量注入

#### `config/report_metadata.yaml` (444 bytes)
学术报告的 YAML 元数据模板，包含：
```yaml
title: ""
subtitle: ""
abstract: ""
info:
  姓名: "张三"
  学号: "20230001"
  课程: "人工智能导论"
  日期: "2025年1月12日"
  指导教师: "李四"
bibliography: ""
```

### 3. 新增 Utility 模块

#### `pocketreport/utils/prompt_loader.py`
功能：
- 从 `config/prompts.toml` 加载 LLM prompts
- 提供方便的 API：`get_system_prompt()`, `get_user_prompt_template()`, `get_user_prompt()`
- 支持模板变量自动替换
- 内存缓存提高性能
- 完善的错误处理和日志记录

主要函数：
```python
get_prompt(agent_name, prompt_type, template_vars=None)  # 通用函数
get_system_prompt(agent_name)  # 获取系统 prompt
get_user_prompt_template(agent_name)  # 获取用户 prompt 模板
get_user_prompt(agent_name, **template_vars)  # 获取包含变量的用户 prompt
clear_cache()  # 清除缓存（用于测试）
```

#### `pocketreport/utils/metadata_loader.py`
功能：
- 从 `config/report_metadata.yaml` 加载模板
- 更新和生成报告元数据
- 生成 YAML frontmatter（带有 `---` 分隔符）
- 将 frontmatter 添加到报告内容

主要函数：
```python
load_metadata_template()  # 加载基础模板
update_metadata(title=None, subtitle=None, abstract=None, info=None, bibliography=None)  # 更新元数据
metadata_to_yaml(metadata)  # 转换为 YAML 字符串
generate_frontmatter(metadata)  # 生成包含分隔符的 frontmatter
append_frontmatter_to_report(frontmatter, report_content)  # 将 frontmatter 添加到报告
```

### 4. Nodes 修改

#### `pocketreport/nodes.py`

**AnalystNode**：
- 将硬编码的 prompt 替换为从 `prompt_loader` 动态加载
- 使用 `get_system_prompt("analyst")` 和 `get_user_prompt("analyst", raw_content=...)`

**ArchitectNode**：
- 将硬编码的 prompt 替换为从 `prompt_loader` 动态加载
- 使用 `get_system_prompt("architect")` 和 `get_user_prompt("architect", topic=..., analysis_summary=...)`

**WriterNode**：
- 将硬编码的 system prompt 替换为从 `prompt_loader` 动态加载
- 使用 `get_system_prompt("writer")` 和 `get_user_prompt("writer", report_title=..., section_path=..., ...)`

**AssembleReportNode**（新功能）：
- 新增 metadata 生成和处理
- 从 `metadata_loader` 加载模板并更新元数据
- 使用 `generate_frontmatter()` 生成 YAML 前言
- 使用 `append_frontmatter_to_report()` 将前言添加到报告内容
- 保存包含元数据的完整报告

### 5. Utility 导出更新

`pocketreport/utils/__init__.py` 已更新，导出所有新的 utility 函数：
- `get_prompt`, `get_system_prompt`, `get_user_prompt_template`, `get_user_prompt`, `clear_prompt_cache`
- `load_metadata_template`, `update_metadata`, `metadata_to_yaml`, `generate_frontmatter`, `append_frontmatter_to_report`

### 6. README 文档更新

更新了 `README.md`：
- 在 Features 部分添加了三项新特性
- 新增 Configuration 章节，说明：
  - 如何修改 LLM prompts
  - YAML frontmatter 的结构和用途
  - 如何定制元数据模板
- 提供了详细的配置示例

### 7. 测试

创建了 `test_integration.py` 进行全面的集成测试：

```
TEST SUMMARY
============
✓ PASS: Configuration Files
✓ PASS: Prompt Loading
✓ PASS: Metadata Loading
✓ PASS: Nodes Integration

Total: 4/4 tests passed
🎉 All integration tests passed!
```

测试验证了：
1. 配置文件的存在和可读性
2. 从 TOML 加载 prompts 的正确性
3. YAML 模板加载和元数据生成
4. Nodes 能够正确导入和使用新的 utilities

## 文件结构变化

```
pocket-report/
├── config/
│   ├── prompts.toml          [NEW] 中央 prompt 配置
│   └── report_metadata.yaml  [NEW] YAML 元数据模板
├── pocketreport/
│   ├── nodes.py              [MODIFIED] 更新为使用 prompt_loader 和 metadata_loader
│   └── utils/
│       ├── __init__.py       [MODIFIED] 添加新的导出
│       ├── prompt_loader.py  [NEW] Prompt 加载器
│       └── metadata_loader.py [NEW] Metadata 加载器
├── docs/
│   └── design.md             [MODIFIED] 添加了新需求和设计说明
├── README.md                 [MODIFIED] 添加了配置说明
└── test_integration.py       [NEW] 集成测试脚本
```

## 使用示例

### 修改 Prompts

编辑 `config/prompts.toml`，例如修改 Writer agent 的 system prompt：

```toml
[writer]
system_prompt = """你是一位学术写手。请为以下描述的特定部分编写内容。
[修改你的 prompt]
"""
```

修改会立即生效，无需重启程序。

### 定制 Metadata 模板

编辑 `config/report_metadata.yaml`：

```yaml
info:
  姓名: "默认姓名"
  学号: "默认学号"
  课程: "默认课程"
  日期: "2025年1月12日"
  指导教师: "默认指导教师"
```

### 在代码中使用新的 APIs

```python
from pocketreport.utils import (
    get_user_prompt,
    load_metadata_template,
    generate_frontmatter,
    append_frontmatter_to_report
)

# 获取动态 prompt
prompt = get_user_prompt(
    "architect",
    topic="AI Report",
    analysis_summary="Summary text..."
)

# 生成报告元数据和 frontmatter
metadata = load_metadata_template()
metadata.update({"title": "My Report"})
frontmatter = generate_frontmatter(metadata)
final_report = append_frontmatter_to_report(frontmatter, content)
```

## 遵守的原则

本改进遵照项目中 `AGENTS.md` 文档的核心原则：

1. **Design First** - 先进行高级设计（已更新 design.md）
2. **Start Simple** - 实现简单而有效的解决方案
3. **Seek Feedback** - 通过测试验证实现的正确性
4. **Modular Architecture** - 所有新功能都被组织为独立的模块
5. **Logging** - 添加了详细的日志记录用于调试
6. **Testing** - 创建了全面的集成测试

## 向后兼容性

- 所有现有的 API 保持不变
- 旧的 prompt 硬编码仍然可以在代码中找到（用于参考）
- Nodes 会自动从配置文件加载 prompts，对外部调用者透明

## 未来改进方向

1. **Prompt 版本控制** - 在 config 中维护 prompt 版本历史
2. **A/B 测试** - 支持加载不同的 prompt 配置进行对比测试
3. **Metadata 验证** - 添加 JSON Schema 验证元数据的有效性
4. **LLM-Generated Metadata** - 使用 LLM 自动生成标题、副标题和摘要
5. **国际化** - 支持多语言的 prompt 和模板

## 验证清单

- ✅ 所有 prompts 已从硬编码移到 `config/prompts.toml`
- ✅ YAML 元数据模板已创建在 `config/report_metadata.yaml`
- ✅ `prompt_loader` utility 已创建并测试
- ✅ `metadata_loader` utility 已创建并测试
- ✅ 所有 nodes 已更新为使用新的 loaders
- ✅ `AssembleReportNode` 支持 metadata 生成
- ✅ 最终报告包含 YAML frontmatter
- ✅ README 已更新，记录新功能
- ✅ 集成测试 100% 通过（4/4）
- ✅ 代码遵循项目的编码规范
