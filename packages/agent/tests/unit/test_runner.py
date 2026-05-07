from agent.memory.working import WorkingMemory
from agent.prompts.builder import build_system_prompt
from agent.tools.wrapper import wrap_untrusted


def test_prompt_builder():
    prompt = build_system_prompt(persona_pack="sme", program_context="Test Program")
    assert "<layer name=\"identity\">" in prompt
    assert "Test Program" in prompt

def test_working_memory():
    wm = WorkingMemory()
    assert wm.trim([1, 2, 3]) == [1, 2, 3]

def test_wrapper():
    res = wrap_untrusted("bad data")
    assert "<untrusted>" in res
    assert "bad data" in res
