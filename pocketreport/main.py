"""
Main entry point for the academic report writing system.
"""
import argparse
import sys
import os
from typing import Optional, Dict, Any

from pocketreport.flow import create_academic_report_flow, create_minimal_flow, create_outline_only_flow
from pocketreport.utils import load_markdown_files

from dotenv import load_dotenv
load_dotenv()

def run_report_generation(
    topic: str,
    materials_dir: str,
    output_dir: Optional[str] = None,
    minimal: bool = False,
    outline_only: bool = False
) -> Dict[str, Any]:
    """
    Run the academic report generation pipeline.
    
    Args:
        topic: Report topic
        materials_dir: Directory containing markdown files
        output_dir: Directory for output files (default: ./output)
        minimal: If True, run minimal flow (no chapter writing)
        outline_only: If True, only generate outline
        
    Returns:
        Shared store with results
    """
    # Validate materials directory
    if not os.path.exists(materials_dir):
        raise FileNotFoundError(f"Materials directory not found: {materials_dir}")
    
    # Set output directory
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        # Update environment for save_report utility
        os.environ.setdefault("OUTPUT_DIR", output_dir)
    
    # Create shared store
    shared = {
        "input": {
            "topic": topic,
            "materials_dir": materials_dir
        }
    }
    
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
        
        return shared
        
    except Exception as e:
        print(f"\n❌ Report generation failed: {e}")
        raise


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
            outline_only=args.outline_only
        )
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()