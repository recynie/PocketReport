"""
Node implementations for the academic report writing system.
"""
import json
from typing import Dict, Any, List, Optional
from pocketreport.pocketflow import Node, BatchNode
from pocketreport.utils import (
    call_llm_with_retry,
    load_markdown_files,
    save_report,
    Chapter,
    ReportOutline,
    AnalysisSummary,
    Report
)
 
class LoadMaterialsNode(Node):
    """Node for loading and concatenating Markdown files."""
    
    def prep(self, shared: Dict[str, Any]) -> str:
        """Prepare by getting materials directory from shared store."""
        materials_dir = shared.get("input", {}).get("materials_dir", "./materials")
        return materials_dir
    
    def exec(self, materials_dir: str) -> Dict[str, Any]:
        """Load markdown files from directory."""
        try:
            content, file_count = load_markdown_files(materials_dir)
            return {
                "raw_content": content,
                "file_count": file_count,
                "materials_dir": materials_dir
            }
        except Exception as e:
            raise RuntimeError(f"Failed to load materials from {materials_dir}: {e}")
    
    def post(self, shared: Dict[str, Any], prep_res: str, exec_res: Dict[str, Any]) -> str:
        """Store loaded materials in shared store."""
        if "materials" not in shared:
            shared["materials"] = {}
        
        shared["materials"]["raw_content"] = exec_res["raw_content"]
        shared["materials"]["file_count"] = exec_res["file_count"]
        shared["materials"]["dir"] = exec_res["materials_dir"]
        
        print(f"Loaded {exec_res['file_count']} markdown files from {exec_res['materials_dir']}")
        print(f"Total content length: {len(exec_res['raw_content'])} characters")
        
        return "default"


class AnalystNode(Node):
    """Node for analyzing materials and generating structured summary."""
    
    def __init__(self, max_retries: int = 3):
        super().__init__(max_retries=max_retries)
    
    def prep(self, shared: Dict[str, Any]) -> str:
        """Prepare by getting raw materials from shared store."""
        raw_content = shared.get("materials", {}).get("raw_content", "")
        if not raw_content:
            raise ValueError("No materials loaded. Run LoadMaterialsNode first.")
        return raw_content
    
    def exec(self, raw_content: str) -> str:
        """Generate structured summary using LLM."""
        system_prompt = """You are an expert academic researcher.
Your goal is to read the provided raw reference materials and generate a "Knowledge Context".
1. Summarize the core problem, methods, and results.
2. List key technical terms and definitions.
3. Extract important math formulas or algorithms (describe them)."""
        
        user_prompt = f"""[RAW MATERIALS]:
{raw_content[:15000]}"""  # Limit context size
        
        response = call_llm_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=False,
            max_retries=self.max_retries
        )
        
        return response
    
    def post(self, shared: Dict[str, Any], prep_res: str, exec_res: str) -> str:
        """Store analysis summary in shared store."""
        if "analysis" not in shared:
            shared["analysis"] = {}
        
        shared["analysis"]["summary"] = exec_res
        
        print(f"Generated analysis summary ({len(exec_res)} characters)")
        
        return "default"


class ArchitectNode(Node):
    """Node for creating report outline based on topic and analysis."""
    
    def __init__(self, max_retries: int = 3):
        super().__init__(max_retries=max_retries)
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, str]:
        """Prepare by getting topic and analysis summary."""
        topic = shared.get("input", {}).get("topic", "Academic Report")
        analysis_summary = shared.get("analysis", {}).get("summary", "")
        
        if not analysis_summary:
            raise ValueError("No analysis available. Run AnalystNode first.")
        
        return {
            "topic": topic,
            "analysis_summary": analysis_summary
        }
    
    def exec(self, inputs: Dict[str, str]) -> Dict[str, Any]:
        """Generate report outline using LLM with JSON output."""
        system_prompt = """You are an Academic Report Architect.
Based on the user's topic and the provided reference summary, design a comprehensive report structure.
The structure must be logical and suitable for a long-form academic paper.
You MUST output strictly valid JSON matching the following schema:
{
  "title": "Report Title",
  "chapters": [
    {"index": 1, "title": "Introduction", "description": "Cover background..."},
    ...
  ]
}"""
        
        user_prompt = f"""[USER TOPIC]: {inputs['topic']}
[REFERENCE SUMMARY]: {inputs['analysis_summary']}"""
        
        response = call_llm_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
            max_retries=self.max_retries
        )
        
        # Ensure response is a dict
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                raise ValueError(f"Failed to parse JSON response: {response[:200]}")
        
        return response
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, str], exec_res: Dict[str, Any]) -> str:
        """Store report outline in shared store."""
        if "outline" not in shared:
            shared["outline"] = {}
        
        # Validate and store outline
        try:
            outline = ReportOutline(**exec_res)
            shared["outline"]["title"] = outline.title
            shared["outline"]["chapters"] = outline.chapters
            shared["outline"]["object"] = outline  # Store the Pydantic object
            
            print(f"Generated outline: '{outline.title}' with {len(outline.chapters)} chapters")
            for chapter in outline.chapters:
                print(f"  Chapter {chapter.index}: {chapter.title}")
            
        except Exception as e:
            raise ValueError(f"Invalid outline structure: {e}")
        
        return "default"


class WriterNode(BatchNode):
    """Node for writing chapters (batch processing)."""
    
    def __init__(self, max_retries: int = 3):
        super().__init__(max_retries=max_retries)
    
    def prep(self, shared: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare batch items (chapters to write)."""
        outline = shared.get("outline", {})
        chapters = outline.get("chapters", [])
        report_title = outline.get("title", "Report")
        analysis_summary = shared.get("analysis", {}).get("summary", "")
        raw_content = shared.get("materials", {}).get("raw_content", "")
        
        if not chapters:
            raise ValueError("No chapters in outline. Run ArchitectNode first.")
        
        # Prepare context for each chapter
        batch_items = []
        for i, chapter in enumerate(chapters):
            # Get previous chapter summary if available
            previous_summary = ""
            if i > 0 and "writing" in shared and "chapters" in shared["writing"]:
                prev_chapter = chapters[i-1]
                prev_content = shared["writing"]["chapters"].get(str(prev_chapter.index), "")
                if prev_content:
                    # Create a brief summary of previous chapter
                    previous_summary = f"Previous chapter ({prev_chapter.title}): {prev_content[:500]}..."
            
            batch_items.append({
                "chapter": chapter,
                "report_title": report_title,
                "analysis_summary": analysis_summary,
                "raw_content": raw_content[:10000],  # Limit context size
                "previous_summary": previous_summary,
                "chapter_index": i
            })
        
        return batch_items
    
    def exec(self, batch_item: Dict[str, Any]) -> str:
        """Write a single chapter."""
        chapter = batch_item["chapter"]
        
        system_prompt = """You are an Academic Writer. Write the content for the specific chapter described below.
- Style: Formal, academic, objective.
- Format: Markdown with LaTeX for math ($...$).
- Evidence: Strictly base your content on the [Reference Materials]. Do not hallucinate."""
        
        user_prompt = f"""[REPORT TITLE]: {batch_item['report_title']}
[CHAPTER TITLE]: {chapter.title}
[CHAPTER INSTRUCTIONS]: {chapter.description}

[CONTEXT / PREVIOUS CHAPTER SUMMARY]:
{batch_item['previous_summary']}

[REFERENCE MATERIALS]:
{batch_item['raw_content']}"""
        
        response = call_llm_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=False,
            max_retries=self.max_retries
        )
        
        return response
    
    def post(self, shared: Dict[str, Any], prep_res: List[Dict[str, Any]], exec_res: List[str]) -> str:
        """Store written chapters in shared store."""
        if "writing" not in shared:
            shared["writing"] = {"chapters": {}}
        
        # Store each chapter
        for i, chapter_content in enumerate(exec_res):
            chapter = prep_res[i]["chapter"]
            chapter_index = chapter.index
            
            shared["writing"]["chapters"][str(chapter_index)] = chapter_content
            
            print(f"Written chapter {chapter_index}: {chapter.title} ({len(chapter_content)} characters)")
        
        return "default"


class AssembleReportNode(Node):
    """Node for assembling final report from written chapters."""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare by getting chapters and outline."""
        writing = shared.get("writing", {})
        chapters_content = writing.get("chapters", {})
        outline = shared.get("outline", {})
        report_title = outline.get("title", "Report")
        
        if not chapters_content:
            raise ValueError("No chapters written. Run WriterNode first.")
        
        return {
            "chapters_content": chapters_content,
            "report_title": report_title,
            "outline": outline
        }
    
    def exec(self, inputs: Dict[str, Any]) -> str:
        """Assemble complete report."""
        chapters_content = inputs["chapters_content"]
        report_title = inputs["report_title"]
        
        # Sort chapters by index
        sorted_indices = sorted(chapters_content.keys(), key=lambda x: int(x))
        
        # Assemble report
        lines = [f"# {report_title}\n"]
        
        for idx in sorted_indices:
            content = chapters_content[idx]
            lines.append(content)
            lines.append("\n")  # Add blank line between chapters
        
        return "\n".join(lines)
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> str:
        """Store and save final report."""
        if "output" not in shared:
            shared["output"] = {}
        
        shared["output"]["report"] = exec_res
        
        # Save to file
        report_title = prep_res["report_title"]
        output_path = save_report(
            content=exec_res,
            report_title=report_title
        )
        
        shared["output"]["path"] = output_path
        
        print(f"Assembled report: {report_title}")
        print(f"Saved to: {output_path}")
        print(f"Report length: {len(exec_res)} characters")
        
        return "default"


class PrintSummaryNode(Node):
    """Node for printing a summary of the process."""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Collect summary data."""
        return {
            "materials": shared.get("materials", {}),
            "analysis": shared.get("analysis", {}),
            "outline": shared.get("outline", {}),
            "writing": shared.get("writing", {}),
            "output": shared.get("output", {})
        }
    
    def exec(self, summary_data: Dict[str, Any]) -> str:
        """Generate summary text."""
        materials = summary_data.get("materials", {})
        outline = summary_data.get("outline", {})
        output = summary_data.get("output", {})
        
        lines = [
            "=" * 60,
            "ACADEMIC REPORT WRITING SYSTEM - PROCESS SUMMARY",
            "=" * 60,
            f"Materials loaded: {materials.get('file_count', 0)} files",
            f"Outline created: {outline.get('title', 'N/A')}",
            f"Chapters written: {len(outline.get('chapters', []))}",
            f"Report saved to: {output.get('path', 'N/A')}",
            "=" * 60
        ]
        
        return "\n".join(lines)
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> str:
        """Print summary."""
        print(exec_res)
        return "default"