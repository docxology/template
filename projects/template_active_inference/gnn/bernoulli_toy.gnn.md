# GNN Example: K=2 Bernoulli / Ising Policy-Entanglement Toy

## GNNSection

TemplateActiveInference_K2_Ising

## GNNVersionAndFlags

GNN v1.1

## ModelName

K=2 Bernoulli/Ising Policy-Entanglement Toy

## StateSpaceBlock

pi1[2,1,type=float]
pi2[2,1,type=float]
E1[2,1,type=float]
E2[2,1,type=float]
J[2,2,type=float]
lam[1,type=float]
gamma[1,type=float]
q_joint[2,2,type=float]

## Connections

E1>pi1
E2>pi2
pi1-J:cross_stream_coupling
pi2-J:cross_stream_coupling
pi1>q_joint
pi2>q_joint
J>q_joint:coupling
lam>q_joint:deformation

## InitialParameterization

E1={(0.5, 0.5)}
E2={(0.5, 0.5)}
J={
  (0.5, -0.5),
  (-0.5, 0.5)
}
lam={(0.0)}
gamma={(0.0)}

## ActInf Ontology Annotation

pi1=Stream1PolicyVector
pi2=Stream2PolicyVector
E1=Stream1HabitPrior
E2=Stream2HabitPrior
J=CrossStreamCouplingPotential
lam=EntanglementDeformationParameter
gamma=SophisticationWeight
q_joint=EntangledJointPosterior
