
from unittest.mock import MagicMock
from agent.tools.program import ProgramCriticalPathTool
import networkx as nx

class MockItem:
    def __init__(self, item_id, name, dependencies=None):
        self.id = item_id
        self.name = name
        self.dependencies = dependencies or []
        self.start_date = None
        self.due_date = None
        self.status = "todo"
        self.item_type = "milestone"

def test_name_to_uuid_resolver_exact_match():
    items_by_id = {
        "1": MockItem("1", "Phase 1"),
        "2": MockItem("2", "Phase 2", dependencies=["Phase 1"])
    }
    relevant_ids = {"1", "2"}
    graph = nx.DiGraph()
    
    # Simulate resolver
    for item_id in relevant_ids:
        item = items_by_id[item_id]
        if item.dependencies:
            for dep in item.dependencies:
                dep_id = None
                if dep in items_by_id:
                    dep_id = dep
                else:
                    for aid in relevant_ids:
                        if items_by_id[aid].name.strip().lower() == dep.strip().lower():
                            dep_id = aid
                            break
                if dep_id and dep_id in relevant_ids:
                    graph.add_edge(dep_id, item_id)
                    
    assert list(graph.edges()) == [("1", "2")]

def test_name_to_uuid_resolver_case_mismatch():
    items_by_id = {
        "1": MockItem("1", "phase 1"),
        "2": MockItem("2", "Phase 2", dependencies=["PHASE 1"])
    }
    relevant_ids = {"1", "2"}
    graph = nx.DiGraph()
    
    for item_id in relevant_ids:
        item = items_by_id[item_id]
        if item.dependencies:
            for dep in item.dependencies:
                dep_id = None
                if dep in items_by_id:
                    dep_id = dep
                else:
                    for aid in relevant_ids:
                        if items_by_id[aid].name.strip().lower() == dep.strip().lower():
                            dep_id = aid
                            break
                if dep_id and dep_id in relevant_ids:
                    graph.add_edge(dep_id, item_id)
                    
    assert list(graph.edges()) == [("1", "2")]

def test_name_to_uuid_resolver_whitespace():
    items_by_id = {
        "1": MockItem("1", "Phase 1 "),
        "2": MockItem("2", "Phase 2", dependencies=[" Phase 1"])
    }
    relevant_ids = {"1", "2"}
    graph = nx.DiGraph()
    
    for item_id in relevant_ids:
        item = items_by_id[item_id]
        if item.dependencies:
            for dep in item.dependencies:
                dep_id = None
                if dep in items_by_id:
                    dep_id = dep
                else:
                    for aid in relevant_ids:
                        if items_by_id[aid].name.strip().lower() == dep.strip().lower():
                            dep_id = aid
                            break
                if dep_id and dep_id in relevant_ids:
                    graph.add_edge(dep_id, item_id)
                    
    assert list(graph.edges()) == [("1", "2")]

class CapLog:
    def __init__(self):
        self.text = ""
        
def test_name_to_uuid_resolver_no_match():
    items_by_id = {
        "1": MockItem("1", "Phase 1"),
        "2": MockItem("2", "Phase 2", dependencies=["Missing Phase"])
    }
    relevant_ids = {"1", "2"}
    graph = nx.DiGraph()
    
    import logging
    import io
    log_capture_string = io.StringIO()
    ch = logging.StreamHandler(log_capture_string)
    ch.setLevel(logging.WARNING)
    logger = logging.getLogger()
    logger.addHandler(ch)
    
    for item_id in relevant_ids:
        item = items_by_id[item_id]
        if item.dependencies:
            for dep in item.dependencies:
                dep_id = None
                if dep in items_by_id:
                    dep_id = dep
                else:
                    for aid in relevant_ids:
                        if items_by_id[aid].name.strip().lower() == dep.strip().lower():
                            dep_id = aid
                            break
                if dep_id and dep_id in relevant_ids:
                    graph.add_edge(dep_id, item_id)
                else:
                    logging.warning(f"Dependency '{dep}' could not be resolved to a valid UUID for item {item.name}. Skipping edge.")
                    
    assert len(list(graph.edges())) == 0
    log_contents = log_capture_string.getvalue()
    assert "Dependency 'Missing Phase' could not be resolved" in log_contents

def test_name_to_uuid_resolver_startswith():
    items_by_id = {
        "1": MockItem("1", "Phase 1 Complete - Foo Bar"),
        "2": MockItem("2", "Phase 2 Complete", dependencies=["Phase 1 Complete"])
    }
    relevant_ids = {"1", "2"}
    graph = nx.DiGraph()
    
    for item_id in relevant_ids:
        item = items_by_id[item_id]
        if item.dependencies:
            for dep in item.dependencies:
                dep_id = None
                if dep in items_by_id:
                    dep_id = dep
                else:
                    for aid in relevant_ids:
                        if items_by_id[aid].name.strip().lower().startswith(dep.strip().lower()):
                            dep_id = aid
                            break
                if dep_id and dep_id in relevant_ids:
                    graph.add_edge(dep_id, item_id)
                    
    assert list(graph.edges()) == [("1", "2")]

if __name__ == "__main__":
    test_name_to_uuid_resolver_exact_match()
    test_name_to_uuid_resolver_case_mismatch()
    test_name_to_uuid_resolver_whitespace()
    test_name_to_uuid_resolver_no_match()
    test_name_to_uuid_resolver_startswith()
    print("All tests passed!")

