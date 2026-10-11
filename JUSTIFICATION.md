# CLAUDE.md Justification

## Commands
I included exact commands for installing dependencies, running tests, and checking lint so Claude can verify its work using the same commands I use in the project. The command rules were especially useful across all three sessions because every implementation was checked with `python -m pytest -v`, ending with 6 passing tests. I also documented the existing Ruff findings so Claude would not treat unrelated lint problems as part of a scoped task. If I had to cut this section in half, I would remove the baseline test count but keep the exact test and lint commands.

## Architecture
I described the project as a layered flow from `routes/api.py` to `services/*.py`, with the module-level dictionaries acting as the current data store. I named `services/users.py` as the canonical service example because it already demonstrates the structure, validation, errors, type hints, and documentation style I want Claude to follow. Session 3 reinforced this section because Claude kept the new task lookup logic in the service layer and did not create an unnecessary route. If I had to shorten this section, I would keep the layer boundaries and canonical file reference and remove some explanation about the data stores.

## Conventions
The conventions require type hints, Google-style docstrings, application-specific errors, stable public signatures, and careful handling of tests. Session 1 shaped this section the most because Claude changed an existing test even though the original rule did not clearly distinguish between existing coverage and a genuinely necessary test change. I therefore made the test rule more specific, and Session 2 showed improvement when Claude added only the missing docstring and left the tests unchanged. If this section had to be reduced, I would keep the type hints, docstring pattern, error handling, and test-preservation rule.

## Do not touch
The do-not-touch section protects parts of this small project that should not change during unrelated service work, including error-to-HTTP mapping, module-level data stores, dependencies, and existing unrelated Ruff findings. These rules helped keep the sessions focused instead of turning small tasks into broad cleanup work. Session 3 also exposed an additional problem with unspecified behavior, so I added a convention requiring Claude not to invent behavior when the code and tests do not establish it. If I had to shorten the restrictions, I would keep the error infrastructure and dependency rules because those changes could affect the project more broadly.

## Solo vs. Team
For a three-developer team, the two most important changes would be stronger verification requirements and clearer rules for ambiguous behavior. I would require contributors to run the same test and lint commands before handing off changes so everyone works against a consistent baseline. I would also require unclear behavioral decisions to be confirmed instead of assumed, because different developers may interpret the same requirement differently. These changes would make CLAUDE.md useful not only as AI guidance but also as a shared project contract for the team.
