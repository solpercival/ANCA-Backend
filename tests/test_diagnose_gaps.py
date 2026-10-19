"""eval/diagnose_gaps.py: whether a missed gold step's supporting text was in the
prompt the model saw (a generation gap) or not (a retrieval gap)."""

from eval.diagnose_gaps import diagnose

CONTEXT = (
    "The drive reports an emergency when it detects a fault. "
    "In the case that it is an error, recover by reinitialising the Ethercat bus.\n"
    "Restarting the system also clears the error state of the drive."
)


def test_gap_is_in_prompt_when_the_context_holds_the_gold_step():
    gold = {"am.fb.0002": {"resolution_steps": ["Reinitialise the EtherCAT bus to recover."]}}
    results = [{"code": "am.fb.0002", "steps": ["Check the drive status LEDs."]}]

    in_prompt = diagnose(results, gold, {"am.fb.0002": CONTEXT})
    absent = diagnose(results, gold, {"am.fb.0002": "Unrelated text about spindles."})

    assert in_prompt["am.fb.0002"][0]["status"] == "in_prompt_not_used"
    assert absent["am.fb.0002"][0]["status"] == "not_in_prompt"
