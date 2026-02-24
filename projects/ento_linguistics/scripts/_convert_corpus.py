import json
from pathlib import Path

def convert_corpus():
    input_path = Path("projects/ento_linguistics/output/data/literature_corpus.json")
    output_path = Path("projects/ento_linguistics/data/corpus/abstracts.json")

    if not input_path.exists():
        print(f"Error: {input_path} does not exist.")
        return

    with open(input_path, "r") as f:
        data = json.load(f)

    abstracts = []
    for pub in data.get("publications", []):
        # Format similar to the manual one: "Title. Author (Year). Abstract"
        title = pub.get("title", "").strip()
        authors = ", ".join(pub.get("authors", []))
        year = pub.get("year", "")
        abstract = (pub.get("abstract") or "").strip()
        
        if abstract:
            entry = f"{title}. {authors} ({year}). {abstract}"
            abstracts.append(entry)

    with open(output_path, "w") as f:
        json.dump(abstracts, f, indent=4, ensure_ascii=False)

    print(f"Converted {len(abstracts)} abstracts to {output_path}")

if __name__ == "__main__":
    convert_corpus()
