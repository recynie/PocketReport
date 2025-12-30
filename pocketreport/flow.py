"""
Flow orchestration for the academic report writing system.
"""
from pocketreport.pocketflow import Flow
from pocketreport.nodes import (
    LoadMaterialsNode,
    AnalystNode,
    ArchitectNode,
    WriterNode,
    AssembleReportNode,
    PrintSummaryNode
)


def create_academic_report_flow() -> Flow:
    """
    Create and return the academic report writing flow.
    
    Returns:
        Flow object configured for academic report writing
    """
    # Create nodes
    load_materials_node = LoadMaterialsNode()
    analyst_node = AnalystNode(max_retries=3)
    architect_node = ArchitectNode(max_retries=3)
    writer_node = WriterNode(max_retries=3)
    assemble_report_node = AssembleReportNode()
    print_summary_node = PrintSummaryNode()
    
    # Connect nodes in sequence
    load_materials_node >> analyst_node
    analyst_node >> architect_node
    architect_node >> writer_node
    writer_node >> assemble_report_node
    assemble_report_node >> print_summary_node
    
    # Create flow starting with load materials node
    flow = Flow(start=load_materials_node)
    
    return flow


def create_minimal_flow() -> Flow:
    """
    Create a minimal flow for testing (skips writing chapters).
    
    Returns:
        Flow object for testing
    """
    load_materials_node = LoadMaterialsNode()
    analyst_node = AnalystNode(max_retries=2)
    architect_node = ArchitectNode(max_retries=2)
    print_summary_node = PrintSummaryNode()
    
    load_materials_node >> analyst_node
    analyst_node >> architect_node
    architect_node >> print_summary_node
    
    return Flow(start=load_materials_node)


def create_outline_only_flow() -> Flow:
    """
    Create a flow that only generates the outline (for planning).
    
    Returns:
        Flow object for outline generation
    """
    load_materials_node = LoadMaterialsNode()
    analyst_node = AnalystNode(max_retries=2)
    architect_node = ArchitectNode(max_retries=2)
    
    load_materials_node >> analyst_node
    analyst_node >> architect_node
    
    return Flow(start=load_materials_node)


# Example usage
if __name__ == "__main__":
    print("Testing flow creation...")
    
    # Create a test flow
    flow = create_academic_report_flow()
    
    # Create shared store with test data
    shared = {
        "input": {
            "topic": "Machine Learning in Healthcare",
            "materials_dir": "./test_materials"
        }
    }
    
    print("Flow created successfully")
    print(f"Flow start node: {flow.start_node.__class__.__name__}")
    
    # Note: To actually run the flow, you would need:
    # 1. Create a test_materials directory with markdown files
    # 2. Set LLM_API_KEY environment variable
    # 3. Call flow.run(shared)
    
    print("\nTo run the flow:")
    print("1. Create a 'test_materials' directory with markdown files")
    print("2. Set LLM_API_KEY environment variable")
    print("3. Call: flow.run(shared)")