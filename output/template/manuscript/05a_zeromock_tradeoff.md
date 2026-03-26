# Discussion

## The Zero-Mock Tradeoff

The [Zero-Mock testing policy](03e_quality.md#zero-mock-testing-policy) is `template/`'s most distinctive design decision. By prohibiting all mock objects, we gain confidence that tests exercise real code paths---a pytest run against the template genuinely invokes `pandoc`, writes to disk, and parses real YAML. The cost is test duration: the full infrastructure test suite (~3,083 tests) takes 2--4 minutes, compared to sub-second execution typical of heavily-mocked suites.

We argue this tradeoff is strongly favorable for research software. Unlike web applications where millisecond latency and thousands of daily deploys demand fast feedback loops, research pipelines run infrequently (once per manuscript revision) and correctness vastly outweighs speed. A mocked test that passes while the real renderer fails is worse than a slow test that catches the failure. The analogy to statistical methodology is precise: just as Simmons et al.'s *researcher degrees of freedom* [@simmons2011falsepositive] inflate false-positive rates through undisclosed analytical flexibility, mock objects create *testing degrees of freedom* that make integration failures invisible. The Zero-Mock policy closes this loophole by the same mechanism that pre-registration [@nosek2018preregistration] closes the p-hacking loophole: removing flexibility before the fact. As Peng [@peng2011reproducible] argues, computational reproducibility requires independent verification---and mock-only tests verify assumptions rather than results. Garijo et al.'s FAIRsoft evaluator [@garijo2024fairsoft] identifies *executability* as a primary quality indicator; the Zero-Mock policy operationalizes executability at the unit level.

### When Mocks Are Not the Problem

It is important to distinguish the Zero-Mock policy from a naive rejection of all test isolation techniques. Fowler's classification [@martin2008clean] recognizes that stubs and fakes serve legitimate purposes—a test database populated with known data is not a mock, it is a fixture. The policy specifically prohibits *mock objects* as defined by Meszaros: assertions on indirect outputs (method calls, argument patterns) rather than direct outputs (return values, side effects). The distinction matters because mock-based assertions encode implementation assumptions ("method X must be called with argument Y") that become invisible coupling between tests and production code, creating the illusion of coverage without testing real behavior.

### Practical Implementation

The template enforces zero-mock compliance at three levels:

1. **Code review**: `AGENTS.md` at every directory level explicitly states the prohibition, ensuring both human and AI contributors are aware before writing tests.
2. **Static analysis**: `grep -rn "MagicMock\|unittest.mock\|@patch" tests/` can be run as a pre-commit hook to catch violations.
3. **Cultural norm**: The `code_project` exemplar demonstrates zero-mock techniques for every integration point (filesystem, YAML, PDF rendering, subprocess), providing a worked reference for contributors.

However, the policy requires careful management of external dependencies. Tests requiring Ollama (the local LLM backend) use `@pytest.mark.requires_ollama` and are skipped in environments where the service is unavailable. Tests requiring network access use `@pytest.mark.network`. This marker system preserves the Zero-Mock principle while acknowledging that not all environments provide all services, especially computationally intensive ones. The key distinction is between *replacing* an external dependency (which mock objects do, hiding failures) and *skipping* a test when a dependency is absent (which markers do, preserving transparency).
