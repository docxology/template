"""Auto-generated analysis entry point for optimization."""
from primitives import collect_primitives


def run():
    prims = collect_primitives()
    domain_specs = prims.get("optimization", ())
    for ps in domain_specs:
        result = ps.fn(ps.example_input)
        print(f"{ps.name}: {result}")


if __name__ == "__main__":
    run()
