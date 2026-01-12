# Academic Report Writing System

A Python-based multi-agent system for automatically generating academic reports from markdown materials.

## Overview

This system implements a flow-based multi-agent architecture with three specialized agents:

1. **Analyst Agent**: Reads raw markdown materials and generates structured summaries
2. **Architect Agent**: Creates logical report outlines based on topics and analysis
3. **Writer Agent**: Writes academic-quality chapters one by one

The system follows the Pocket Flow framework for orchestration and uses OpenAI-compatible LLM APIs for content generation.

## Features

- **Multi-Agent Architecture**: Three specialized agents working in sequence
- **Flow-Based Orchestration**: Uses Pocket Flow for robust workflow management
- **Structured Outputs**: Pydantic models ensure consistent data structures
- **Multi-Format Input**: Reads markdown files and converts PDF, DOCX, PPTX, Excel, images, audio, HTML, and more to markdown using MarkItDown
- **Hierarchical Outlines**: Supports multi‑level report structures (chapters → sections → subsections)
- **Reusable Outlines**: Save and load outlines as YAML/JSON files for manual editing and reuse
- **Intermediate Results**: All conversion metadata, analysis summaries, and outlines saved to organized output folders
- **Configurable LLM Backend**: Supports any OpenAI-compatible API (GPT-4o, DeepSeek, OpenRouter, etc.)
- **Batch Processing**: Efficiently processes multiple chapters in parallel
- **Conversion Caching**: Caches file conversions to avoid redundant processing
- **Centralized Prompt Management**: All LLM prompts stored in `config/prompts.toml` for easy modification
- **Report Metadata**: Final reports include YAML frontmatter with title, subtitle, abstract, and author information
- **Customizable Metadata Template**: YAML template in `config/report_metadata.yaml` for standard academic report headers

## Installation

### Prerequisites
- Python 3.8+
- Conda (recommended) or pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd pocket-report
```

2. Create and activate conda environment:
```bash
conda create -n report-env python=3.9
conda activate report-env
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create a .env file
echo "LLM_API_KEY=your_api_key_here" > .env
echo "LLM_MODEL=gpt-4o" >> .env  # Optional
echo "LLM_BASE_URL=https://api.openai.com/v1" >> .env  # Optional
```

## Configuration

### LLM Prompts

All prompts used by the three agents (Analyst, Architect, Writer) are centralized in `config/prompts.toml`:

- **Analyst Agent**: `[analyst]` section - Summarizes raw materials into structured knowledge context
- **Architect Agent**: `[architect]` section - Creates hierarchical report outlines based on topics
- **Writer Agent**: `[writer]` section - Writes academic-quality content for each section
- **Metadata Generation**: `[metadata_generation]` section - Generates title, subtitle, and abstract

Each section contains:
- `system_prompt`: The system instruction for the LLM
- `user_prompt_template`: The user prompt template with placeholders (e.g., `{topic}`, `{raw_content}`)

**To modify prompts**, edit `config/prompts.toml` directly. Prompts are loaded dynamically at runtime, so changes take effect immediately.

### Report Metadata Template

Academic reports include YAML frontmatter (header) with metadata. The template is stored in `config/report_metadata.yaml`:

```yaml
title: ""
subtitle: ""
abstract: ""
info:
  姓名: "Zhang San"  # Student/Author name
  学号: "20230001"   # Student ID
  课程: "AI Introduction"  # Course name
  日期: "2025-01-12"  # Date
  指导教师: "Li Si"  # Advisor name
bibliography: ""
```

**To customize default metadata**, edit `config/report_metadata.yaml`. The system will:
1. Load this template
2. Populate `title`, `subtitle`, and `abstract` based on report content
3. Allow user to override `info` fields
4. Prepend the YAML frontmatter to the final markdown report

## Usage

### Command Line Interface

```bash
# Generate a full report (converts non‑markdown files automatically)
python -m pocketreport.main --topic "Machine Learning in Healthcare" --materials ./research_papers --output ./output_report

# Generate only the outline (for planning)
python -m pocketreport.main --topic "Climate Change" --materials ./docs --outline-only

# Run minimal flow (skip chapter writing, for testing)
python -m pocketreport.main --topic "Quantum Computing" --materials ./papers --minimal

# List available markdown files
python -m pocketreport.main --list --materials ./research_papers

# Use a pre‑generated outline file (skip outline generation)
python -m pocketreport.main --topic "t-SNE Algorithm" --materials ./papers --outline-file ./output/outline.yaml

# Disable conversion caching (force re‑conversion of all files)
python -m pocketreport.main --topic "Test Topic" --materials ./mixed_files --no-cache

# Skip intermediate results (analysis, outline, conversion info)
python -m pocketreport.main --topic "Test Topic" --materials ./docs --no-intermediate
```

### Programmatic API

```python
from pocketreport import run_report_generation

# Generate a report
shared = run_report_generation(
    topic="Machine Learning Applications",
    materials_dir="./research_papers",
    output_dir="./output",
    minimal=False  # Set to True for testing
)

# Access the generated report
report_content = shared["output"]["report"]
report_path = shared["output"]["path"]
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--topic` | Report topic/title | Required |
| `--materials` | Directory with materials (markdown + other formats) | `./materials` |
| `--output` | Output directory for reports and intermediates | `./output` |
| `--minimal` | Run minimal flow (skip chapter writing) | `False` |
| `--outline-only` | Only generate outline (no writing) | `False` |
| `--outline-file` | Use existing outline file (YAML/JSON) | None |
| `--no-cache` | Disable caching of file conversions | `False` |
| `--no-intermediate` | Skip saving intermediate results | `False` |
| `--list` | List available files and exit | `False` |
| `--env-file` | Path to .env configuration file | None |

## Project Structure

```
pocket-report/
├── pocketreport/           # Main package
│   ├── __init__.py        # Package exports
│   ├── main.py           # CLI entry point
│   ├── nodes.py          # Agent node implementations
│   ├── flow.py           # Flow orchestration
│   └── utils/            # Utility functions
│       ├── __init__.py
│       ├── call_llm.py   # LLM API calls
│       ├── load_markdown.py # Markdown file loading
│       ├── load_materials.py # Multi‑format file loading & conversion
│       ├── save_report.py # Report saving
│       ├── save_intermediate.py # Intermediate results saving
│       ├── outline_serializer.py # Outline YAML/JSON serialization
│       └── models.py     # Pydantic models (including hierarchical sections)
├── docs/
│   └── design.md         # System design document
├── test_materials/       # Sample markdown files
├── test_system.py       # Component tests
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .env.example        # Example environment configuration
```

## Agent Prompts

The system uses three specialized prompts:

### 1. Analyst Agent
```text
System: You are an expert academic researcher.
Goal: Read raw materials and generate "Knowledge Context"
- Summarize core problem, methods, results
- List key technical terms and definitions
- Extract important math formulas/algorithms
```

### 2. Architect Agent
```text
System: You are an Academic Report Architect.
Goal: Design comprehensive report structure
- Output must be valid JSON with title and chapters
- Structure must be logical for academic paper
```

### 3. Writer Agent
```text
System: You are an Academic Writer.
Goal: Write specific chapter content
- Style: Formal, academic, objective
- Format: Markdown with LaTeX math
- Evidence: Base strictly on reference materials
```

## Dependencies

Core dependencies:
- `pocketflow`: Flow-based orchestration framework
- `pydantic`: Data validation and settings management
- `requests`: HTTP client for API calls
- `python-dotenv`: Environment variable management
- `markitdown[all]`: File format conversion (PDF, DOCX, PPTX, images, audio, etc.)
- `pyyaml`: YAML serialization for outlines

See `requirements.txt` for complete list.

**Note**: For file conversion features, install with `pip install 'markitdown[all]'`.

## Testing

Run the component tests:
```bash
python test_system.py
```

This tests:
- File loading utilities
- Pydantic models
- Node creation
- Flow orchestration
- Shared store structure
- Main module imports

## Design Principles

1. **Flow-Based Architecture**: Uses Pocket Flow for robust, retryable workflows
2. **Structured Data**: Pydantic models ensure data consistency
3. **Separation of Concerns**: Clear separation between agents, utilities, and orchestration
4. **Configurability**: Environment variables for LLM configuration
5. **Error Handling**: Built-in retry mechanisms and fallback strategies

## Limitations

- **Context Window**: Limited by LLM context size (mitigated by summarization)
- **API Dependencies**: Requires LLM API access and internet connection
- **Academic Focus**: Optimized for academic/scientific content
- **File Conversion**: Some complex PDF layouts may not convert perfectly
- **Caching**: Old cached conversion errors may persist (clear with `--no-cache`)

## Future Enhancements

Potential improvements:
- Enhanced PDF conversion quality for complex layouts
- Vector database integration for larger document sets
- Multi-language support
- Citation management and bibliography generation
- Interactive outline editing interface
- Performance optimizations for large document sets
- Plugin system for custom file converters

## License

MIT license

## Acknowledgments

- Built with the Pocket Flow framework
- Inspired by academic writing workflows
- Uses OpenAI-compatible LLM APIs