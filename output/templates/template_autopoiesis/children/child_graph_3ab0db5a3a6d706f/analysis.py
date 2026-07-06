"""Auto-generated analysis entry point for graph."""
from primitives import collect_primitives


def run():
    prims = collect_primitives()
    domain_specs = prims.get("graph", ())
    for ps in domain_specs:
        result = ps.fn(ps.example_input)
        print(f"{ps.name}: {result}")


if __name__ == "__main__":
    run()
