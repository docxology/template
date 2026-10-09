# Installed native readiness action contract

[README.md](README.md) describes prerequisite ordering. This action is a hosted
Ubuntu preparation step, called after checkout, pinned source fixtures and
Python/uv setup. It has no inputs or acceptance outputs. Java and EPUBCheck
nominations are exported as `TEMPLATE_NATIVE_JAVA` and
`TEMPLATE_NATIVE_EPUBCHECK` for the caller's explicit tool arguments.

Preserve Root `uv.lock`, Source package/tool pins, upstream licenses and existing
local setup actions. Do not combine independent project locks or use a cache,
path or tool label as provider authority. Cache warming precedes the cold
operation; the original 14400-second deadline and all later provider/Code/native
predicates belong to the genuine installed launcher and reader.

Retain genuine preparation failures. Keep temporary cache-warming cleanup
restricted to the action's own `mktemp` destinations. This action does not clean
shared source, runtime aliases or acceptance evidence. The same preparation must
serve originals, readers and handoff under the
[required workflow](../../workflows/platform-required-acceptance.yml) and
[release workflow](../../workflows/release.yml).

Maintain the [parent action contract](../AGENTS.md), the local doc pair and
resolving links. Run actionlint after action edits; complete docs and release
acceptance remain caller-owned gates.
