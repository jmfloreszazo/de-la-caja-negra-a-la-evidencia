**English** · [Español](../../es/parte-1-antes-de-traducir/05-modernizar-exige-elegir-que-problema-resolvemos.md)

[← Chapter 4 · What I share with other authors and where I disagree](04-what-i-share-with-other-authors-and-where-i-disagree.md) · [Contents](../README.md) · [Part II · Archaeology, knowledge and authority →](../part-2-archaeology-and-authority/README.md)

# Chapter 5 · Modernizing means choosing which problem we solve

> [!IMPORTANT]
> **Chapter thesis.** "Move it to .NET" describes a technology destination, not an outcome. Each goal requires different evidence, and each alternative must explain its verification cost and its way back.

## The destination does not replace the diagnosis

"Move it to .NET" describes a target technology. It does not yet describe the outcome the organization needs. We can end up with the same hard-to-change process, now written in C#. We can also keep COBOL and significantly improve operations, testing or how capabilities are exposed.

Before choosing a route, I would fix the outcome sought. It may be retiring a dependency, regaining maintainability, shortening a batch window or enabling a new integration. Each goal requires different evidence. A shorter compile time does not prove better service continuity; a new API does not prove the internal process is easier to evolve.

Some decisions can be combined. Preserving and documenting may be the right action for a stable component. Encapsulating offers a controlled interface. Refactoring improves structure while keeping behaviour. Replacing a capability may make sense when the benefit outweighs the cost and we can verify the transition. A standard product may solve another part, provided we accept and evaluate its differences.

I would not set a universal preference before studying the system. I would, however, require each alternative to explain its verification cost, its dependencies and its way back. An apparently cheap option can shift the cost to data reconciliation or to years of coexistence.

## The unit of change must stand on its own

In the lab we will choose a calculation and a decision without persistence. It is a deliberately small unit. It lets us observe inputs and outputs without introducing database locks, pending messages or recoveries in the middle of a process.

In a real system, that convenience is not a given. A function that looks autonomous may read a file prepared by a previous job or depend on a shared variable. A program called from several transactions may interpret the same record differently. The first task is to discover those dependencies, not to ignore them so they fit the diagram.

A useful boundary describes inputs, outputs, prior state, side effects and failure conditions. It also identifies who can write and when. If during coexistence two systems modify the same data without a consistency strategy, the difficulty can outweigh the benefit of having split the code.

My criterion would be to start where evidence is recoverable and impact is contained. That does not mean choosing only trivial cases. It means choosing a case that lets us learn about the system and that can be stopped without turning every uncertainty into a production emergency.

## Success needs a business measure

The project must measure more than code produced. What matters is escaped defects, review time, the effort of clarifying rules, operating cost and the ability to restore service. AI can reduce one part and increase another.

A fair comparison includes the cost of building and maintaining the oracles. It is real work. If we hide it, we turn TODM into a commercial promise that is hard to sustain. My interest lies in finding out when that cost is offset by a reduction in uncertainty and in accepted errors.

> **An apparently cheap option can shift the cost to years of reconciliation.**

---

[← Chapter 4 · What I share with other authors and where I disagree](04-what-i-share-with-other-authors-and-where-i-disagree.md) · [Contents](../README.md) · [Part II · Archaeology, knowledge and authority →](../part-2-archaeology-and-authority/README.md)
