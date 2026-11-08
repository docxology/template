```{=html}
<!--template-web-source-0aff125c12264cc558cfdadd639bd747e270b25bbb3dc762acda5ae501276f7d-0-start-->
```

# Abstract

This living record tracks 3 experiments organized as a version-controlled tree with frozen nodes. Of these, 0 are answered (0 wins, 0 dead ends), 1 are frozen preregistrations, and 2 are provisional plans. The paper you are reading is generated from the tree state; answering or freezing a node regenerates it.

```{=html}
<!--template-web-source-0aff125c12264cc558cfdadd639bd747e270b25bbb3dc762acda5ae501276f7d-0-end-->
```



---



```{=html}
<!--template-web-source-0aff125c12264cc558cfdadd639bd747e270b25bbb3dc762acda5ae501276f7d-1-start-->
```

# Introduction

Research logs rot because outcomes live in notebooks while plans live in issue trackers. We propose the opposite coupling: a single experiment tree where nodes are preregistered (frozen) before being run, and the manuscript is a deterministic projection of that tree. The tree carries a run_command contract per node, so every recorded experiment names the canonical command that produced its evidence.

```{=html}
<!--template-web-source-0aff125c12264cc558cfdadd639bd747e270b25bbb3dc762acda5ae501276f7d-1-end-->
```



---



```{=html}
<!--template-web-source-0aff125c12264cc558cfdadd639bd747e270b25bbb3dc762acda5ae501276f7d-2-start-->
```

# Methodology

Each node carries a status from the ladder {provisional, frozen, answered}. A provisional node may be frozen (preregistered, immutable) or answered directly. Answering a frozen node is refused by construction: preregistered commitments may not be back-filled. Within one tree, each run_command may be declared by at most one node, so an experiment identity maps one-to-one onto the command that runs it.

```{=html}
<!--template-web-source-0aff125c12264cc558cfdadd639bd747e270b25bbb3dc762acda5ae501276f7d-2-end-->
```



---



```{=html}
<!--template-web-source-0aff125c12264cc558cfdadd639bd747e270b25bbb3dc762acda5ae501276f7d-3-start-->
```

# Results

## Answered nodes

No answered experiments yet.

## Winners per round

{}

```{=html}
<!--template-web-source-0aff125c12264cc558cfdadd639bd747e270b25bbb3dc762acda5ae501276f7d-3-end-->
```



---



```{=html}
<!--template-web-source-0aff125c12264cc558cfdadd639bd747e270b25bbb3dc762acda5ae501276f7d-4-start-->
```

# Dead ends and discussion

Negative results are first-class: every answered node with outcome `dead_end` is registered below, keeping future rounds away from retired directions.

No dead ends recorded.

## In progress (frozen preregistrations)

- E003: Frozen preregistration: momentum follow-up

```{=html}
<!--template-web-source-0aff125c12264cc558cfdadd639bd747e270b25bbb3dc762acda5ae501276f7d-4-end-->
```



---



```{=html}
<!--template-web-source-0aff125c12264cc558cfdadd639bd747e270b25bbb3dc762acda5ae501276f7d-5-start-->
```

# References

See `references.bib` for the bibliography (rendered by Pandoc).

```{=html}
<!--template-web-source-0aff125c12264cc558cfdadd639bd747e270b25bbb3dc762acda5ae501276f7d-5-end-->
```
