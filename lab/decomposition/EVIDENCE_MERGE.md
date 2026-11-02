# Static/runtime dependency evidence union (synthetic)

Run `python3 -m unittest -v test_evidence_merge.py` from this directory.

This is an **offline research contract**, not static parsing of real COBOL/JCL/CICS or live production tracing. The input explicitly identifies the evidence source (`static`, `runtime`, `domain-expert`), observation ID, confidence and an asserted atomic group.

Matching independent observations remain separately traceable. Contradictory atomic-group assertions yield `conflict=true` and `confidence=unknown`; a missing runtime observation does **not** imply absence of a dependency. Treat all unknown and conflicting crossing dependencies as **REJECT** in downstream boundary gates. The current `oracle.py` does not yet consume this merged representation: integrating it safely, including hyperedge transaction membership and negative tests, is a separate required acceptance gate.

No financial execution, IBM Z measurement or migration claim. See issue #32 and PR #50.
