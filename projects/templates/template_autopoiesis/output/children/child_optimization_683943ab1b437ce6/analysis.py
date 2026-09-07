"""Auto-generated analysis entry point for optimization."""
# spec_hash: 683943ab1b437ce6  grammar_hash: 484f85e003a8825a
# seed: 42  track: analytical  section_set: standard
from primitives import collect_primitives


def run() -> None:
    """Execute the optimization primitive suite."""
    prims = collect_primitives()
    domain_specs = prims.get("optimization", ())
    for ps in domain_specs:
        result = ps.fn(ps.example_input)
        print(f"{ps.name}: {result}")


if __name__ == "__main__":
    run()
