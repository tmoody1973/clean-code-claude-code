# Start Here If You Vibe Code

You can build a real product by describing what you want and letting AI help write the code. The danger arrives when the product grows faster than your understanding of it.

This toolkit gives you a safer loop:

1. Understand what the product should do.
2. Review before changing things.
3. Fix the highest-risk issue first.
4. Verify the behavior, not just the appearance of the code.
5. Keep enough documentation that another person can take over.

## Which tool should I use?

| You want to… | Use | What happens |
|---|---|---|
| Understand code quality | “Review my code in plain English” | Reports important findings; changes nothing |
| Know whether the product is launch-ready | “Run a product-readiness review” | Checks product and operational risks; changes nothing |
| See a quick cleanup list | `/code-smells` | Runs available tools and reports contextual smells |
| Tidy one file | “Use boy-scout-cleanup on this file” | Makes 3–5 small verified changes |
| Restructure code | `/refactor` | Changes structure while preserving behavior |
| Start with the right folders | “Scaffold this project” | Follows the detected framework |
| Give the project to an engineer | “Prepare a developer handoff” | Creates a verified map of the product and repository |

Start with the tools that change nothing. Read the findings and decide what matters for your users before asking AI to rewrite code.

## Four rules that prevent expensive mistakes

1. **Never commit secrets.** API keys, tokens, passwords, and private credentials do not belong in code, screenshots, examples, logs, or chat prompts.
2. **A passing build is not proof the product works.** Test the important user journeys and business rules.
3. **Do not clean up code blindly.** A rename, removed import, or “simpler” condition can change behavior.
4. **Unknown is an acceptable answer.** A handoff that clearly lists unknowns is safer than confident documentation the AI invented.

## What a developer needs from you

A developer does not need every line explained. They need to know what the product does, how to run it, where important behavior lives, what external systems it touches, what is fragile, and what outcome matters next.

Use the `developer-handoff` skill before transferring the project. Then walk through its “Unknowns for the owner” section yourself—those answers contain product context that the repository may never reveal.
