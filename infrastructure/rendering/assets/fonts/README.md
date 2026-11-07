# Bundled rendering fonts

[Liberation](liberation/README.md) contains the explicitly selected font bodies,
license text and provenance used by rendering and native observations.

Runtime font discovery and rendering observations must identify the actual
selected files. A family name or this directory's presence does not prove which
font a native tool consumed.

The shared web transport includes a local adaptation of the
[LZMA-JS decoder](lzma-d-min.js) from
[LZMA-JS/LZMA-JS](https://github.com/LZMA-JS/LZMA-JS), commit
`8f98fe85a1ef78ab6e9d26ab85ce338f50095a23`, and its complete
[MIT notice](LZMA-JS-LICENSE.txt). The asset identifies its upstream origin and
local changes. The renderer pins both physical files by SHA-256 and embeds the
notice in each published font script.

The local synchronous binary API requires an exact finite output budget. It
bounds compressed input to 4 MiB, decoded output to 6 MiB and dictionary to 8 MiB,
checks complete input and the unsigned final range state, and rejects missing or
incorrect budgets, truncation and trailing data. Unused text, callback and worker
APIs are removed. Native LZMA-Alone unknown-size/end-marker streams remain intact
for portability across liblzma versions.

This is lossless transport: all twelve Liberation font bodies, their full OFL
notice and per-face hashes remain unchanged.
