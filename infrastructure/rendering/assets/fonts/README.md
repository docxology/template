# Bundled rendering fonts

[Liberation](liberation/README.md) contains the explicitly selected font bodies,
license text and provenance used by rendering and native observations.

Runtime font discovery and rendering observations must identify the actual
selected files. A family name or this directory's presence does not prove which
font a native tool consumed.

The shared web transport includes the unmodified [LZMA-JS decoder](lzma-d-min.js)
from [LZMA-JS/LZMA-JS](https://github.com/LZMA-JS/LZMA-JS), commit
`8f98fe85a1ef78ab6e9d26ab85ce338f50095a23`, and its complete
[MIT notice](LZMA-JS-LICENSE.txt). The renderer pins both physical files by
SHA-256 and embeds that notice in each published font script. The decoder is a
local lossless transport component; all twelve Liberation font bodies, their
OFL notice and per-face hashes remain unchanged.
