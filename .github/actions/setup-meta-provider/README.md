# Declared Meta provider

Builds the current public Meta exemplar as a noneditable wheel and installs it
into the root interpreter. Advanced Literature Review uses this declared
namespaced engine; neither source-path injection nor a replacement module
supplies it.

The caller checks out the repository, provisions Python and uv, then runs
uv sync --locked --group installed-build before using this action:

~~~yaml
- uses: ./.github/actions/setup-meta-provider
~~~

The action builds with the prepared interpreter and locked backend, writes its
wheel to a fresh runner-temporary directory, and installs without resolving
additional dependencies. It does not install native tools or run project tests.
