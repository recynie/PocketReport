# Design Doc: Academic Report Writing Agent System

> Please DON'T remove notes for AI

## Requirements

> Notes for AI: Keep it simple and clear.
> If the requirements are abstract, write concrete user stories

**User Story**: As a researcher, I want to input my academic materials (Markdown and other document formats) and get a comprehensive academic report written automatically, so I can save time on report writing and focus on research.

**Core Requirements**:
1. Read raw materials from a local directory, supporting multiple formats (Markdown, PDF, DOCX, etc.) via automatic conversion to Markdown.
2. Generate a structured summary of the materials (Analyst agent)
3. Create a logical report outline with hierarchical sections (Architect agent)
4. Write each section with academic rigor, referencing source materials (Writer agent)
5. Output a complete Markdown report
6. Save intermediate results (converted files, analysis, outline) to output folder for reusability and inspection
7. Allow outline to be saved/loaded as YAML file for manual editing and reuse

**Technical Constraints**:
- No vector database - rely on LLM's long-context capability
- Use OpenAI-compatible API (GPT-4o, DeepSeek, OpenRouter)
- Simplified flow-based approach (Pocket Flow inspired)
- MVP version with minimal complexity

**New Requirements (Report Metadata)**:
8. All LLM prompts are centralized in `config/prompts.toml` for easy maintenance and modification.
9. Final markdown reports include YAML frontmatter with metadata (title, subtitle, abstract, author info).
10. YAML metadata template is stored in `config/report_metadata.yaml` and loaded dynamically.
11. Agents can customize title, subtitle, and abstract in the metadata during report assembly.
12. Final report format: YAML frontmatter (with `---` separators) followed by markdown content.

## Flow Design

> Notes for AI:
> 1. Consider the design patterns of agent, map-reduce, rag, and workflow. Apply them if they fit.
> 2. Present a concise, high-level description of the workflow.

### Applicable Design Pattern:

**Sequential Agent Workflow**: Three specialized agents work in sequence:
1. **Analyst Agent**: Processes raw materials → produces structured summary
2. **Architect Agent**: Uses summary + user topic → produces hierarchical report outline
3. **Writer Agent**: Iterates through outline sections → produces final report

This is a **workflow** pattern where each node transforms data for the next node.

### Flow high-level Design:

1. **Load Materials Node**: Load and convert all supported files in input directory to Markdown, save converted files to output folder, concatenate content.
2. **Analyst Node**: Generate structured summary/knowledge context from raw materials.
3. **Architect Node**: Create hierarchical report outline (title, chapters, subsections) based on topic and summary. Save outline as YAML to output folder.
4. **Writer Node** (Batch): For each section in outline, write section content.
5. **Assemble Report Node**: Combine all sections into final report and save to file.

```mermaid
flowchart TD
    start[Start] --> load[Load Materials & Convert]
    load --> analyst[Analyst Agent]
    analyst --> architect[Architect Agent]
    architect --> writerLoop[Writer Loop]
    writerLoop --> assemble[Assemble Report]
    assemble --> end[End]
    
    subgraph load [Load Materials & Convert]
        direction LR
        scan[Scan directory] --> convert[Convert non‑MD files]
        convert --> save[Save converted MD]
        save --> concat[Concatenate content]
    end
    
    subgraph writerLoop [Writer Loop]
        direction LR
        forEach[For each section] --> write[Write Section]
        write --> next[Next]
    end
```

## Utility Functions

> Notes for AI:
> 1. Understand the utility function definition thoroughly by reviewing the doc.
> 2. Include only the necessary utility functions, based on nodes in the flow.

1. **Load and Convert Materials** (`utils/load_materials.py`)
   - *Input*: directory path (str), output directory (str)
   - *Output*: concatenated markdown content (str), list of converted file paths
   - *Necessity*: Used by Load Materials node to read input files and convert non‑MD files using MarkItDown.
   - *Features*: Detects file extensions, converts PDF, DOCX, etc., saves converted markdown to output/converted/, caches conversion.

2. **Call LLM** (`utils/call_llm.py`)
   - *Input*: system_prompt (str), user_prompt (str), json_mode (bool)
   - *Output*: LLM response (str or dict)
   - *Necessity*: Used by all agent nodes to interact with LLM API.

3. **Save Report** (`utils/save_report.py`)
   - *Input*: report content (str), output path (str)
   - *Output*: file path (str)
   - *Necessity*: Used by Assemble Report node to save final output.

4. **Outline Serialization** (`utils/outline_serializer.py`)
   - *Input*: ReportOutline object, file path (str)
   - *Output*: None (writes YAML)
   - *Necessity*: Save outline for reuse; load outline from YAML file.

5. **Intermediate Results Saver** (`utils/save_intermediate.py`)
   - *Input*: data dict, category (str), output directory (str)
   - *Output*: file path (str)
   - *Necessity*: Save analysis summary, converted files, outline, etc. to organized output folder.

6. **Prompt Loader** (`utils/prompt_loader.py`)
   - *Input*: prompt key (str), optional substitutions dict
   - *Output*: loaded prompt string (str)
   - *Necessity*: Load prompts from centralized `config/prompts.toml` file for all LLM nodes (Analyst, Architect, Writer).
   - *Features*: Cache prompts in memory, support template variables for dynamic substitution.

7. **Metadata Loader** (`utils/metadata_loader.py`)
   - *Input*: metadata dict with title, subtitle, abstract (and other fields)
   - *Output*: YAML string or dict
   - *Necessity*: Load base YAML template from `config/report_metadata.yaml` and update with provided metadata.
   - *Features*: Validate required fields, generate YAML frontmatter with `---` separators.

## Data Design

> Notes for AI: Design the shared store that nodes will use to communicate.

The shared store structure is organized as follows:

```python
shared = {
    "input": {
        "topic": "User-provided report topic",
        "materials_dir": "path/to/materials",
        "outline_file": "optional/path/to/outline.yaml"  # New: allow loading existing outline
    },
    "materials": {
        "raw_content": "Concatenated markdown text",
        "file_count": 3,
        "converted_files": ["path1.md", "path2.md"]  # Paths to converted files
    },
    "analysis": {
        "summary": "Structured summary from Analyst agent"
    },
    "outline": {
        "title": "Report Title",
        "sections": [  # Hierarchical sections (arbitrary nesting)
            {
                "index": "1",
                "title": "Introduction",
                "description": "...",
                "subsections": [
                    {
                        "index": "1.1",
                        "title": "Background",
                        "description": "...",
                        "subsections": [
                            {
                                "index": "1.1.1",
                                "title": "Historical Context",
                                "description": "..."
                            }
                        ]
                    }
                ]
            }
        ]
    },
    "writing": {
        "sections": {
            "1": "Chapter 1 content in markdown",
            "1.1": "Section 1.1 content",
            # ... all sections
        }
    },
    "output": {
        "report": "Complete assembled report",
        "output_path": "path/to/output/report.md",
        "metadata": {
            "title": "Report Title",
            "subtitle": "Report Subtitle",
            "abstract": "Report Abstract Summary",
            "info": {
                "姓名": "Author Name",
                "学号": "Student ID",
                "课程": "Course Name",
                "日期": "Date",
                "指导教师": "Advisor Name"
            }
        }
    }
}
```

## Node Design

### Node Steps

> Notes for AI: Carefully decide whether to use Batch/Async Node/Flow.

1. **Load Materials Node**
   - *Purpose*: Load and convert all supported files in input directory to Markdown.
   - *Type*: Regular Node
   - *Steps*:
     - *prep*: Read "input.materials_dir" from shared store.
     - *exec*: Call load_materials utility function (handles conversion).
     - *post*: Write "materials.raw_content", "materials.file_count", "materials.converted_files" to shared store.

2. **Analyst Node**
   - *Purpose*: Generate structured summary/knowledge context from raw materials.
   - *Type*: Regular Node
   - *Steps*:
     - *prep*: Read "materials.raw_content" from shared store.
     - *exec*: Call LLM with Analyst prompt template.
     - *post*: Write "analysis.summary" to shared store; optionally save to output folder.

3. **Architect Node** (optional if outline provided)
   - *Purpose*: Create hierarchical report outline based on topic and analysis summary.
   - *Type*: Regular Node
   - *Steps*:
     - *prep*: Read "input.topic" and "analysis.summary" from shared store; check if "input.outline_file" exists.
     - *exec*: If outline file provided, load it; else call LLM with Architect prompt template (JSON mode) for nested sections.
     - *post*: Parse outline and write "outline.title" and "outline.sections" to shared store; save outline as YAML to output folder.

4. **Writer Node** (Batch Node for sections)
   - *Purpose*: Write content for each section in the outline (breadth‑first or depth‑first).
   - *Type*: Batch Node (processes each leaf section)
   - *Steps*:
     - *prep*: Read "outline.sections", "outline.title", "analysis.summary", "materials.raw_content" from shared store.
     - *exec*: For each section, call LLM with Writer prompt template (context includes parent sections).
     - *post*: Write each section content to "writing.sections[section_index]" in shared store.

5. **Assemble Report Node**
   - *Purpose*: Combine all sections into final report respecting hierarchy, prepare metadata, and save to file.
   - *Type*: Regular Node
   - *Steps*:
     - *prep*: Read "writing.sections", "outline.sections", "input.topic", "analysis.summary" from shared store.
     - *exec*: Traverse outline hierarchy, assemble sections with appropriate heading levels. Generate metadata (title, subtitle, abstract). Load YAML template and populate metadata.
     - *post*: Write "output.report", "output.metadata", and "output.output_path" to shared store; save to file using save_report utility (includes YAML frontmatter).

6. **Print Summary Node**
   - *Purpose*: Print summary of the generated report.
   - *Type*: Regular Node
   - *Steps*: (as existing)

## Implementation

> Notes for AI: Keep it simple, stupid! Avoid complex features and full‑scale type checking. FAIL FAST! Leverage the built‑in Node retry and fallback mechanisms to handle failures gracefully. Add logging throughout the code to facilitate debugging.

Implementation will follow the Pocket Flow framework already used. The main changes are:

- Extend `load_markdown.py` to `load_materials.py` with MarkItDown integration.
- Create new utility modules: `outline_serializer.py`, `save_intermediate.py`, `prompt_loader.py`, `metadata_loader.py`.
- Update data models (`models.py`) to support hierarchical sections and metadata.
- Create `config/prompts.toml` to centralize all LLM prompts used by Analyst, Architect, and Writer nodes.
- Create `config/report_metadata.yaml` as YAML template for report metadata.
- Modify all agent nodes to load prompts from centralized config instead of hardcoding.
- Update `AssembleReportNode` to generate metadata and prepend YAML frontmatter to report.
- Modify `save_report()` utility to handle YAML frontmatter when saving.
- Update `flow.py` to optionally skip ArchitectNode when outline file provided.
- Update `main.py` CLI to accept `--outline-file`, `--save-intermediate`, and metadata-related flags.
- Ensure all intermediate files are saved under `output/` with clear naming.

### Section Nesting Improvements

The system now supports **arbitrary section nesting** with proper heading level calculation:

1. **Heading Levels**: Heading levels are determined by the dot count in the section index:
   - `"1"` → h1 (top-level section)
   - `"1.1"` → h2
   - `"1.1.1"` → h3
   - `"1.1.1.1"` → h4
   - `"1.1.1.1.1"` → h5
   - `"1.1.1.1.1.1"` → h6 (maximum per Markdown spec)
   - Deeper nesting is capped at h6

2. **No Section Type Distinction**: The deprecated `SectionType` enum (chapter/section/subsection) is no longer used. All sections are treated uniformly.

3. **Report Title Handling**: The report title is used only for filename generation and is **not** included as an h1 heading in the content. Top-level sections (index like "1", "2") become h1 headings.

4. **Backward Compatibility**: Legacy outlines with `type` field are still supported through automatic conversion.

5. **Duplicate Heading Prevention**: The WriterNode checks if LLM-generated content already includes a heading and avoids adding duplicate headings.

## Optimization

- **Prompt Engineering**: Refine prompts for Analyst, Architect, and Writer agents to produce higher‑quality outputs.
- **In‑Context Learning**: Provide robust examples for nested outline generation.
- **Caching Converted Files**: Avoid re‑conversion of unchanged files by checking timestamps.
- **Parallel Writing**: Consider parallelizing section writing where dependencies allow (e.g., sibling sections).

## Reliability

- **Node Retries**: Increase `max_retries` and `wait` times for LLM‑heavy nodes.
- **Logging and Visualization**: Maintain logs of all attempts and visualize node results for easier debugging.
- **Self‑Evaluation**: Add a separate node (powered by an LLM) to review outline and report quality when results are uncertain.
- **Validation**: Validate converted markdown content for completeness; validate outline structure before writing.