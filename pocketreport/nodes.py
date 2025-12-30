"""
Node implementations for the academic report writing system.
"""
import json
import os
import logging
from typing import Dict, Any, List, Optional
from pocketreport.pocketflow import Node, BatchNode
from pocketreport.utils import (
    call_llm_with_retry,
    load_markdown_files,
    load_materials,
    save_report,
    Chapter,
    ReportOutline,
    AnalysisSummary,
    Report,
    Section,
    SectionType,
    outline_serializer
)
 
class LoadMaterialsNode(Node):
    """Node for loading and converting materials to Markdown."""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare by getting materials directory and output options."""
        materials_dir = shared.get("input", {}).get("materials_dir", "./materials")
        output_dir = shared.get("input", {}).get("output_dir", "./output")
        cache_conversions = shared.get("input", {}).get("cache_conversions", True)
        
        return {
            "materials_dir": materials_dir,
            "output_dir": output_dir,
            "cache_conversions": cache_conversions
        }
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load and convert materials from directory."""
        try:
            content, file_count, converted_files = load_materials(
                directory_path=inputs["materials_dir"],
                output_dir=os.path.join(inputs["output_dir"], "converted"),
                cache_conversions=inputs["cache_conversions"]
            )
            return {
                "raw_content": content,
                "file_count": file_count,
                "converted_files": converted_files,
                "materials_dir": inputs["materials_dir"],
                "output_dir": inputs["output_dir"]
            }
        except ImportError as e:
            raise RuntimeError(
                f"MarkItDown not installed. Install with: pip install 'markitdown[all]'\n{str(e)}"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load materials from {inputs['materials_dir']}: {e}")
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """Store loaded materials in shared store."""
        if "materials" not in shared:
            shared["materials"] = {}
        
        shared["materials"]["raw_content"] = exec_res["raw_content"]
        shared["materials"]["file_count"] = exec_res["file_count"]
        shared["materials"]["converted_files"] = exec_res["converted_files"]
        shared["materials"]["dir"] = exec_res["materials_dir"]
        shared["materials"]["output_dir"] = exec_res["output_dir"]
        
        logging.info(f"Loaded {exec_res['file_count']} files from {exec_res['materials_dir']}")
        logging.info(f"Converted {len(exec_res['converted_files'])} non‑markdown files")
        logging.info(f"Total content length: {len(exec_res['raw_content'])} characters")
        
        # Save conversion info to output folder
        conversion_info_path = os.path.join(exec_res["output_dir"], "conversion_info.json")
        try:
            import json as json_module
            with open(conversion_info_path, 'w', encoding='utf-8') as f:
                json_module.dump({
                    "materials_dir": exec_res["materials_dir"],
                    "total_files": exec_res["file_count"],
                    "converted_files": exec_res["converted_files"]
                }, f, indent=2, default=str)
            logging.info(f"Conversion info saved to {conversion_info_path}")
        except Exception as e:
            logging.warning(f"Could not save conversion info: {e}")
        
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
{raw_content[:127000]}"""  # Limit context size
        
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
        
        logging.info(f"Generated analysis summary ({len(exec_res)} characters)")
        
        return "default"


class ArchitectNode(Node):
    """Node for creating hierarchical report outline based on topic and analysis."""
    
    def __init__(self, max_retries: int = 3):
        super().__init__(max_retries=max_retries)
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare by getting topic, analysis summary, and optional outline file."""
        topic = shared.get("input", {}).get("topic", "Academic Report")
        analysis_summary = shared.get("analysis", {}).get("summary", "")
        outline_file = shared.get("input", {}).get("outline_file")
        
        if not analysis_summary and not outline_file:
            raise ValueError("No analysis available. Run AnalystNode first or provide outline file.")
        
        return {
            "topic": topic,
            "analysis_summary": analysis_summary,
            "outline_file": outline_file
        }
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate or load report outline."""
        # If outline file provided, load it
        if inputs.get("outline_file"):
            try:
                outline = outline_serializer.load_outline(inputs["outline_file"])
                logging.info(f"Loaded outline from file: {inputs['outline_file']}")
                return outline.model_dump()
            except Exception as e:
                raise RuntimeError(f"Failed to load outline from {inputs['outline_file']}: {e}")
        
        # Otherwise generate hierarchical outline using LLM
        system_prompt = """You are an Academic Report Architect.
Based on the user's topic and the provided reference summary, design a comprehensive hierarchical report structure.
The structure should have chapters, sections, and possibly subsections for detailed organization.
You MUST output strictly valid JSON matching the following schema:
{
  "title": "Report Title",
  "sections": [
    {
      "type": "chapter",
      "index": "1",
      "title": "Introduction",
      "description": "Cover background, motivation, and problem statement.",
      "subsections": [
        {
          "type": "section",
          "index": "1.1",
          "title": "Background",
          "description": "Provide historical context and related work."
        },
        {
          "type": "section",
          "index": "1.2",
          "title": "Problem Statement",
          "description": "Define the specific problem addressed."
        }
      ]
    },
    {
      "type": "chapter",
      "index": "2",
      "title": "Methodology",
      "description": "Describe the methods, algorithms, and experimental setup.",
      "subsections": []
    }
  ]
}
Important:
- Use "type": "chapter" for top‑level sections, "type": "section" for subsections.
- Indexes should be hierarchical: "1", "1.1", "1.2", "2", "2.1", etc.
- Include at least 3‑5 chapters with 2‑4 subsections each for a comprehensive report.
- Ensure descriptions are specific and reference the provided materials."""
        
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
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """Store report outline in shared store and save to file."""
        if "outline" not in shared:
            shared["outline"] = {}
        
        try:
            # Validate using new hierarchical model
            outline = ReportOutline(**exec_res)
            shared["outline"]["title"] = outline.title
            shared["outline"]["sections"] = [section.model_dump() for section in outline.sections]
            shared["outline"]["object"] = outline
            
            # Also store legacy chapters for backward compatibility
            legacy_chapters = outline.to_legacy_chapters()
            shared["outline"]["chapters"] = legacy_chapters
            
            logging.info(f"Generated outline: '{outline.title}' with {len(outline.sections)} top‑level sections")
            logging.info(f"Total leaf sections: {len(outline.flatten())}")
            
            # Print structure
            def print_section(section: Section, depth: int = 0):
                indent = "  " * depth
                logging.info(f"{indent}{section.index} {section.title} ({section.type})")
                for sub in section.subsections:
                    print_section(sub, depth + 1)
            
            for section in outline.sections:
                print_section(section)
            
            # Save outline to output folder
            output_dir = shared.get("input", {}).get("output_dir", "./output")
            if output_dir:
                outline_path = outline_serializer.save_outline(
                    outline,
                    file_path=os.path.join(output_dir, "outline.yaml"),
                    format="yaml"
                )
                logging.info(f"Outline saved to: {outline_path}")
            
        except Exception as e:
            # Fallback: try legacy format
            try:
                legacy_outline = ReportOutline(**exec_res)  # This will use legacy if chapters present
                shared["outline"]["title"] = legacy_outline.title
                shared["outline"]["chapters"] = legacy_outline.chapters
                shared["outline"]["object"] = legacy_outline
                logging.info(f"Generated legacy outline: '{legacy_outline.title}' with {len(legacy_outline.chapters)} chapters")
            except Exception as e2:
                raise ValueError(f"Invalid outline structure: {e}. Fallback also failed: {e2}")
        
        return "default"


class WriterNode(BatchNode):
    """Node for writing leaf sections (batch processing)."""
    
    def __init__(self, max_retries: int = 3):
        super().__init__(max_retries=max_retries)
    
    def prep(self, shared: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare batch items (leaf sections to write)."""
        outline_obj = shared.get("outline", {}).get("object")
        if not outline_obj:
            # Fallback to legacy chapters
            chapters = shared.get("outline", {}).get("chapters", [])
            if not chapters:
                raise ValueError("No outline available. Run ArchitectNode first.")
            # Convert legacy chapters to leaf sections
            leaf_sections = []
            for chapter in chapters:
                leaf_sections.append({
                    "section": Section(
                        type=SectionType.CHAPTER,
                        index=str(chapter.index),
                        title=chapter.title,
                        description=chapter.description,
                        subsections=[]
                    ),
                    "is_legacy": True,
                    "chapter": chapter
                })
        else:
            # Use hierarchical outline
            leaf_sections = outline_obj.flatten()
        
        # Progress reporting
        total_sections = len(leaf_sections)
        logging.info(f"Starting to write {total_sections} leaf sections...")
        
        report_title = shared.get("outline", {}).get("title", "Report")
        analysis_summary = shared.get("analysis", {}).get("summary", "")
        raw_content = shared.get("materials", {}).get("raw_content", "")
        
        # Prepare context for each leaf section
        batch_items = []
        for i, leaf in enumerate(leaf_sections):
            if isinstance(leaf, dict) and leaf.get("is_legacy"):
                # Legacy chapter
                chapter = leaf["chapter"]
                section = leaf["section"]
                section_path = [section.title]
            else:
                # Section object
                section = leaf
                # Build path from root
                section_path = self._get_section_path(section, outline_obj)
            
            # Get previous section summary if available
            previous_summary = ""
            if i > 0 and "writing" in shared and "sections" in shared["writing"]:
                prev_section = leaf_sections[i-1]
                prev_index = prev_section.index if hasattr(prev_section, 'index') else prev_section.get("section").index
                prev_content = shared["writing"]["sections"].get(str(prev_index), "")
                if prev_content:
                    prev_title = prev_section.title if hasattr(prev_section, 'title') else prev_section.get("section").title
                    previous_summary = f"Previous section ({prev_title}): {prev_content[:500]}..."
            
            batch_items.append({
                "section": section,
                "section_path": section_path,
                "report_title": report_title,
                "analysis_summary": analysis_summary,
                "raw_content": raw_content[:10000],  # Limit context size
                "previous_summary": previous_summary,
                "section_index": i,
                "is_leaf": True
            })
        
        return batch_items
    
    def _get_section_path(self, section: Section, outline: ReportOutline) -> List[str]:
        """Get hierarchical path from root to this section."""
        path = []
        # Simple implementation: just return parent titles
        # For now, we'll just use the section's own title
        return [section.title]
    
    def exec(self, batch_item: Dict[str, Any]) -> str:
        """Write a single leaf section."""
        section = batch_item["section"]
        section_path = batch_item["section_path"]
        
        system_prompt = """You are an Academic Writer. Write the content for the specific section described below.
- Style: 
    - Formal, academic. 
    - In a plain, rigorous tone.
    - Mainly objective style during explaination.
    - In sections need you to show personal opinions, in addition to objective analysis, you may add perspectives based on depp insight and unique analysis.
    - Method of Argumentation: Reduce the frequency of metaphorical and exemplary reasoning. Avoid using excessive metaphorical language in your descriptions. Your argumentation should be concise and powerful.
    - Expressing Viewpoints: Frequently use conceptual expressions (such as "I believe," "In my view," "I...") to articulate your unique perspectives to a potential "teacher" or reader.
- Format: 
    - Markdown with LaTeX for math ($...$). 
    - Structural Constraints: Avoid using extensive unordered lists to elaborate on ideas, and minimize the use of complex structures like tables.
- Evidence: Strictly base your content on the [Reference Materials]. Do not hallucinate.
- Structure: Include appropriate headings (## for sections, ### for subsections).
- Length: Write 500‑1500 words depending on the section's importance."""
        
        # Build hierarchical heading
        if len(section_path) == 1:
            heading_level = "##"
        elif len(section_path) == 2:
            heading_level = "###"
        else:
            heading_level = "####"
        
        user_prompt = f"""[REPORT TITLE]: {batch_item['report_title']}
[SECTION PATH]: {' → '.join(section_path)}
[SECTION TITLE]: {section.title}
[SECTION INSTRUCTIONS]: {section.description}
[SECTION TYPE]: {section.type}
[SECTION INDEX]: {section.index}

[CONTEXT / PREVIOUS SECTION SUMMARY]:
{batch_item['previous_summary']}

[REFERENCE MATERIALS]:
{batch_item['raw_content']}"""
        
        response = call_llm_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=False,
            max_retries=self.max_retries
        )
        
        # Add appropriate heading
        heading = f"{heading_level} {section.index} {section.title}"
        section_content = f"{heading}\n\n{response}"
        
        # Log section completion with timestamp
        logging.info(f"Written section {section.index}: {section.title} ({len(section_content)} characters)")
        
        return section_content
    
    def post(self, shared: Dict[str, Any], prep_res: List[Dict[str, Any]], exec_res: List[str]) -> str:
        """Store written sections in shared store."""
        if "writing" not in shared:
            shared["writing"] = {"sections": {}, "chapters": {}}
        
        total_chars = 0
        sections_written = []
        
        # Store each section
        for i, section_content in enumerate(exec_res):
            section = prep_res[i]["section"]
            section_index = section.index
            
            shared["writing"]["sections"][str(section_index)] = section_content
            
            # Also store in legacy chapters format for backward compatibility
            # Use integer index (1‑based) for chapters, matching to_legacy_chapters order
            chapter_index = i + 1
            shared["writing"]["chapters"][str(chapter_index)] = section_content
            
            total_chars += len(section_content)
            sections_written.append(section_index)
        
        # Log summary of all sections written
        logging.info(f"Completed writing {len(exec_res)} sections: {', '.join(sorted(sections_written))}")
        logging.info(f"Total characters written: {total_chars}")
        
        return "default"


class AssembleReportNode(Node):
    """Node for assembling final report from written chapters."""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare by getting chapters, outline, and output directory."""
        writing = shared.get("writing", {})
        chapters_content = writing.get("chapters", {})
        outline = shared.get("outline", {})
        report_title = outline.get("title", "Report")
        output_dir = shared.get("input", {}).get("output_dir", "./output")
        
        if not chapters_content:
            raise ValueError("No chapters written. Run WriterNode first.")
        
        return {
            "chapters_content": chapters_content,
            "report_title": report_title,
            "outline": outline,
            "output_dir": output_dir
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
        output_dir = prep_res["output_dir"]
        output_path = save_report(
            content=exec_res,
            report_title=report_title,
            output_dir=output_dir
        )
        
        shared["output"]["path"] = output_path
        
        logging.info(f"Assembled report: {report_title}")
        logging.info(f"Saved to: {output_path}")
        logging.info(f"Report length: {len(exec_res)} characters")
        
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
        logging.info(exec_res)
        return "default"