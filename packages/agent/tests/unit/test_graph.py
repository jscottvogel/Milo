from agent.graph import build_graph


def test_graph_compile():
    graph = build_graph()
    assert graph is not None

def test_perceive_node():
    from agent.graph import perceive_node
    state = {"turn_count": 0}
    new_state = perceive_node(state)
    assert new_state["turn_count"] == 1

def test_plan_node():
    from agent.graph import plan_node
    assert plan_node({"test": 1}) == {"test": 1}

def test_act_node():
    from agent.graph import act_node
    assert act_node({"test": 1}) == {"test": 1}

def test_observe_node():
    from agent.graph import observe_node
    assert observe_node({"test": 1}) == {"test": 1}

def test_reflect_node():
    from agent.graph import reflect_node
    assert reflect_node({"test": 1}) == {"test": 1}
