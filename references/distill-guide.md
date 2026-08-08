# Distillation Guide — turning book text into a Skill

The extractor gives you raw text. RAG would stop there. A Skill goes further: it rewrites the book's knowledge into **procedural, agent-ready form**. Follow these rules per section.

## 1. Convert description → procedure
- Bad: "The book explains that dependency injection improves testability."
- Good: "When a class has >2 collaborators, inject them via constructor. Test the class by passing mocks. See template in §4."

Use imperative/infinitive voice. Lead with the action, not the theory.

## 2. Extract decision rules
Turn the book's "when to use X vs Y" into explicit rules:
- IF <observable condition> → USE <approach A>
- ELSE IF <condition> → USE <approach B>
- ELSE → <default>

## 3. Capture anti-patterns
Every methodology has "don't do this." Pull the book's warnings into a bullet list of **forbidden/discouraged** actions with the failure mode.

## 4. Extract reusable artifacts
- Code templates / skeletons
- Naming conventions, schema rules, config keys
- Checklists an agent can tick off
Keep these verbatim where they must be exact.

## 5. Preserve the mental model
One short paragraph per major section: *how the author wants you to think about the problem.* This is what makes the agent "write with depth" rather than "write code that compiles."

## 6. Structure the output
In `references/<book>.md`:
```
# <Book Title> — distilled
## Methodology (the mental model)
## Core procedures
### <Section from TOC>
- Procedure / rules / anti-patterns / template
## Quick reference (decision table, naming, config)
## Source mapping (TOC # → this section)
```
Keep only what an agent needs. Cut narrative, examples-for-humans, and filler.

## Quality bar
A section is "distilled" when another agent could follow it to produce work matching the book's intent **without re-reading the source**. If it still reads like a summary, it isn't done.
