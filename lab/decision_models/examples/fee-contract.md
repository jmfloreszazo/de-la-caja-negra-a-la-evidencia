# Synthetic fee capability contract v1

Classification: synthetic, unapproved. This is a newly written bounded interpretation of the public fee example, not a replacement protected oracle. Context: [legacy implementation](../../legacy/fee.cob) and [public cases](../../contracts/cases.json). Neither was executed to obtain this example's expected results.

The decision input is a **parsed** object with integer `amountCents`, integer `rateBps`, and string `customerActive`. Reject unknown keys and wrong types as profile failures. Missing inputs are inconclusive. This profile does not parse COBOL PIC bytes, EBCDIC, whitespace, record lengths, or malformed numeric text; those require separate adapter tests.

Within parsed inputs, a negative amount or amount over 99,999,999, a negative rate or rate over 10,000, or an active flag other than Y/N yields `INVALID` and zero fee. Domain-invalid values have priority over an inactive flag. Otherwise N yields `REJECT` and zero fee. Otherwise calculate fee cents = amount cents * basis points / 10,000, rounded to integer cents with HALF_UP (positive half ties round up). A valid active amount over 1,000,000 yields `REVIEW`; at or below the boundary it yields `APPROVE`. These business result labels are not authorization actions. Numeric safety bounds in the profile reject integers with more than 18 digits before business evaluation.

The expected cases are manually specified below the model abstraction, with distinct inputs from the protected oracle. Boundary arithmetic includes 250 * 20 / 10,000 = 0.5 -> 1 and 750 * 20 / 10,000 = 1.5 -> 2. No binary float or ambient decimal context is used by the tool.

The process example observes only `Start -> Validate -> Decide -> Record -> End` or `Start -> Validate -> Rejected -> End`. It checks allowed sequential state observations, not which branch the fee result mandates. No branch guard, decision invocation, external side effect, durable event, actor identity, timing, concurrency, gateway, compensation, or retry semantics is inferred.

An accountable owner must approve a scoped, versioned baseline independently before using these artifacts for acceptance. Diagrams, ADRs, hashes, and an `approved` JSON claim alone do not establish that authority.
