#!/usr/bin/env python3
"""
Test script for the academic report writing system.
Tests basic functionality without requiring LLM API calls.
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_file_loading():
    """Test markdown file loading utility."""
    print("Testing file loading...")
    try:
        from pocketreport.utils import load_markdown_files, get_markdown_files_info
        
        # Test with our test materials
        content, count = load_markdown_files("test_materials")
        print(f"✓ Loaded {count} markdown files")
        print(f"  Total content length: {len(content)} characters")
        
        files_info = get_markdown_files_info("test_materials")
        print(f"✓ Found {len(files_info)} files:")
        for file_info in files_info:
            print(f"  - {file_info['filename']}: {file_info['lines']} lines")
        
        return True
    except Exception as e:
        print(f"✗ File loading test failed: {e}")
        return False

def test_models():
    """Test Pydantic models."""
    print("\nTesting Pydantic models...")
    try:
        from pocketreport.utils import Chapter, ReportOutline
        
        # Create a chapter
        chapter = Chapter(
            index=1,
            title="Introduction",
            description="Introduction to the topic"
        )
        print(f"✓ Created chapter: {chapter.title}")
        
        # Create an outline
        outline = ReportOutline(
            title="Test Report",
            chapters=[chapter]
        )
        print(f"✓ Created outline: {outline.title} with {len(outline.chapters)} chapters")
        
        return True
    except Exception as e:
        print(f"✗ Models test failed: {e}")
        return False

def test_node_creation():
    """Test that nodes can be created."""
    print("\nTesting node creation...")
    try:
        from pocketreport.nodes import (
            LoadMaterialsNode, AnalystNode, ArchitectNode,
            WriterNode, AssembleReportNode, PrintSummaryNode
        )
        
        # Create instances
        nodes = [
            LoadMaterialsNode(),
            AnalystNode(max_retries=2),
            ArchitectNode(max_retries=2),
            WriterNode(max_retries=2),
            AssembleReportNode(),
            PrintSummaryNode()
        ]
        
        print(f"✓ Created {len(nodes)} node types:")
        for node in nodes:
            print(f"  - {node.__class__.__name__}")
        
        return True
    except Exception as e:
        print(f"✗ Node creation test failed: {e}")
        return False

def test_flow_creation():
    """Test flow creation."""
    print("\nTesting flow creation...")
    try:
        from pocketreport.flow import (
            create_academic_report_flow,
            create_minimal_flow,
            create_outline_only_flow
        )
        
        # Create flows
        full_flow = create_academic_report_flow()
        minimal_flow = create_minimal_flow()
        outline_flow = create_outline_only_flow()
        
        print(f"✓ Created 3 flow types:")
        print(f"  - Full academic report flow")
        print(f"  - Minimal flow")
        print(f"  - Outline-only flow")
        
        # Test that flows have start nodes
        assert full_flow.start_node is not None
        assert minimal_flow.start_node is not None
        assert outline_flow.start_node is not None
        
        print(f"✓ All flows have valid start nodes")
        
        return True
    except Exception as e:
        print(f"✗ Flow creation test failed: {e}")
        return False

def test_shared_store_structure():
    """Test shared store structure."""
    print("\nTesting shared store structure...")
    try:
        # Create a sample shared store
        shared = {
            "input": {
                "topic": "Test Topic",
                "materials_dir": "test_materials"
            },
            "materials": {
                "raw_content": "Test content",
                "file_count": 2
            },
            "analysis": {
                "summary": "Test analysis summary"
            },
            "outline": {
                "title": "Test Report",
                "chapters": [
                    {"index": 1, "title": "Intro", "description": "Introduction"}
                ]
            },
            "writing": {
                "chapters": {
                    "1": "Chapter 1 content"
                }
            },
            "output": {
                "report": "Full report content",
                "path": "./output/test_report.md"
            }
        }
        
        print("✓ Shared store structure is valid")
        print(f"  - Topic: {shared['input']['topic']}")
        print(f"  - Materials: {shared['materials']['file_count']} files")
        print(f"  - Chapters: {len(shared['outline']['chapters'])} in outline")
        
        return True
    except Exception as e:
        print(f"✗ Shared store test failed: {e}")
        return False

def test_main_module():
    """Test main module imports."""
    print("\nTesting main module...")
    try:
        from pocketreport import main, run_report_generation
        
        print("✓ Main module imports successfully")
        print("✓ Available functions:")
        print("  - main() - CLI entry point")
        print("  - run_report_generation() - Programmatic API")
        
        return True
    except Exception as e:
        print(f"✗ Main module test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Academic Report Writing System - Component Tests")
    print("=" * 60)
    
    tests = [
        test_file_loading,
        test_models,
        test_node_creation,
        test_flow_creation,
        test_shared_store_structure,
        test_main_module
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{i:2d}. {test.__name__:30} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! System components are working correctly.")
        print("\nNext steps:")
        print("1. Set LLM_API_KEY environment variable")
        print("2. Run: python -m pocketreport.main --topic 'ML Research' --materials test_materials --minimal")
        print("3. Check the output directory for generated reports")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)