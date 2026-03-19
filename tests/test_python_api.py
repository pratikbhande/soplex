"""
Tests for the native Python Graph Builder API.
"""
import pytest
from soplex import PythonGraphBuilder
from soplex.compiler.graph import NodeType

def test_linear_graph_building():
    """Test building a simple linear graph without branches."""
    builder = PythonGraphBuilder(name="Linear Test")
    
    # Add steps
    builder.add_llm_step(id="start_chat", action="Say hello")
    
    def my_code_handler(state):
        state["processed"] = True
        return state
        
    builder.add_code_step(
        id="process_data", 
        action="Process the data", 
        handler_func=my_code_handler
    )
    
    builder.add_end_step(id="finish", action="Done")
    
    # Add manual linear edges
    builder.add_edge(from_node="start_chat", to_node="process_data")
    builder.add_edge(from_node="process_data", to_node="finish")
    
    # Build resulting graph
    graph = builder.build()
    
    assert graph.name == "Linear Test"
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    
    # Check start node logic
    assert graph.start_node_id == "start_chat"
    
    # Verify the specific node got the python handler
    process_node = graph.get_node("process_data")
    assert process_node.type == NodeType.CODE
    assert process_node.handler is not None
    
    # Verify state execution by manually calling the handler
    test_state = {"processed": False}
    result_state = process_node.handler(test_state)
    assert result_state["processed"] is True


def test_branching_graph_building():
    """Test building a graph with complex branching."""
    builder = PythonGraphBuilder(name="Branch Test")
    
    builder.add_llm_step(id="step_1", action="Start")
    
    def is_valid(state):
        return state.get("valid", False)
        
    # The branch node is just a node
    builder.add_branch_step(
        id="check_valid",
        action="Check if valid",
    )
    
    builder.add_end_step(id="success_end", action="Success")
    builder.add_end_step(id="fail_end", action="Fail")
    
    # Wire the start node to the branch node
    builder.add_edge(from_node="step_1", to_node="check_valid")
    
    # Explicitly wire branch conditions using native callables
    builder.add_edge(
        from_node="check_valid", 
        to_node="success_end", 
        condition_func=is_valid, 
        label="YES"
    )
    builder.add_edge(
        from_node="check_valid", 
        to_node="fail_end", 
        condition_func=lambda state: not is_valid(state), 
        label="NO"
    )
    
    graph = builder.build()
    
    # 4 Nodes: step_1, check_valid, success_end, fail_end
    # 3 Edges: step_1 -> check_valid, check_valid -> success_end (YES), check_valid -> fail_end (NO)
    assert len(graph.nodes) == 4
    assert len(graph.edges) == 3
    
    # Verify branch conditions work correctly
    outgoing_edges = graph.get_outgoing_edges("check_valid")
    assert len(outgoing_edges) == 2
    
    yes_edge = next(e for e in outgoing_edges if e.to_node == "success_end")
    no_edge = next(e for e in outgoing_edges if e.to_node == "fail_end")
    
    # Test True state routing
    state_valid = {"valid": True}
    assert yes_edge.should_traverse(state_valid) is True
    assert no_edge.should_traverse(state_valid) is False
    
    # Test False state routing
    state_invalid = {"valid": False}
    assert yes_edge.should_traverse(state_invalid) is False
    assert no_edge.should_traverse(state_invalid) is True


def test_malformed_graph_validation():
    """Test that GraphBuilder catches validation errors."""
    builder = PythonGraphBuilder(name="Broken Graph")
    
    builder.add_llm_step(id="n1", action="Node 1")
    builder.add_llm_step(id="n2", action="Node 2")
    # Missing edge between n1 and n2 makes n2 an orphaned node
    
    with pytest.raises(ValueError) as excinfo:
        builder.build()
        
    assert "Orphaned nodes" in str(excinfo.value)
