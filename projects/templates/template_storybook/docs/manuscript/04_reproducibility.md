# Reproducibility

The project avoids external image services and live APIs. Page images are
procedurally generated from checked-in content, and the final PDF is assembled
from those generated images. Tests check that the story loads, the two central
characters have opposite family shapes, a page renders at the configured
dimensions, the PDF page count matches the content file, and at least one page
script can run against a temporary project root.

The generated manifest records the cast, page list, and render paths. That
manifest is the compact evidence surface for the primary artifact.
