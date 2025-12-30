"""
Main entry point for the academic report writing system.
"""
import argparse
import sys
import os
import logging
from typing import Optional, Dict, Any

from pocketreport.flow import create_academic_report_flow, create_minimal_flow, create_outline_only_flow
from pocketreport.utils import load_markdown_files, save_intermediate

from dotenv import load_dotenv
load_dotenv()


def setup_logging(output_dir: str, log_level: int = logging.INFO) -> None:
    """
    Configure logging to write to both a file and console.
    
    Args:
        output_dir: Directory where log file will be saved (logs/pocketreport.log)
        log_level: Logging level (default: INFO)
    """
    # Create logs directory inside output directory
    logs_dir = os.path.join(output_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(logs_dir, "pocketreport.log")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    logging.info(f"Logging configured. Log file: {log_file}")

def run_report_generation(
    topic: str,
    materials_dir: str,
    output_dir: Optional[str] = None,
    minimal: bool = False,
    outline_only: bool = False,
    outline_file: Optional[str] = None,
    cache_conversions: bool = True,
    save_intermediate: bool = True
) -> Dict[str, Any]:
    """
    Run the academic report generation pipeline.
    
    Args:
        topic: Report topic
        materials_dir: Directory containing materials (markdown and other formats)
        output_dir: Directory for output files (default: ./output)
        minimal: If True, run minimal flow (no chapter writing)
        outline_only: If True, only generate outline
        outline_file: Optional path to existing outline file (YAML/JSON)
        cache_conversions: Whether to cache file conversions (default: True)
        save_intermediate: Whether to save intermediate results (analysis, outline, etc.)
        
    Returns:
        Shared store with results
    """
    # Validate materials directory
    if not os.path.exists(materials_dir):
        raise FileNotFoundError(f"Materials directory not found: {materials_dir}")
    
    # Set output directory
    if output_dir is None:
        output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Configure logging
    setup_logging(output_dir)
    
    # Update environment for save_report utility
    os.environ.setdefault("OUTPUT_DIR", output_dir)
    
    # Create shared store with extended input
    shared = {
        "input": {
            "topic": topic,
            "materials_dir": materials_dir,
            "output_dir": output_dir,
            "cache_conversions": cache_conversions,
            "save_intermediate": save_intermediate
        }
    }
    
    # Add outline file if provided
    if outline_file:
        if not os.path.exists(outline_file):
            raise FileNotFoundError(f"Outline file not found: {outline_file}")
        shared["input"]["outline_file"] = outline_file
        print(f"Using existing outline file: {outline_file}")
    
    # Choose flow based on options
    if outline_only:
        print("Running outline-only flow...")
        flow = create_outline_only_flow()
    elif minimal:
        print("Running minimal flow...")
        flow = create_minimal_flow()
    else:
        print("Running full academic report flow...")
        flow = create_academic_report_flow()
    
    # Run the flow
    try:
        flow.run(shared)
        print("\n✅ Report generation completed successfully!")
        
        # Print output path if available
        output_path = shared.get("output", {}).get("path")
        if output_path:
            print(f"📄 Report saved to: {output_path}")
        
        # Save intermediate results if requested
        if save_intermediate:
            _save_intermediate_results(shared, output_dir)
        
        return shared
        
    except Exception as e:
        print(f"\n❌ Report generation failed: {e}")
        raise


def _save_intermediate_results(shared: Dict[str, Any], output_dir: str) -> None:
    """Save intermediate results to output directory."""
    try:
        from pocketreport.utils.save_intermediate import (
            save_intermediate,
            save_analysis_summary,
            save_outline_file,
            save_conversion_info
        )
        
        # Save analysis summary
        if "analysis" in shared and "summary" in shared["analysis"]:
            save_analysis_summary(
                shared["analysis"]["summary"],
                output_dir=output_dir
            )
        
        # Save outline
        if "outline" in shared:
            outline_data = {
                "title": shared["outline"].get("title", ""),
                "sections": shared["outline"].get("sections", []),
                "chapters": shared["outline"].get("chapters", [])  # legacy
            }
            save_outline_file(
                outline_data,
                output_dir=output_dir,
                format="yaml"
            )
        
        # Save conversion info
        if "materials" in shared and "converted_files" in shared["materials"]:
            save_conversion_info(
                shared["materials"]["converted_files"],
                shared["materials"].get("dir", ""),
                output_dir=output_dir
            )
        
        # Save full shared store (excluding large raw content)
        shared_copy = {k: v for k, v in shared.items() if k != "materials" or "raw_content" not in v}
        if "materials" in shared_copy:
            shared_copy["materials"] = {k: v for k, v in shared_copy["materials"].items()
                                       if k != "raw_content"}
        
        save_intermediate(
            shared_copy,
            category="shared_store",
            output_dir=output_dir,
            format="json"
        )
        
        print("Intermediate results saved to output/intermediate/")
        
    except Exception as e:
        print(f"Warning: Could not save intermediate results: {e}")


def list_materials(materials_dir: str) -> None:
    """List markdown files in the materials directory."""
    try:
        from pocketreport.utils import get_markdown_files_info
        files_info = get_markdown_files_info(materials_dir)
        
        if not files_info:
            print(f"No markdown files found in {materials_dir}")
            return
        
        print(f"Markdown files in {materials_dir}:")
        for i, file_info in enumerate(files_info, 1):
            print(f"  {i}. {file_info['path']} ({file_info['lines']} lines, {file_info['size']} bytes)")
        
        # Try to load and show total size
        try:
            content, count = load_markdown_files(materials_dir)
            print(f"\nTotal: {count} files, {len(content)} characters")
        except:
            pass
            
    except Exception as e:
        print(f"Error listing materials: {e}")


def main():
    """Command-line interface for the academic report writing system."""
    parser = argparse.ArgumentParser(
        description="Academic Report Writing System - Generate academic reports from markdown materials",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --topic "Machine Learning" --materials ./papers
  %(prog)s --topic "Climate Change" --materials ./research --minimal
  %(prog)s --topic "Quantum Computing" --materials ./docs --outline-only
  %(prog)s --list --materials ./papers
        """
    )
    
    parser.add_argument(
        "--topic",
        type=str,
        help="Topic for the report (e.g., 'Machine Learning in Healthcare')"
    )
    
    parser.add_argument(
        "--materials",
        type=str,
        default="./materials",
        help="Directory containing markdown files (default: ./materials)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for generated reports (default: ./output)"
    )
    
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Run minimal flow (skip chapter writing, for testing)"
    )
    
    parser.add_argument(
        "--outline-only",
        action="store_true",
        help="Only generate outline (no writing)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List markdown files in materials directory and exit"
    )
    
    parser.add_argument(
        "--outline-file",
        type=str,
        help="Path to existing outline file (YAML/JSON) to skip outline generation"
    )
    
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching of file conversions"
    )
    
    parser.add_argument(
        "--no-intermediate",
        action="store_true",
        help="Do not save intermediate results (analysis, outline, etc.)"
    )
    
    parser.add_argument(
        "--env-file",
        type=str,
        help="Path to .env file for configuration"
    )
    
    args = parser.parse_args()
    
    # Load environment variables if specified
    if args.env_file:
        from dotenv import load_dotenv
        load_dotenv(args.env_file)
        print(f"Loaded environment from {args.env_file}")
    
    # Check for required LLM API key
    if not os.getenv("LLM_API_KEY") and not (args.list or args.outline_only):
        print("⚠️  Warning: LLM_API_KEY environment variable not set")
        print("   Set it with: export LLM_API_KEY=your_key_here")
        print("   Or create a .env file with LLM_API_KEY=your_key")
        print("   Continuing anyway...")
    
    # Handle list command
    if args.list:
        list_materials(args.materials)
        return
    
    # Validate required arguments for report generation
    if not args.topic:
        parser.error("--topic is required for report generation")
    
    # Run report generation
    try:
        run_report_generation(
            topic=args.topic,
            materials_dir=args.materials,
            output_dir=args.output,
            minimal=args.minimal,
            outline_only=args.outline_only,
            outline_file=args.outline_file,
            cache_conversions=not args.no_cache,
            save_intermediate=not args.no_intermediate
        )
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()