# Research Log

Append-only. Newest entries first.
Tags: [OBS] [Q] [H] [RISK] [FINDING]
Resolved entries marked ✓ with pointer to outcome.

---

## 2026-03-17

**[RISK] Risk score formula has a structural ceiling**
`risk = 100 - (abs(50 - chain_a_supply_pct) × 2)` can never reach EXTREME
unless economic nodes cover ~95%+ of supply. Current 30-node network covers
~30% of supply → max achievable score ~40/100. May be systematically masking
genuine risk in realistic configurations. Consider whether total supply
*covered by economic nodes* should be a denominator rather than hardcoded
to full circulating supply (19.5M BTC). A 49/51 split where the minority
controls payment rails may score LOW while being operationally dangerous.

**[RISK] Dynamic ideology feedback loop untested for oscillation**
The anti-oscillation mechanisms in DYNAMIC_IDEOLOGY_PLAN.md (inertia, dead
zones, cooldowns) were chosen heuristically. Whether they are sufficient to
prevent limit cycles under adversarial initial conditions has not been shown.
If the feedback loop (price → ideology → economic_pct → price) has no stable
fixed point in some regions of parameter space, sustained oscillation could
produce spurious fork signals during simulation runs.

**[RISK] Mempool policy divergence is the unmodeled dangerous scenario**
Current test suite covers version forks and custody/volume splits — both
visible, discrete events that trigger fork detection. Mempool policy divergence
(different `maxmempool`, `minrelaytxfee`) is gradual and produces no fork
signal until depth threshold is crossed. By then divergence may already be
deep and the economic analysis triggers late. This scenario is noted as
"future" in CRITICAL_SCENARIOS_SUMMARY.md but may be the highest-priority
gap given its stealthy nature.

**[Q] Is the 70/30 custody:volume ratio empirically defensible?**
The weighting is BCAP-inspired but not derived from historical fork outcomes.
Would it have correctly predicted the 2017 SegWit/UASF/BCH result?
The custody-volume conflict scenario already showed 60% daily volume beats
10% custody — raising the question of whether the formula correctly weights
operational chokepoint power vs store-of-value power. Needs a calibration
test against at least one known historical fork before the ratio is cited
as validated in the paper.

**[Q] Is the fork depth threshold of 3 calibrated or arbitrary?**
Designed around 10-minute real-world blocks. In simulation with accelerated
block times, 3 blocks may be milliseconds of divergence. Is the threshold
actually filtering what it claims to filter in the test environment?
The natural split vs sustained fork boundary likely needs to be expressed
as time-since-divergence or block-rate-normalized depth, not raw block count.

**[Q] Does the price feedback loop have stable fixed points, or does it cycle?**
The price oracle uses `chain × 0.3 + economic × 0.5 + hashrate × 0.2`.
Economic weight is the dominant factor. Once dynamic ideology is implemented,
does the loop converge, oscillate, or diverge depending on initial conditions?
This is the most important unanswered structural question in the simulation.
Directly testable with a minimal 5-node network once DYNAMIC_IDEOLOGY_PLAN.md
is implemented.

**[Q] What is the empirically correct custody:volume ratio for fork prediction?**
Separate from the 70/30 BCAP question — what ratio would a Bayesian update
produce if trained on historical Bitcoin fork outcomes? The model currently
has no mechanism to learn or update the weighting from observed data.

**[H] Defense premium fails for emergent structural vulnerabilities**
The incentive hypothesis (rational actors prefer defense in a perfect money
system because attack is self-defeating for holders) holds for discrete
attacks: find vulnerability → disclose → bounty. It likely does not hold
for configuration drift — mempool policy divergence, peer selection topology
— where no individual actor makes a bad choice but the aggregate configuration
converges on a vulnerable attractor. This is tragedy-of-the-commons geometry,
not attacker/defender geometry. The price signal is too diffuse and delayed
to govern individual node configuration choices.
→ Testable once dynamic ideology and configuration evolution rules are implemented.

**[H] Custody weight is structurally dampened in dynamic scenarios**
Custody providers in the model have `discover=0`, 300 connections, high
inertia, and slow adoption speed. These config constraints reduce their
effective dynamic influence even when their static weight is high (70%
in the formula). Under the dynamic ideology feedback loop, the realized
custody:volume influence ratio may be much closer to 50/50 than the
formula implies — meaning the 70% custody dominance is a static-snapshot
artifact that disappears under realistic temporal dynamics.

**[H] Correlated ideology breaks the node independence assumption**
DYNAMIC_IDEOLOGY_PLAN.md assigns ideology parameters independently per node.
But major exchanges face the same regulatory environment, communicate via
industry groups, and historically move together during contentious forks.
Correlated node behavior would produce sudden large shifts in `v27_economic_pct`
that the per-node inertia/cooldown mechanisms cannot dampen — potentially
creating the rapid 100%/0% equilibrium the plan was specifically designed
to prevent. The independence assumption may be the plan's most fragile premise.

**[H] The price feedback loop has a phase transition threshold**
Below some critical economic weight threshold (minority chain holding <X%
combined custody+volume), the price gravity well is too weak to pull actors
back. Above it, the feedback stabilizes rapidly. This would explain the
empirically observed pattern where Bitcoin forks either die very quickly
or persist for years — with few intermediate outcomes. If this threshold
exists, identifying it is a primary research deliverable.

**[H] Node configuration attractors exist independent of actor rationality**
Node configurations in Bitcoin (topology, software version, mempool policy,
pool affiliation) may have stable attractor states that the network converges
toward via individually rational local optimization — regardless of whether
actors prefer security. Mining pool centralization (variance reduction draws
miners to large pools) and eclipse-vulnerable peer selection (efficiency
optimization reduces connection diversity) are candidate attractors. Each
is reached by rational steps; the basin is the problem, not the actor.
→ Warnet is well-positioned to test this via Monte Carlo over initial
configurations and Lyapunov stability testing of candidate attractors.

**[OBS] Custody providers are structurally dampened in dynamic scenarios**
See [H] above. The static 70% weight assigned to custody may not survive
contact with dynamic node behavior. This should be flagged as a modeling
assumption in the paper — the dual-metric model is validated for static
fork snapshots but not yet validated for dynamic scenarios.

**[OBS] Fork depth should be a risk multiplier, not just a binary filter**
Current implementation: below threshold → ignore, above threshold → analyze.
A 3-block fork forming in 5 minutes likely indicates more fundamental
disagreement than a 10-block fork that built slowly over hours. Depth
rate-of-change is probably more informative than depth alone as a predictor
of fork resolution time and economic impact. The binary filter discards
information that should be fed into the risk score.

**[OBS] The two active codebases are not cleanly integrated**
`warnetScenarioDiscovery/monitoring/` performs economic analysis that
conceptually feeds into tests run by `warnet_entity_distribution/`, but
there is no formal interface between them. They operate as standalone
tools. Phase 3 is the natural integration point — or a dedicated
refactor task before the convergence test runs begin.

**[OBS] Dynamic ideology is the load-bearing missing piece**
All current tests produce static snapshots: a fork happens, economic
weights are measured, a risk score is computed. The interesting research
questions (attractor dynamics, feedback loop stability, phase transitions,
correlated ideology effects) cannot be answered without the temporal
dynamics that DYNAMIC_IDEOLOGY_PLAN.md describes. This is not a nice-to-have
for Phase 3 — it is the precondition for the most important findings.

---
