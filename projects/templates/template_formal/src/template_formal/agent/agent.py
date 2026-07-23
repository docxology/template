"""``Agent[StateT]`` -- one storage session, one protocol endpoint, one decision loop.

Each :class:`Agent` owns *exactly* two resources, matching the ISA's
decentralization framing (per ``Out of Scope``: real local DB, real
in-process networking, no shared global state):

1. **One storage session** -- a real, on-disk :class:`~template_formal.storage.db.Database`
   opened by this agent alone at construction time (never ``:memory:``, per
   ISC-66), against which this agent begins its own single-use
   :class:`~template_formal.storage.transaction.TransactionHandle` instances
   each time it records an observation.
2. **One protocol endpoint** -- a :class:`~template_formal.protocol.session.SessionEndpoint`
   phase object, starting at :class:`~template_formal.protocol.session.IdleSession`,
   mutated only through this agent's own public methods.

Neither resource is ever exposed on the public API surface (see
``tests/agent/test_agent_isolation.py``, ISC-30): there is no public
attribute or method that returns a :class:`~pathlib.Path`,
:class:`sqlite3.Connection`, or ``Database``, and no public method accepts
one as a parameter either -- so one agent's storage file is structurally
unreachable through a second agent's API, not merely unreached-in-practice.

Free-energy-minimizing decision loop
-------------------------------------
:meth:`Agent.decide` scores a small set of candidate actions by a
*simplified, pedagogical* variational-free-energy-style quantity and picks
the action that minimizes it. The general framing -- that adaptive
behavior can be cast as approximate minimization of a variational free
energy over beliefs about hidden/observed states -- traces to Friston, K.
(2005), "A theory of cortical responses," *Phil. Trans. R. Soc. B*,
360(1456), 815-836. That paper establishes the free-energy principle for
perception and does not itself present the risk/ambiguity decomposition of
*expected* free energy used below; that decomposition was formalized in
later active-inference literature. This module borrows only the general
framing (behavior as free-energy minimization over a belief distribution)
and states the borrowed formula explicitly rather than presenting it as a
verbatim reproduction of Friston 2005's equations. See ``manuscript``
§"Active Inference framing" for the full scoping of this claim, including
what is genuinely computed here versus what a research-grade active
inference implementation would additionally require (hierarchical
generative models, policy-conditioned rollouts, precision-weighting, and
message-passing inference -- all out of scope for this template).

For a single scalar Gaussian belief ``Q(o) = N(mean, variance)`` about a
candidate action's predicted outcome, and a fixed Gaussian preference
(prior) ``P(o) = N(pref_mean, pref_variance)`` over preferred outcomes,
this module computes:

    G(action) = KL[Q(o) || P(o)] + H[Q(o)]

where ``KL`` is the closed-form Gaussian Kullback-Leibler divergence
(the "risk" term -- how far the predicted outcome distribution is from
the preferred one) and ``H`` is the closed-form Gaussian differential
entropy (the "ambiguity" term -- how uncertain the predicted outcome
itself is). :meth:`Agent.decide` returns the candidate minimizing
``G``. Both closed-form terms are ordinary, exactly-checkable arithmetic
-- see ``tests/agent/test_agent_free_energy.py`` for a hand-derived
numeric expectation this implementation is required to match (ISC-29),
not merely a "runs without error" smoke test.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Protocol, Sequence, TypeAlias, TypeVar
from uuid import UUID

from template_formal.protocol.session import (
    ClosedSession,
    EstablishedSession,
    HandshakingSession,
    IdleSession,
    WireMessage,
)
from template_formal.storage.db import (
    Database,
    IsolationLevel,
    QueryBuilder,
    StorageError,
    create_schema,
    open_database,
)
from template_formal.storage.schema import OBSERVATIONS_TABLE
from template_formal.storage.transaction import begin_transaction
from template_formal.types.ids import AgentId
from template_formal.types.result import Err, Ok, Result


class GaussianBelief(Protocol):
    """Structural interface any belief-state type ``StateT`` must satisfy.

    ``mean``/``variance`` are declared as read-only ``@property`` members
    (not plain mutable attributes) deliberately: mypy --strict treats a
    plain ``attr: float`` Protocol member as read-write, which a
    ``frozen=True`` dataclass field can never satisfy (a frozen field has
    no setter). Declaring these read-only is what actually lets any
    frozen dataclass (or other read-only object) exposing these two
    ``float`` values satisfy this ``Protocol`` structurally -- verified by
    ``tests/mypy_fixtures/good_agent_belief_instantiation.py``, which
    type-checks ``Agent[BeliefState]`` itself as a mypy-oracle positive
    control (a prior revision of this Protocol used plain attributes and
    silently failed this exact instantiation; see ISA.md Changelog).
    """

    @property
    def mean(self) -> float:
        """The mean (expected value) of this Gaussian belief."""
        ...

    @property
    def variance(self) -> float:
        """The variance of this Gaussian belief (must be finite and > 0)."""
        ...


StateT = TypeVar("StateT", bound=GaussianBelief)

AnyProtocolPhase: TypeAlias = ClosedSession | EstablishedSession | HandshakingSession | IdleSession
"""The union of every concrete phase class an ``Agent``'s protocol endpoint may hold.

``SessionEndpoint`` is generic over a *constrained* ``PhaseT`` (one of the
four phase markers), which mypy --strict does not allow parameterizing with
a catch-all like ``object`` or ``Any`` (see ``types/phase.py``). This union
of the four concrete session classes is the honest, fully-typed
description of "any one of the four phases this endpoint could currently
be in" -- it is what :attr:`Agent._session` is actually typed as below.
"""


@dataclass(frozen=True, slots=True)
class BeliefState:
    """The reference :class:`GaussianBelief` implementation: ``N(mean, variance)``.

    ``variance`` is validated at construction (finite, ``> 0.0``) rather
    than left as a bare ``float`` -- ``gaussian_kl_divergence`` divides by
    it and ``gaussian_differential_entropy`` takes ``math.log`` of it, so a
    zero, negative, or non-finite value would otherwise construct silently
    and only fail three calls later, deep inside :func:`expected_free_energy`,
    with an undocumented ``ZeroDivisionError``/``ValueError: math domain
    error`` far from the real defect. This mirrors the same
    construction-time-guard pattern this template already uses for
    ``storage/schema.py``'s ``Column``/``TableSchema`` SQL identifiers and
    ``colony/experiment.py``'s ``ColonyTrialConfig`` -- a third-adversarial-
    pass finding (independently surfaced by both a FirstPrinciples pass and
    a security review) that this was the one remaining unvalidated numeric
    boundary feeding the manuscript's headline Active-Inference claim.
    """

    mean: float
    variance: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.variance) or self.variance <= 0.0:
            raise ValueError(f"BeliefState.variance must be finite and > 0.0, got {self.variance!r}")


@dataclass(frozen=True, slots=True)
class CandidateAction(Generic[StateT]):
    """One candidate action, paired with the belief about its predicted outcome.

    Attributes:
        name: A human-readable label for the action (e.g. a pheromone-field
            location name in the colony integration test).
        predicted_state: This agent's belief ``Q(o | action)`` about the
            outcome this action would produce.
    """

    name: str
    predicted_state: StateT


@dataclass(frozen=True, slots=True)
class DecisionError:
    """An expected decision-loop failure -- never raised, always ``Err``.

    Currently the only member: the candidate list handed to
    :meth:`Agent.decide` was empty, so there is nothing to minimize over.
    """

    reason: str


def gaussian_kl_divergence(predicted: GaussianBelief, preference: GaussianBelief) -> float:
    """Closed-form ``KL[N(predicted) || N(preference)]`` -- the "risk" term.

    Uses the standard univariate-Gaussian KL-divergence formula::

        KL(N(mu_q, s_q) || N(mu_p, s_p))
            = 0.5 * ( s_q/s_p + (mu_p - mu_q)**2 / s_p - 1 + ln(s_p / s_q) )

    where ``s_q``/``s_p`` are variances (not standard deviations).
    """
    q_mean, q_var = predicted.mean, predicted.variance
    p_mean, p_var = preference.mean, preference.variance
    return 0.5 * ((q_var / p_var) + ((p_mean - q_mean) ** 2) / p_var - 1.0 + math.log(p_var / q_var))


def gaussian_differential_entropy(belief: GaussianBelief) -> float:
    """Closed-form differential entropy of ``N(belief.mean, belief.variance)`` -- the "ambiguity" term.

    ``H[N(mu, s)] = 0.5 * ln(2 * pi * e * s)`` (independent of ``mu``).
    """
    return 0.5 * math.log(2.0 * math.pi * math.e * belief.variance)


def expected_free_energy(predicted: GaussianBelief, preference: GaussianBelief) -> float:
    """``G = KL[Q(o) || P(o)] + H[Q(o)]`` -- see module docstring for scoping."""
    return gaussian_kl_divergence(predicted, preference) + gaussian_differential_entropy(predicted)


class Agent(Generic[StateT]):
    """One colony member: one storage session, one protocol endpoint, one decision loop.

    Construction requires a :data:`~template_formal.types.ids.AgentId` --
    a ``NewType``-wrapped ``UUID`` -- not a bare ``str``/``UUID``. mypy
    --strict rejects a bare ``UUID``/``str`` argument at the call site (see
    ``tests/mypy_fixtures/bad_agent_id_construction.py``, ISC-31); the
    ``isinstance`` check below is the runtime half of that proof, reachable
    only if a caller bypasses mypy (e.g. via ``# type: ignore`` or an
    untyped boundary) -- the same pattern ``storage/db.py`` uses for its
    ``IsolationLevel`` literal.
    """

    __slots__ = ("_agent_id", "_database", "_preference", "_session")

    def __init__(
        self,
        agent_id: AgentId,
        db_path: Path,
        preference: StateT,
        *,
        isolation_level: IsolationLevel = "deferred",
    ) -> None:
        if not isinstance(agent_id, UUID):
            raise TypeError(f"Agent requires an AgentId (a NewType-wrapped UUID), got {type(agent_id).__name__}")
        self._agent_id: AgentId = agent_id
        database = open_database(db_path, isolation_level=isolation_level)
        create_schema(database, OBSERVATIONS_TABLE)
        self._database: Database = database
        self._preference: StateT = preference
        self._session: AnyProtocolPhase = IdleSession(local_id=agent_id)

    @property
    def agent_id(self) -> AgentId:
        """This agent's nominal identity."""
        return self._agent_id

    @property
    def protocol_phase(self) -> str:
        """The class name of this agent's current protocol phase (``"IdleSession"``, ...).

        Exposes *observability only* -- the underlying
        :class:`~template_formal.protocol.session.SessionEndpoint` object
        itself is never returned, only its phase name as a plain ``str``.
        """
        return type(self._session).__name__

    def initiate_handshake(self, peer_id: AgentId) -> WireMessage:
        """Move this agent's protocol endpoint from Idle to Handshaking.

        Returns the ``hello`` :class:`~template_formal.protocol.session.WireMessage`
        the caller must deliver to ``peer_id`` (e.g. via a
        :class:`~template_formal.network.bus.InProcessBus`).

        Raises:
            RuntimeError: If this agent's protocol endpoint is not
                currently :class:`~template_formal.protocol.session.IdleSession`
                (i.e. a handshake was already initiated). This mirrors the
                affine-discipline runtime guards on
                :class:`~template_formal.protocol.session.IdleSession` itself
                -- calling ``open`` twice on the same instance is a
                programmer-error condition, not an expected outcome.
        """
        session = self._session
        if not isinstance(session, IdleSession):
            raise RuntimeError(
                f"cannot initiate a handshake from phase {type(session).__name__!r}; "
                "a handshake was already initiated on this agent"
            )
        next_session, hello = session.open(peer_id)
        self._session = next_session
        return hello

    def decide(self, candidates: Sequence[CandidateAction[StateT]]) -> Result[CandidateAction[StateT], DecisionError]:
        """Return the candidate minimizing :func:`expected_free_energy`, or ``Err`` if empty.

        Ties are broken by :func:`min`'s documented behavior: the first
        candidate (in ``candidates`` order) achieving the minimum score
        wins. This is exploited deliberately, not incidentally, by the
        colony integration test's symmetry-breaking (see
        ``tests/colony/test_colony_integration.py``).
        """
        if not candidates:
            return Err(DecisionError("cannot decide over an empty candidate list"))
        chosen = min(
            candidates, key=lambda candidate: expected_free_energy(candidate.predicted_state, self._preference)
        )
        return Ok(chosen)

    def record_observation(self, chosen: CandidateAction[StateT]) -> Result[int, StorageError]:
        """Persist ``chosen``'s name and its expected free energy to this agent's own DB.

        Opens a fresh :class:`~template_formal.storage.transaction.TransactionHandle`
        on *this agent's own* :class:`~template_formal.storage.db.Database`
        (never another agent's), inserts one row, and commits it -- never
        raising for an ordinary insert failure (a constraint violation
        comes back as ``Err(StorageError(...))``, per
        ``storage/db.py``'s documented convention).
        """
        txn = begin_transaction(self._database)
        builder: QueryBuilder[int] = QueryBuilder(
            database=self._database,
            table=OBSERVATIONS_TABLE,
            row_factory=lambda row: int(row["id"]),
        )
        score = expected_free_energy(chosen.predicted_state, self._preference)
        inserted = builder.insert({"key": chosen.name, "value": score})
        if isinstance(inserted, Err):
            txn.rollback()
            return inserted
        txn.commit()
        return inserted

    def tick(self, candidates: Sequence[CandidateAction[StateT]]) -> Result[CandidateAction[StateT], DecisionError]:
        """One decision-loop tick: :meth:`decide`, then :meth:`record_observation`.

        Returns the chosen candidate on success. A storage failure while
        recording the observation is folded into a :class:`DecisionError`
        rather than silently discarded -- the caller still learns
        something went wrong, even though the underlying failure was a
        ``StorageError`` rather than a ``DecisionError`` in origin.
        """
        decided = self.decide(candidates)
        if isinstance(decided, Err):
            return decided
        chosen = decided.value
        recorded = self.record_observation(chosen)
        if isinstance(recorded, Err):
            return Err(DecisionError(f"chose {chosen.name!r} but failed to record it: {recorded.error.message}"))
        return Ok(chosen)

    def observation_count(self) -> int:
        """Return how many observations this agent has recorded, via a real ``SELECT``."""
        builder: QueryBuilder[int] = QueryBuilder(
            database=self._database,
            table=OBSERVATIONS_TABLE,
            row_factory=lambda row: int(row["id"]),
        )
        selected = builder.select_all()
        if isinstance(selected, Err):
            return 0
        return len(selected.value)

    def close(self) -> None:
        """Close this agent's own SQLite connection. Idempotent-unsafe: call once."""
        self._database.connection.close()
