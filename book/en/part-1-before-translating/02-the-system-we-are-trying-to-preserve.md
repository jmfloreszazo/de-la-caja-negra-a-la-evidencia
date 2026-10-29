**English** · [Español](../../es/parte-1-antes-de-traducir/02-el-sistema-que-estamos-intentando-conservar.md)

[← Chapter 1 · The mainframe is not a fast box](01-the-mainframe-is-not-a-fast-box.md) · [Contents](../README.md) · [Chapter 3 · Why one-to-one conversion is not modernization →](03-why-one-to-one-conversion-is-not-modernization.md)

# Chapter 2 · The system we are trying to preserve

> [!IMPORTANT]
> **Chapter thesis.** The behaviour that matters runs through programs, data, nightly processes and people. And not everything the system does today deserves to become tomorrow's requirement.

## Memory is distributed

A legacy application contains decisions that perhaps nobody would make the same way today. Some are still necessary. Others were temporary fixes. There are behaviours the business considers essential and others it has simply tolerated for decades. Often they are all mixed together in the same execution path.

That is why I find it insufficient to start a modernization by asking how many lines of code we have. I need to know what commitments the system fulfils, with whom it fulfils them and what happens when it stops fulfilling them. The code is part of the answer. So are the data, the parameter tables, the nightly processes, the interfaces and the people who know the exceptions.

Imagine an end-of-day settlement. One program calculates amounts, another groups movements and a third generates a file for an external entity. A screen lets someone correct incidents before sending. The behaviour we must preserve runs through all of those elements. Translating the first routine correctly does not prove we have preserved the settlement.

It is one of the ideas I find most valuable in what has been written about COBOL: it brings attention back to the knowledge that sustains operations. An organization can keep depending on a system while losing the ability to explain it. For my proposal, that observation has a direct consequence: recovering knowledge must produce artifacts that can be used to decide and to verify.

A readable explanation helps. An explanation linked to a rule, an owner and a test lets us go further. Documentation stops being a parallel narrative and becomes part of the acceptance mechanism.

## Preserving behaviour does not mean preserving any result

Suppose the system has been charging an incorrect fee for years. A reimplementation that reproduces that charge is compatible with the observed behaviour. That does not make it correct with respect to business policy.

We need to separate two questions. What does the current system do? What must the system we are going to accept do? The first is answered through observation, analysis and characterization tests. The second requires an authorized decision about rules and exceptions. When the answers differ, the project includes a behaviour change that must be identified.

This distinction avoids two common mistakes. The first is silently fixing something that looked like a defect, without knowing which consumer depended on it. The second is elevating every historical behaviour to a permanent requirement. Both can introduce problems that a superficial comparison will not detect.

My preferred unit of work is a bounded capability: a calculation, a decision, an exchange or a state transition we can observe and explain. Its size must allow us to build enough evidence and control the change. It does not have to match a whole program or the microservice someone drew at the beginning.

At the end of this phase we should be able to describe what we preserve, what we deliberately change and what we still do not know. The last category has value too. A recorded uncertainty can be investigated; an uncertainty disguised as certainty ends up in the design.

> **A recorded uncertainty can be investigated. An uncertainty disguised as certainty ends up in the design.**

---

[← Chapter 1 · The mainframe is not a fast box](01-the-mainframe-is-not-a-fast-box.md) · [Contents](../README.md) · [Chapter 3 · Why one-to-one conversion is not modernization →](03-why-one-to-one-conversion-is-not-modernization.md)
