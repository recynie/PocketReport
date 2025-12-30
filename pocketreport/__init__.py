"""
Academic Report Writing System - A multi-agent system for generating academic reports from markdown materials.

This package implements a flow-based multi-agent system with three specialized agents:
1. Analyst Agent: Reads raw markdown and generates structured summary
2. Architect Agent: Creates report outline based on topic and analysis
3. Writer Agent: Writes chapters one by one

The system follows the Pocket Flow framework for orchestration.
"""

__version__ = "0.1.0"
__author__ = "Academic Report Writing System"
__description__ = "Multi-agent system for academic report generation"

# Core components
from .nodes import (
    LoadMaterialsNode,
    AnalystNode,
    ArchitectNode,
    WriterNode,
    AssembleReportNode,
    PrintSummaryNode
)

from .flow import (
    create_academic_report_flow,
    create_minimal_flow,
    create_outline_only_flow
)

from .utils import (
    # LLM utilities
    call_llm,
    call_llm_with_retry,
    
    # Markdown utilities
    load_markdown_files,
    load_markdown_file,
    get_markdown_files_info,
    
    # Report utilities
    save_report,
    save_chapter,
    save_outline,
    
    # Models
    Chapter,
    ReportOutline,
    AnalysisSummary,
    Report,
)

# Main entry point
from .main import run_report_generation, main

__all__ = [
    # Nodes
    'LoadMaterialsNode',
    'AnalystNode',
    'ArchitectNode',
    'WriterNode',
    'AssembleReportNode',
    'PrintSummaryNode',
    
    # Flows
    'create_academic_report_flow',
    'create_minimal_flow',
    'create_outline_only_flow',
    
    # Utilities
    'call_llm',
    'call_llm_with_retry',
    'load_markdown_files',
    'load_markdown_file',
    'get_markdown_files_info',
    'save_report',
    'save_chapter',
    'save_outline',
    
    # Models
    'Chapter',
    'ReportOutline',
    'AnalysisSummary',
    'Report',
    
    # Main functions
    'run_report_generation',
    'main',
]