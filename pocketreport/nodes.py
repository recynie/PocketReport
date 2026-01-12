"""
Node implementations for the academic report writing system.
"""
import json
import os
import logging
from typing import Dict, Any, List, Optional
from pocketflow import Node, BatchNode
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
    outline_serializer,
    prompt_loader,
    metadata_loader
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
        system_prompt = prompt_loader.get_system_prompt("analyst")
        user_prompt = prompt_loader.get_user_prompt(
            "analyst",
            raw_content=raw_content[:127000]  # Limit context size
        )
        
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
        system_prompt = prompt_loader.get_system_prompt("architect")
        user_prompt = prompt_loader.get_user_prompt(
            "architect",
            topic=inputs['topic'],
            analysis_summary=inputs['analysis_summary']
        )
        
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
                # Calculate heading level based on index dot count
                level = section.index.count('.') + 1
                logging.info(f"{indent}{section.index} {section.title} (h{level})")
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
        
        system_prompt = prompt_loader.get_system_prompt("writer")
        
        # Calculate heading level based on index dot count
        # Use the Section's built-in method
        heading_markdown = section.get_heading_markdown(include_index=True)
        
        user_prompt = prompt_loader.get_user_prompt(
            "writer",
            report_title=batch_item['report_title'],
            section_path=' → '.join(section_path),
            section_title=section.title,
            section_instructions=section.description,
            section_index=section.index,
            heading_level=section.get_heading_level(),
            previous_summary=batch_item['previous_summary'],
            raw_content=batch_item['raw_content']
        )
        
        response = call_llm_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=False,
            max_retries=self.max_retries
        )
        
        # IMPORTANT: Check if LLM already included a heading in the response
        # We need to detect if the response already contains a heading at the appropriate level
        response_stripped = response.strip()
        
        # Check if response starts with any markdown heading (1-6 # symbols)
        # Also check if it contains the section title in a heading
        has_heading = False
        lines = response_stripped.split('\n')
        if lines and lines[0].startswith('#'):
            # First line is a heading, check if it matches expected heading level
            first_line = lines[0]
            # Count # symbols to determine heading level
            heading_level = len(first_line) - len(first_line.lstrip('#'))
            expected_level = section.get_heading_level()
            
            # If the heading level matches or is close, assume LLM included proper heading
            if abs(heading_level - expected_level) <= 1:
                has_heading = True
                # Also check if the heading contains the section title
                heading_text = first_line.lstrip('#').strip()
                if section.title.lower() in heading_text.lower():
                    # Good match, use as-is
                    section_content = response
                else:
                    # Heading exists but doesn't match section title
                    # We'll still use it but log a warning
                    logging.warning(f"Section {section.index} heading mismatch: '{heading_text}' vs '{section.title}'")
                    section_content = response
            else:
                # Heading level mismatch, we should add our own heading
                has_heading = False
        
        if not has_heading:
            # Add heading before content
            section_content = f"{heading_markdown}\n\n{response}"
        
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
    """Node for assembling final report from written chapters and adding metadata."""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare by getting chapters, outline, analysis, and output directory."""
        writing = shared.get("writing", {})
        chapters_content = writing.get("chapters", {})
        outline = shared.get("outline", {})
        report_title = outline.get("title", "Report")
        analysis_summary = shared.get("analysis", {}).get("summary", "")
        output_dir = shared.get("input", {}).get("output_dir", "./output")
        topic = shared.get("input", {}).get("topic", "Report")
        
        if not chapters_content:
            raise ValueError("No chapters written. Run WriterNode first.")
        
        return {
            "chapters_content": chapters_content,
            "report_title": report_title,
            "outline": outline,
            "analysis_summary": analysis_summary,
            "output_dir": output_dir,
            "topic": topic
        }
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Assemble complete report and generate metadata."""
        chapters_content = inputs["chapters_content"]
        report_title = inputs["report_title"]
        analysis_summary = inputs["analysis_summary"]
        outline = inputs["outline"]
        
        # Sort chapters by index
        sorted_indices = sorted(chapters_content.keys(), key=lambda x: int(x))
        
        # Assemble report - DO NOT include report title as h1
        # Top-level sections (index "1", "2", etc.) are already h1
        lines = []
        
        for idx in sorted_indices:
            content = chapters_content[idx]
            lines.append(content)
            lines.append("\n")  # Add blank line between chapters
        
        report_content = "\n".join(lines)
        
        # Generate metadata (title, subtitle, abstract)
        # For now, use simple defaults, but this could be LLM-generated
        metadata = metadata_loader.update_metadata(
            title=report_title,
            subtitle=inputs.get("topic", ""),
            abstract=analysis_summary[:300] if analysis_summary else ""
        )
        
        return {
            "report_content": report_content,
            "metadata": metadata,
            "report_title": report_title
        }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """Store and save final report with metadata."""
        if "output" not in shared:
            shared["output"] = {}
        
        report_content = exec_res["report_content"]
        metadata = exec_res["metadata"]
        report_title = exec_res["report_title"]
        output_dir = prep_res["output_dir"]
        
        # Generate frontmatter
        frontmatter = metadata_loader.generate_frontmatter(metadata)
        
        # Append frontmatter to report content
        final_report = metadata_loader.append_frontmatter_to_report(frontmatter, report_content)
        
        shared["output"]["report"] = final_report
        shared["output"]["metadata"] = metadata
        
        # Save to file
        output_path = save_report(
            content=final_report,
            report_title=report_title,
            output_dir=output_dir
        )
        
        shared["output"]["path"] = output_path
        
        logging.info(f"Assembled report: {report_title}")
        logging.info(f"Added metadata: title='{metadata.get('title')}', subtitle='{metadata.get('subtitle')}'")
        logging.info(f"Saved to: {output_path}")
        logging.info(f"Final report length (with metadata): {len(final_report)} characters")
        
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