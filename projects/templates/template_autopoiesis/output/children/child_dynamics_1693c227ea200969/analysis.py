"""Auto-generated analysis entry point for dynamics."""
# spec_hash: 1693c227ea200969  grammar_hash: 16b9eb43de4d5e77
# seed: 42  track: analytical  section_set: standard
from primitives import collect_primitives


def run() -> None:
    """Execute the dynamics primitive suite."""
    prims = collect_primitives()
    domain_specs = prims.get("dynamics", ())
    for ps in domain_specs:
        result = ps.fn(ps.example_input)
        print(f"{ps.name}: {result}")


if __name__ == "__main__":
    run()
