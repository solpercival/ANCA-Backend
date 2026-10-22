"""A chat reply that answers the question and then adds the refusal sentence keeps
only the answer; a reply that is only the refusal stays a refusal."""

from rag_engine.orchestrator import Orchestrator

REFUSAL = "The documentation does not cover this."


def test_refusal_is_dropped_only_when_there_is_an_answer():
    answer = "Add at least three control points between splineon and splineoff."

    assert Orchestrator._drop_stray_refusal(f"{answer} {REFUSAL}") == answer
    lowercase = f"{answer} the documentation does not cover this"
    assert Orchestrator._drop_stray_refusal(lowercase) == answer
    assert Orchestrator._drop_stray_refusal(REFUSAL) == REFUSAL
    assert Orchestrator._drop_stray_refusal(answer) == answer
