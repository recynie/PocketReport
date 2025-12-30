### **Prompt specifically for Coding LLM: Building the MVP Academic Agent System**

**Context:**
I need you to build a Python-based Multi-Agent system for writing academic reports.
This is an MVP version.
- **Input**: Raw Markdown files (loaded from a local directory).
- **No Vector DB**: The system relies on the LLM's long-context capability.
- **Framework**: Use a simplified flow-based approach (inspired by Pocket Flow or LangChain Graph).
- **LLM Provider**: OpenAI-compatible API (e.g., GPT-4o, DeepSeek, OpenRouter).

**Project Goal:**
The system reads academic materials (Markdown), plans a report outline, and writes the report chapter by chapter.

Please follow the architecture and implementation details below strictly.

---

### 1. Data Structures (Pydantic Models)

Use `pydantic` to enforce structured outputs for the planning stage.

```python
from pydantic import BaseModel, Field
from typing import List

class Chapter(BaseModel):
    index: int
    title: str = Field(..., description="The title of the chapter")
    description: str = Field(..., description="Detailed instructions on what this chapter should cover, based on input materials")

class ReportOutline(BaseModel):
    title: str
    chapters: List[Chapter]
```

### 2. The Agent Prompts (System Prompts)

You need to implement three specific agents. Use a robust function to call the LLM API (e.g., `call_llm(system_prompt, user_prompt, json_mode=False)`).

#### **Agent A: The Analyst (Content Compress)**
*Goal:* Read raw markdown and generate a structured summary to serve as the "Global Context" for other agents.
*Prompt Template:*
```text
System:
You are an expert academic researcher.
Your goal is to read the provided raw reference materials and generate a "Knowledge Context".
1. Summarize the core problem, methods, and results.
2. List key technical terms and definitions.
3. Extract important math formulas or algorithms (describe them).

User Input:
[RAW MATERIALS]:
{raw_markdown_content}
```

#### **Agent B: The Architect (Planner)**
*Goal:* Generate a JSON outline.
*Prompt Template:*
```text
System:
You are an Academic Report Architect.
Based on the user's topic and the provided reference summary, design a comprehensive report structure.
The structure must be logical and suitable for a long-form academic paper.
You MUST output strictly valid JSON matching the following schema:
{
  "title": "Report Title",
  "chapters": [
    {"index": 1, "title": "Introduction", "description": "Cover background..."},
    ...
  ]
}

User Input:
[USER TOPIC]: {user_topic}
[REFERENCE SUMMARY]: {summary_from_analyst}
```

#### **Agent C: The Writer (Executor)**
*Goal:* Write one chapter at a time.
*Important Strategy:* Since we don't have RAG, pass the **Reference Summary** AND the **Raw Materials** (if they fit in context) to the Writer.
*Prompt Template:*
```text
System:
You are an Academic Writer. Write the content for the specific chapter described below.
- Style: Formal, academic, objective.
- Format: Markdown with LaTeX for math ($...$).
- Evidence: Strictly base your content on the [Reference Materials]. Do not hallucinate.

User Input:
[REPORT TITLE]: {report_title}
[CHAPTER TITLE]: {chapter_title}
[CHAPTER INSTRUCTIONS]: {chapter_description}

[CONTEXT / PREVIOUS CHAPTER SUMMARY]:
{previous_chapter_summary} (Optional, to keep flow)

[REFERENCE MATERIALS]:
{raw_markdown_content}
```

### 3. Implementation Logic (The Flow)

Write a main class `AcademicReportGenerator`.

**Step 1: Ingestion**
- Function `load_materials(path)`: Read all `.md` files in the folder and concatenate them into a single string `raw_text`.

**Step 2: Analysis**
- Call **Agent A (Analyst)** with `raw_text`.
- Store result as `global_summary`.

**Step 3: Planning**
- Call **Agent B (Architect)** with `user_topic` and `global_summary`.
- Parse the JSON output into the `ReportOutline` object.

**Step 4: Execution Loop (Sequential)**
- Initialize `full_report = ""`
- Iterate through `outline.chapters`:
    - Print status: "Writing Chapter {index}: {title}..."
    - Call **Agent C (Writer)**.
        - Inputs: `chapter.title`, `chapter.description`, `raw_text` (or `global_summary` if text is too long).
    - Receive `chapter_content`.
    - Append to `full_report`.
    - (Optional) Save individual chapter files (`chapter_01.md`, etc.).

**Step 5: Assembly**
- Save the final `full_report` to `final_report.md`.

### 4. Technical Requirements

- **Environment**: Use `python-dotenv` to load `OPENAI_API_KEY`.
- **LLM Client**: Use `openai.OpenAI` client.
- **Error Handling**: Add retry logic for JSON parsing (if Agent B fails to output valid JSON).
- **Configuration**: Allow the user to specify the `model_name` (default to `gpt-4o` or equivalent for best results with long context).

---

### **Action Plan for the Coding LLM**

1.  **Setup**: Create `main.py` and `agents.py`.
2.  **Helpers**: Create a `chat_completion` wrapper function that handles the API call.
3.  **Logic**: Implement the 5-step flow described above.
4.  **CLI**: Use `argparse` to let me run it like:
    `python main.py --topic "LLM Agents" --input_dir "./docs" --output "report.md"`

Start by writing the code for `agents.py` and the `ReportOutline` data structure.