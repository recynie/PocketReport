# Design Doc: Academic Report Writing Agent System

> Please DON'T remove notes for AI

## Requirements

> Notes for AI: Keep it simple and clear.
> If the requirements are abstract, write concrete user stories

**User Story**: As a researcher, I want to input my academic materials (Markdown files) and get a comprehensive academic report written automatically, so I can save time on report writing and focus on research.

**Core Requirements**:
1. Read raw Markdown files from a local directory
2. Generate a structured summary of the materials (Analyst agent)
3. Create a logical report outline with chapters (Architect agent)
4. Write each chapter with academic rigor, referencing source materials (Writer agent)
5. Output a complete Markdown report

**Technical Constraints**:
- No vector database - rely on LLM's long-context capability
- Use OpenAI-compatible API (GPT-4o, DeepSeek, OpenRouter)
- Simplified flow-based approach (Pocket Flow inspired)
- MVP version with minimal complexity

## Flow Design

> Notes for AI:
> 1. Consider the design patterns of agent, map-reduce, rag, and workflow. Apply them if they fit.
> 2. Present a concise, high-level description of the workflow.

### Applicable Design Pattern:

**Sequential Agent Workflow**: Three specialized agents work in sequence:
1. **Analyst Agent**: Processes raw materials → produces structured summary
2. **Architect Agent**: Uses summary + user topic → produces report outline
3. **Writer Agent**: Iterates through chapters → produces final report

This is a **workflow** pattern where each node transforms data for the next node.

### Flow high-level Design:

1. **Load Materials Node**: Load and concatenate Markdown files from input directory
2. **Analyst Node**: Generate structured summary/knowledge context from raw materials
3. **Architect Node**: Create report outline (title + chapters) based on topic and summary
4. **Writer Loop Node**: For each chapter in outline, write chapter content
5. **Assemble Report Node**: Combine all chapters into final report

```mermaid
flowchart TD
    start[Start] --> load[Load Materials]
    load --> analyst[Analyst Agent]
    analyst --> architect[Architect Agent]
    architect --> writerLoop[Writer Loop]
    writerLoop --> assemble[Assemble Report]
    assemble --> end[End]
    
    subgraph writerLoop [Writer Loop]
        direction LR
        forEach[For each chapter] --> write[Write Chapter]
        write --> next[Next]
    end
```

## Utility Functions

> Notes for AI:
> 1. Understand the utility function definition thoroughly by reviewing the doc.
> 2. Include only the necessary utility functions, based on nodes in the flow.

1. **Load Markdown Files** (`utils/load_markdown.py`)
   - *Input*: directory path (str)
   - *Output*: concatenated markdown content (str)
   - *Necessity*: Used by Load Materials node to read input files

2. **Call LLM** (`utils/call_llm.py`)
   - *Input*: system_prompt (str), user_prompt (str), json_mode (bool)
   - *Output*: LLM response (str or dict)
   - *Necessity*: Used by all agent nodes to interact with LLM API

3. **Save Report** (`utils/save_report.py`)
   - *Input*: report content (str), output path (str)
   - *Output*: file path (str)
   - *Necessity*: Used by Assemble Report node to save final output

## Node Design

### Shared Store

> Notes for AI: Try to minimize data redundancy

The shared store structure is organized as follows:

```python
shared = {
    "input": {
        "topic": "User-provided report topic",
        "materials_dir": "path/to/markdown/files"
    },
    "materials": {
        "raw_content": "Concatenated markdown text",
        "file_count": 3
    },
    "analysis": {
        "summary": "Structured summary from Analyst agent"
    },
    "outline": {
        "title": "Report Title",
        "chapters": [
            {"index": 1, "title": "Introduction", "description": "..."},
            # ... more chapters
        ]
    },
    "writing": {
        "chapters": {
            1: "Chapter 1 content in markdown",
            2: "Chapter 2 content in markdown",
            # ... all chapters
        },
        "current_chapter": 1
    },
    "output": {
        "report": "Complete assembled report",
        "output_path": "path/to/output/report.md"
    }
}
```

### Node Steps

> Notes for AI: Carefully decide whether to use Batch/Async Node/Flow.

1. **Load Materials Node**
   - *Purpose*: Load and concatenate all Markdown files from input directory
   - *Type*: Regular Node
   - *Steps*:
     - *prep*: Read "input.materials_dir" from shared store
     - *exec*: Call load_markdown utility function
     - *post*: Write "materials.raw_content" and "materials.file_count" to shared store

2. **Analyst Node**
   - *Purpose*: Generate structured summary/knowledge context from raw materials
   - *Type*: Regular Node
   - *Steps*:
     - *prep*: Read "materials.raw_content" from shared store
     - *exec*: Call LLM with Analyst prompt template
     - *post*: Write "analysis.summary" to shared store

3. **Architect Node**
   - *Purpose*: Create report outline based on topic and analysis summary
   - *Type*: Regular Node
   - *Steps*:
     - *prep*: Read "input.topic" and "analysis.summary" from shared store
     - *exec*: Call LLM with Architect prompt template (JSON mode)
     - *post*: Parse JSON and write "outline.title" and "outline.chapters" to shared store

4. **Writer Node** (Batch Node for chapters)
   - *Purpose*: Write content for each chapter in the outline
   - *Type*: Batch Node (processes each chapter)
   - *Steps*:
     - *prep*: Read "outline.chapters", "outline.title", "analysis.summary", "materials.raw_content" from shared store
     - *exec*: For each chapter, call LLM with Writer prompt template
     - *post*: Write each chapter content to "writing.chapters[chapter_index]" in shared store

5. **Assemble Report Node**
   - *Purpose*: Combine all chapters into final report and save to file
   - *Type*: Regular Node
   - *Steps*:
     - *prep*: Read "writing.chapters" and "outline.title" from shared store
     - *exec*: Assemble chapters with proper formatting
     - *post*: Write "output.report" to shared store and save to file using save_report utility