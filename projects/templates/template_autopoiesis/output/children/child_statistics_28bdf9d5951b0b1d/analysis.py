"""Auto-generated analysis entry point for statistics."""
# spec_hash: 28bdf9d5951b0b1d  grammar_hash: 1142e011a7d4b835
# seed: 42  track: analytical  section_set: standard
from primitives import collect_primitives


def run() -> None:
    """Execute the statistics primitive suite."""
    prims = collect_primitives()
    domain_specs = prims.get("statistics", ())
    for ps in domain_specs:
        result = ps.fn(ps.example_input)
        print(f"{ps.name}: {result}")


if __name__ == "__main__":
    run()
