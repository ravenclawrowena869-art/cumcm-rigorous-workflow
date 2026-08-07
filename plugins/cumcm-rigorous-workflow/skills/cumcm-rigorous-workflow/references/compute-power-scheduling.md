# Compute-power scheduling review card

Use this card for AI data-center scheduling with workload placement, renewable generation, storage, grid trading, latency, carbon, or multiobjective optimization.

## Define the layers

Keep these layers explicit rather than hiding them in one objective:

1. workload demand and service class;
2. GPU/compute allocation across region and time;
3. network migration and latency feasibility;
4. electric load mapping from compute activity;
5. renewable generation, storage, grid purchase, and grid sale;
6. cost, carbon, peak load, delay, and service-quality objectives.

Specify which layers are fixed in each subquestion. Do not optimize workload placement in a question that fixes compute load, and do not attribute gains to scheduling when they come only from electricity trading.

## Workload constraints

- Distinguish rigid training, deferrable batch, and online inference when the prompt does.
- Preserve task resource demand, duration, release time, deadline, continuity/preemption rule, and location eligibility.
- Enforce GPU capacity by type, region, and time.
- For migration, enforce bandwidth or migration capacity and end-to-end latency limits.
- Prevent double scheduling and account for any dropped, late, or unserved task explicitly.

## Energy constraints

At each region and time, write an auditable balance among load, direct renewable use, charge, discharge, grid purchase, grid sale, and curtailment. Keep signs and units consistent.

For storage, check:

- SOC recursion and initial SOC;
- terminal SOC requirement;
- energy and charge/discharge power bounds;
- charge/discharge efficiencies;
- simultaneous charge and discharge;
- throughput or degradation if economic claims depend on cycling.

If an LP has equivalent optima that allow meaningless simultaneous charging and discharging, use a two-stage LP before adding binary variables:

1. minimize the primary objective and obtain its optimum;
2. keep the primary objective within a small tolerance and minimize total storage throughput.

Upgrade to MILP only if physical mutual exclusion still fails or is essential.

For grid interaction, verify purchase/sale limits, whether simultaneous purchase and sale is allowed, tariff consistency, and whether carbon is assigned to purchases, sales, or both under the chosen accounting rule.

Do not let exports hide imports in a peak metric. Report at least actual import peak `max(G)`, export peak `max(P_sell)`, and the chosen net-exchange peak separately. If purchase and sale can both be positive in one period, prohibit it, prove why tariffs make it suboptimal, or report and justify every occurrence.

## Benchmark ladder

Use a consistent hierarchy when data permit:

| Benchmark | Meaning |
|---|---|
| Given baseline | Operating state supplied in the attachment |
| B0 | No-storage or no-flexibility structural baseline |
| B1 | Transparent rule-based strategy |
| B2 | LP/MILP optimized strategy |
| B3 | Robust, rolling, or multiobjective extension when justified |

Compare B2 with both the supplied baseline and the structural baseline. Do not claim the optimizer beats a rule strategy until B1 is implemented.

## Required result decomposition

Separate:

- purchase expenditure;
- sale revenue;
- net operating cost;
- carbon emissions under a stated boundary;
- peak net purchase power;
- actual import peak, export peak, and net-exchange peak as distinct quantities;
- renewable use and curtailment;
- storage throughput and terminal SOC;
- delay, migration, and service violations.

Report regional or service-class distributions when aggregation can conceal infeasibility or risk. A system-wide zero peak or negative cost requires a decomposition showing which regions and trades create it.

Do not present operating-cost improvement as investment return unless storage capital cost, degradation, and other omitted costs are included.

## Scale and solver checks

- Estimate variable and constraint counts before choosing exact or heuristic methods.
- Exploit separability only after checking cross-region coupling, network constraints, shared budgets, and global carbon limits.
- For large task sets, consider aggregation, candidate pruning, rolling horizons, decomposition, and warm starts before a metaheuristic.
- Recompute every key balance and objective from the returned solution.
- Report status, gap, runtime, infeasibility diagnostics, and maximum violation.
- For multiobjective work, normalize objectives and show extreme points before selecting weights or generating a Pareto set.

## Current project review reminders

- Keep the attachment's supplied baseline separate from a newly constructed no-storage baseline.
- When renewable energy is abundant, explain whether improvement comes from reduced purchase, reduced curtailment, or increased sale.
- Output six-region metrics rather than only a maximum or cross-region average when regional constraints matter.
- Pass forecast uncertainty into later scheduling when it materially affects feasibility, cost, carbon, or delay.
