---
name: worker-selection
description: Select worker or smart-worker by reasoning difficulty. Use when rating fix complexity, delegating coding tasks, or starting an OpenSpec implementation workstream.
---

# Worker selection

Both workers share one execution contract. The parent selects the model and supplies the task scope. The table recommends a profile, not a different set of worker rules.

| Score | Complexity reference | Recommended profile |
| --- | --- | --- |
| 1 | Small local correction with clear behavior and direct verification | `worker` |
| 2 | Bounded function-level change with clear caller behavior | `worker` |
| 3 | Multi-file or state changes with known constraints and a clear test approach | `worker` |
| 4 | Algorithms, concurrency, or security that need difficult reasoning about interacting behavior | `smart-worker` |
| 5 | Architecture or state-machine changes with interacting constraints and substantial technical uncertainty | `smart-worker` |

- Base selection on reasoning difficulty, not patch size, file count, test count, or finding severity.
- A small concurrency fix can need `smart-worker`. A large mechanical change can fit `worker`.
- Ordinary parent sessions do not need a formal score report. Reviewers report the score and a short reason when their caller needs a recommendation.
- Missing requirements need clarification, not another model.
- Workers do not stop or change models solely because task complexity increases. Investigation delegation remains optional.

For a parent-owned OpenSpec implementation workstream, read `references/openspec-workflow.md` relative to this skill directory. Delegated workers follow their assigned tasks rather than the parent branch and review procedure.
