# GNN Example: T-maze Sophisticated Inference

## GNNSection

TemplateActiveInference_SI_TMaze

## GNNVersionAndFlags

GNN v1.1

## ModelName

T-maze Sophisticated Inference Toy

## StateSpaceBlock

loc[2,1,type=float]
obs[2,1,type=float]
pi[2,1,type=float]
belief_entropy[1,type=float]

## Connections

loc>obs
pi>loc:transition
pi>belief_entropy:planning

## ActInf Ontology Annotation

loc=HiddenState
obs=ObservationLikelihood
pi=PolicyPosterior
belief_entropy=BeliefEntropy
