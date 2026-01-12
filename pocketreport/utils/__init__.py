"""
Utility functions for the academic report writing system.
"""

from .call_llm import call_llm, call_llm_with_retry
from .load_markdown import load_markdown_files, load_markdown_file, get_markdown_files_info
from .load_materials import load_materials
from .save_report import save_report, save_chapter, save_outline
from .save_intermediate import (
    save_intermediate,
    save_analysis_summary,
    save_outline_file,
    save_conversion_info,
    load_intermediate
)
from .outline_serializer import outline_serializer
from .prompt_loader import (
    get_prompt,
    get_system_prompt,
    get_user_prompt_template,
    get_user_prompt,
    clear_cache as clear_prompt_cache
)
from .metadata_loader import (
    load_metadata_template,
    update_metadata,
    metadata_to_yaml,
    generate_frontmatter,
    append_frontmatter_to_report
)
from .models import (
    Chapter,
    ReportOutline,
    AnalysisSummary,
    Report,
    Section,
    SectionType
)

__all__ = [
    # LLM utilities
    'call_llm',
    'call_llm_with_retry',
    
    # Markdown utilities
    'load_markdown_files',
    'load_markdown_file',
    'get_markdown_files_info',
    
    # File conversion utilities
    'load_materials',
    
    # Report utilities
    'save_report',
    'save_chapter',
    'save_outline',
    
    # Intermediate results utilities
    'save_intermediate',
    'save_analysis_summary',
    'save_outline_file',
    'save_conversion_info',
    'load_intermediate',
    
    # Outline serialization
    'outline_serializer',
    
    # Prompt loading utilities
    'get_prompt',
    'get_system_prompt',
    'get_user_prompt_template',
    'get_user_prompt',
    'clear_prompt_cache',
    
    # Metadata loading utilities
    'load_metadata_template',
    'update_metadata',
    'metadata_to_yaml',
    'generate_frontmatter',
    'append_frontmatter_to_report',
    
    # Models
    'Chapter',
    'ReportOutline',
    'AnalysisSummary',
    'Report',
    'Section',
    'SectionType',
]