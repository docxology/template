# tests/ — template_sia

- Real filesystem fixtures under `../src/fixtures/recorded_generations/`
- No mocks — subprocess and temp dirs only
- Opt-in Ollama tests: `@pytest.mark.requires_ollama`

Run one pytest process per project directory (repo-wide convention).
