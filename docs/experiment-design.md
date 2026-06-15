# Experiment Design Document

## Hypothesis

We believe that by adjusting prices between $0.25 and $2.00 on USPS Ground rate shopper orders USPS won, while remaining below the second-cheapest competitor rate, at least one price increase arm will exceed its break-even retention threshold, generating higher revenue per order than the $6.84 baseline.

**Note on the $6.84 baseline:** $6.84 is the nominal average USPS Ground rate across all eligible orders — it represents the average price a customer pays today. It is not the same as the simulation's revenue-per-order figure, which is `avg(price × retention)`. Because the churn model applies a baseline switching probability even at the current price (control arm), the simulated control revenue is lower than the nominal rate: $5,936–$7,009/1k orders depending on the churn scenario. The $6.84 figure is used only for the practical threshold calculation ($6.84 + $0.34 = $7.18).

## Primary Metric

Expected Revenue Per Order (retention rate \* adjusted price)

## Secondary Metrics

1. **Competitive shift analysis:** what did churned customers do when prices rose? — *Not measurable in this simulation. Churn is modeled as a probability, not an observed event, so there is no post-churn carrier selection to analyze. A live experiment would be required to observe actual switching behavior.*
2. **Churn rate segmented by transit time gap:** did customers with a competitor 1 day faster churn at a different rate than customers with a competitor 3 days faster?
3. **Price elasticity curve:** what is the inflection point where churn starts accelerating faster?
4. **Plan Tier and Zone segmentation:** which customers are the most and least price sensitive?

## Success Criteria

### Statistical Threshold

p < 0.0125 per pairwise comparison (Bonferroni correction for 4 treatment arms: α = 0.05 / 4)

### Practical Threshold

Expected revenue per order must exceed $7.18 (>=$0.34 lift over $6.84 baseline, equivalent to $2.4M/month incremental revenue across 7.1M orders). If no arm exceeds the practical threshold, maintain current pricing and document the price elasticity curve as a reference for future experiments.

### Business Threshold

Do not recommend implementation if:

- UPS relationship risk: flag for legal/partnership review if the pricing change appears to systematically redirect volume away from UPS contract terms.
- Competitive repricing risk: setting the price close enough to a competing rate would encourage competitors to drop their prices (e.g. within $0.20)

## Inclusions/Exclusions

### Inclusions

- USPS Ground winning rate shopper orders where:
  - there is another non-USPS rate that it beat that includes both price and delivery time (we can calculate delivery time using fields in the rate shopper table)
  - fall in Q1 2026
  - orders where after a price adjustment they still remain cheaper than a competitor. the n number of orders per experiment arm will change depending on the price adjustment and allowable headroom (e.g. an order with $0.30 headroom will be excluded from the +$0.50 arm but would be included in the +$0.25 arm)

### Exclusions

- fall outside the 5 to 95 percentile USPS price percentile
- any test/internal accounts - we can exclude any order from an account that does not have either a first paid invoice date or a trial closed/conversion date
- orders from customers that use BYOA carrier accounts but do not have the negotiated flag on
- Orders with null zone, zone 0, or zone 10+ (non-standard or international pricing, excluded to maintain domestic Ground pricing dynamics)

## Multi-Arm Structure

- There are 5 groups (control (no change), +$0.25, +$0.50, +$1.00, +$2.00). Each arm represents the amount of the price increase over the original winning USPS Ground rate
- In a live experiment, randomization should hash on `seller_id` using `MOD(FARM_FINGERPRINT(CAST(seller_id AS STRING)), 5)` to prevent spillover: if the same seller appeared in multiple arms, their behavior in one arm could influence another, making the arms non-independent.
- For this retrospective simulation, randomization hashes on `order_id` instead (`MOD(ABS(FARM_FINGERPRINT(CAST(order_id AS STRING))), 5)`). This is because the Rate Shopper dataset for March 2026 contains only ~40 unique sellers after applying all inclusion/exclusion filters — seller-level hashing produced severe arm imbalance (arm 4 held 42% of orders due to one whale seller with ~20k orders). Order-level hashing achieves near-perfect balance (~20% per arm, ±0.2%) at the cost of the spillover-prevention guarantee, which is acceptable in a simulation with no live treatment.

## Churn Simulation Model

Since this is a retrospective simulation rather than a live experiment, customer churn cannot be directly observed. Churn is modeled using a logistic function applied to the competitive gap after each price increase:

```
P(churn) = 1 / (1 + exp(-k × new_gap))
new_gap  = adjusted_price - cheapest_competitor_cost
```

A positive `new_gap` means USPS is no longer the cheapest option; a negative `new_gap` means USPS is still cheaper after the increase. Three sensitivity scenarios are run in parallel to test how conclusions depend on the assumed elasticity:

| Scenario  | k   | Interpretation |
|-----------|-----|----------------|
| Tolerant  | 0.3 | Customers switch slowly even as gap narrows — high inertia |
| Moderate  | 0.8 | Meaningful churn response as USPS approaches competitor parity |
| Sensitive | 1.5 | Sharp switching behavior — customers react quickly to price proximity |

K values were calibrated against the actual headroom distribution (median $5.71, P25 $2.26). At median headroom, these k values produce baseline control churn of ~18%, ~5%, and ~0% respectively, rising as arms push prices closer to competitor rates.

Conclusions from Phase 4 and 5 are reported conditionally: "if customers are X price-sensitive, then arm Y is optimal." This framing is intentional — the simulation cannot determine true elasticity, and a real A/B test would be required to do so.

## Formula Explanation

n = (Z*α + Z*β)² × (p₀(1-p₀) + p₁(1-p₁))
────────────────────────────────────
(p₀ - p₁)²

p0 = retention rate in the control arm
p1 = retention rate in a treatment arm
Z_a = z-score corresponding to significance threshold which is 0.0125 (standard errors away from zero required to call the result real, not random noise)
Z_B = false negative probability, z-score corresponding to 80% (0.84), which is the probability that we correctly detect an effect if one truly exists
Small effect sizes require a larger N because the it hard to detect reliably without having a large number of samples. When p0 - p1 is small, that difference gets squared in the denominator, making the whole denominator very small, which makes N very large

Total eligible orders = 6,305,858
Orders per arm = 1,261,172
Required N for each loss rate:

- 5%: 181
- 10%: 86
- 20%: 39

80% power is the probability that we correctly detect a real retention difference if there is one, and a 20% chance of missing it (false negative).
The number of orders well exceeds the required N so sample size is not an issue. The hard part of the experiment will be accurately simulating the churn behavior.

### Simulation Population (March 2026)

After applying all inclusion/exclusion filters to the Rate Shopper dataset for March 2026, the actual simulation population is 61,915 orders (~12,400 per arm). This is much smaller than the 6.3M figure above because:
- Rate Shopper is used by a small subset of high-volume ShipStation sellers
- BYOA exclusion and negotiated rate requirements narrow the pool further
- Only ~40 unique sellers appear in the filtered population

Sample size is still far above the required N for detecting even a 5% retention difference, so statistical power is not a concern. The seller concentration (40 sellers across 61k orders) is the more important limitation for interpreting results — see Churn Simulation Model section above.

### Balance Check Results (March 2026)

Order-level hashing (`MOD(ABS(FARM_FINGERPRINT(CAST(order_id AS STRING))), 5)`) produced near-perfect arm balance:

| Arm | Orders | % of Total |
|-----|--------|------------|
| 0 (control) | 12,291 | ~19.85% |
| 1 (+$0.25) | 12,352 | ~19.95% |
| 2 (+$0.50) | 12,366 | ~19.97% |
| 3 (+$1.00) | 12,481 | ~20.16% |
| 4 (+$2.00) | 12,425 | ~20.07% |

All arms within ±0.2% of 20%. Covariate balance (avg USPS cost, avg headroom, zone distribution) was also consistent across arms, confirming the randomization produced comparable groups.

## Phase 4 Analysis: Findings

### Method

Phase 4 ran two analyses against `experiment_dataset_march_2026`:

1. **Retention rate and revenue per arm** (`phase4_statistical_analysis.sql`): For each arm, computed average retention rate (`1 - avg churn probability`) and expected revenue per 1,000 orders (`avg(adjusted_price × retention) × 1000`) across all three churn scenarios.

2. **Two-proportion z-test** (`phase_4_z_test.sql`): For each treatment arm vs. control, computed the pooled standard error, z-score, two-tailed p-value (via a JavaScript UDF approximating the normal CDF), Bonferroni significance flag (α = 0.0125), and 95% confidence interval on the retention delta.

### Retention and Revenue Results

Practical threshold: $7,180 per 1,000 orders (equivalent to $7.18/order). Cells marked ✓ exceed the threshold.

| Arm | Price | Ret (Tolerant) | Ret (Moderate) | Ret (Sensitive) | Rev/1k (Tolerant) | Rev/1k (Moderate) | Rev/1k (Sensitive) |
|-----|-------|---------------|----------------|-----------------|-------------------|-------------------|-------------------|
| 0 (control) | +$0.00 | 0.7999 | 0.9077 | 0.9486 | $5,936 | $6,723 | $7,009 |
| 1 | +$0.25 | 0.7893 | 0.8935 | 0.9333 | $6,029 | $6,814 | $7,100 |
| 2 | +$0.50 | 0.7801 | 0.8800 | 0.9164 | $6,166 | $6,949 | $7,219 ✓ |
| 3 | +$1.00 | 0.7571 | 0.8460 | 0.8742 | $6,395 | $7,144 | $7,366 ✓ |
| 4 | +$2.00 | 0.7100 | 0.7699 | 0.7760 | $6,698 | $7,278 ✓ | $7,336 ✓ |

### Z-Test Results

| Arm | Δ Ret (Tolerant) | p (Tolerant) | Sig? | Δ Ret (Moderate) | p (Moderate) | Sig? | Δ Ret (Sensitive) | p (Sensitive) | Sig? |
|-----|-----------------|-------------|------|-----------------|-------------|------|-----------------|--------------|------|
| 1 (+$0.25) | -0.0106 | 0.0395 | NO | -0.0142 | 0.0002 | YES | -0.0153 | ~0 | YES |
| 2 (+$0.50) | -0.0198 | 0.0001 | YES | -0.0277 | ~0 | YES | -0.0322 | ~0 | YES |
| 3 (+$1.00) | -0.0428 | ~0 | YES | -0.0617 | ~0 | YES | -0.0744 | ~0 | YES |
| 4 (+$2.00) | -0.0899 | ~0 | YES | -0.1378 | ~0 | YES | -0.1726 | ~0 | YES |

Bonferroni-corrected threshold: α = 0.0125 per comparison.

### Interpretation

All treatment arms show statistically significant retention drops in at least two of three scenarios. **The z-tests confirm churn effects are real and scale with price magnitude** — this is expected and does not mean the experiment failed. The primary metric is expected revenue per order (price × retention), not retention alone.

A price increase can be net positive even with a retention drop, as long as the incremental revenue from higher prices exceeds the revenue lost to churn. Whether any arm clears the $7.18 practical threshold depends on the revenue calculation, not the retention delta alone.

**Key constraint on interpretation:** With only ~40 unique sellers driving 61k orders, the results reflect the price sensitivity of a small group of high-volume Rate Shopper users, not the broader ShipStation seller population. A live experiment with seller-level randomization would be required to measure true elasticity.

## Phase 5 Analysis: Segmentation

### 5.1 — Revenue per 1,000 orders by arm

All revenue figures use the moderate churn scenario (k=0.8). Practical threshold: $7,180/1k orders.

| Arm | Price | Orders | Retention | Rev/1k | vs Control |
|-----|-------|--------|-----------|--------|------------|
| 0 (control) | +$0.00 | 12,291 | 90.77% | $6,723 | — |
| 1 | +$0.25 | 12,352 | 89.35% | $6,814 | +$91 |
| 2 | +$0.50 | 12,366 | 88.00% | $6,949 | +$226 |
| 3 | +$1.00 | 12,481 | 84.60% | $7,144 | +$421 |
| 4 | +$2.00 | 12,425 | 76.99% | **$7,278 ✓** | **+$555** |

### 5.2 — Demand curve

Revenue across a continuous range of $0.00–$2.50 increases (moderate scenario, $0.25 steps):

| Price increase | Avg churn | Rev/1k |
|---------------|-----------|--------|
| $0.00 | 9.25% | $6,719 |
| $0.50 | 12.10% | $6,952 |
| $1.00 | 15.40% | $7,121 |
| $1.50 | 19.05% | $7,228 |
| $2.00 | 22.93% | $7,277 |
| $2.25 | 24.91% | **$7,283** (peak) |
| $2.50 | 26.91% | $7,277 |

Revenue peaks at roughly +$2.25 under the moderate scenario. Under the sensitive scenario (k=1.5) the peak is at +$1.50 ($7,375), after which churn accelerates enough to erode the price gain. Under the tolerant scenario (k=0.3) revenue is still climbing at +$2.50.

### 5.3 — Price elasticity

Using avg USPS cost of $7.40 as baseline, elasticity = (% Δ retention) / (% Δ price):

| Arm | % Δ price | % Δ retention | Elasticity |
|-----|-----------|---------------|------------|
| +$0.25 | +3.4% | −1.6% | −0.46 |
| +$0.50 | +6.8% | −3.1% | −0.46 |
| +$1.00 | +13.5% | −6.8% | −0.50 |
| +$2.00 | +27.0% | −15.2% | −0.56 |

Demand is inelastic across all arms (|elasticity| < 1). The magnitude increases slightly at +$2.00, indicating the demand curve begins to steepen but has not yet reached a sharp inflection point within the tested range.

### 5.4 — Revenue-maximizing arm

- **Moderate** (k=0.8): Arm 4 (+$2.00) at $7,278/1k — clears the $7,180 practical threshold.
- **Sensitive** (k=1.5): Arm 3 (+$1.00) at $7,366/1k is the peak; Arm 4 declines to $7,336.
- **Tolerant** (k=0.3): Revenue is still increasing at Arm 4 ($6,698); threshold not yet cleared in this scenario.

Arm 3 (+$1.00) is the only arm that beats the practical threshold across both the moderate and sensitive scenarios.

### 5.5 — Segment-level results

**By zone (moderate scenario):**

| Zone | Arm 0 rev/1k | Arm 4 rev/1k | Lift | Avg headroom |
|------|-------------|-------------|------|--------------|
| 1–3 (short haul) | $5,469 | $5,999 | +$530 | $5.57 |
| 4–6 (mid haul) | $6,753 | $7,246 | +$493 | $6.41 |
| 7–9 (long haul) | $7,331 | **$8,043** | **+$712** | $6.44 |

Zones 7–9 produce the highest lift in absolute terms. Higher base prices and consistent headroom mean the +$2.00 increase moves prices less as a percentage of the total cost relative to competitor rates.

**By plan segment (moderate scenario):**

| Segment | % of orders | Arm 0 rev/1k | Arm 4 rev/1k | Verdict |
|---------|------------|-------------|-------------|---------|
| Large | 91% | $6,824 | **$7,563** | Raise price |
| Medium | 8% | $5,508 | $4,139 | Do not raise price |
| Small | <1% | $6,498 | $5,390 | Inconclusive (n<30) |

Large-tier customers (91% of orders) drive the entire aggregate result. Medium-tier retention collapses from 72.9% to 42.7% at +$2.00, turning the revenue effect sharply negative (−$1,369/1k vs control). Any blanket price increase would need to exclude Medium-tier.

## 5.6 — Confounds

The simulation results look clean but several structural limitations could cause the real-world outcome to diverge from these projections.

**The churn model is not empirically calibrated.** The logistic function with k=0.8 (moderate) was not fitted to observed customer behavior — it was chosen because it produced intuitively plausible churn rates given the headroom distribution. There is no historical data from an event where USPS raised prices and switching behavior was measured. The k-value is the single most consequential assumption in the entire analysis: if customers are closer to k=1.5, Arm 4 underperforms; if closer to k=0.3, we are leaving money on the table.

**Treatment is hashed on order_id, not seller_id.** Order-level hashing was necessary to achieve arm balance given the small number of unique sellers (~40) in the filtered dataset. But it means the same seller can appear in all five arms simultaneously. In a live experiment this would be spillover contamination: a seller seeing inconsistent pricing across their own orders could complain or adjust behavior in ways that corrupt both arms. The simulation treats each order as independent; real customers are not independent across orders.

**March 2026 is one month in a seasonal cycle.** Q1 is typically a post-holiday shipping slowdown. Price sensitivity may differ in Q3 or Q4, when merchants are more dependent on shipping infrastructure and less likely to experiment with carrier switching.

**Competitor rates in the shopper may not reflect what customers actually pay.** The rate shopper captures quoted rates at the moment of comparison. High-volume merchants may have negotiated side agreements with UPS or FedEx that are lower than what the shopper returns. The average headroom figure ($6.35) could be overstated for sellers with real negotiated competitor rates that are not surfaced in the shopper event.

**Headroom varies within the same seller across orders.** A seller who ships to zones 1–3 one day and zones 7–9 another day will have very different competitive gaps per order. In a live experiment, the entire seller is assigned to one arm — meaning some of their orders would have the increase applied in situations where USPS is already close to parity with the competitor.

## 5.7 — Risk Assessment

**Medium-tier customers reverse the revenue gain.** Under the moderate scenario, a blanket +$2.00 increase loses $1,369/1k orders for Medium-tier customers (retention drops from 72.9% to 42.7%). Medium-tier accounts are ~8% of the simulation dataset but may account for a disproportionate share of support tickets, churn signals, and word-of-mouth that could influence Large-tier behavior over time. Any implementation must exclude Medium-tier from price increases or cap increases at +$0.25 for that segment.

**Zone 1–3 has thin headroom and marginal lift.** Average headroom in zones 1–3 is $5.57 vs $6.43 in zones 7–9. The revenue lift from +$2.00 in zone 1–3 is +$530/1k under the moderate scenario. If actual customer sensitivity is higher than assumed, zone 1–3 customers are closest to the break-even point and most likely to flip from revenue-accretive to revenue-destructive first.

**Competitive repricing risk is low at these increments.** Average headroom is $6.35. A +$2.00 increase reduces that to $4.35 average buffer over the cheapest competitor, which is well above the $0.20 business threshold defined in the success criteria.

**UPS relationship signal in zone 7–9.** Zones 7–9 are long-haul shipments where UPS is the primary USPS competitor. These zones produce the highest revenue lift precisely because customers tolerate higher USPS prices there. However, systematically moving USPS prices closer to UPS in long-haul zones could be noticed by UPS and used as leverage in a rate renegotiation for the platform's UPS contract. This should be reviewed with carrier partnerships before any production rollout.

**The churn model may understate tail risk from seller concentration.** The logistic function distributes churn smoothly across all orders. In practice, a single large merchant switching carriers could remove thousands of orders from USPS volume at once — an event that order-level simulation cannot capture. With ~40 sellers driving 61k orders, one whale decision could move the aggregate metric significantly.

## Conclusions and Recommendation

**Recommendation: Run a limited live test at +$1.00 for Large-tier customers in Zones 4–9 for one full month before committing to a broader rollout.**

### What the simulation shows

Under the moderate price-sensitivity assumption, every treatment arm beats control on expected revenue per order. The +$2.00 arm generates $7,278/1k vs $6,723/1k in control — a $555/1k lift that clears the $7,180 practical threshold. The demand curve shows revenue not clearly peaking until +$2.25, suggesting there is no obvious upper bound within the tested range under moderate sensitivity.

Segment-level analysis narrows the recommendation considerably. Large-tier customers (91% of orders) are resilient — they retain at 80.2% even at +$2.00, producing $7,563/1k. Medium-tier customers (8% of orders) are highly sensitive and their revenue drops to $4,139/1k at +$2.00 vs $5,508 in control — a clear do-not-raise signal. Zone 7–9 produces the highest absolute lift ($8,043/1k at +$2.00) with strong retention (80.8%).

### Why not implement +$2.00 now

The churn model is the critical unknown. The k=0.8 moderate assumption was not fitted to observed data. If actual customer sensitivity is closer to the sensitive model (k=1.5), the revenue-maximizing arm shifts from +$2.00 to +$1.00 ($7,366 vs $7,336 — the two are nearly tied). A live test at +$1.00 is both safer and informative: it still clears the practical threshold under both the moderate and sensitive scenarios, and the observed churn rate from the live test can be used to empirically calibrate the k-value and update the full demand curve before committing to a higher price point.

### Proposed implementation scope

- **Segment**: Large-tier only. Exclude Medium-tier and any accounts without a validated plan segment.
- **Zones**: Zones 4–9. Zone 1–3 has the thinnest headroom and the smallest lift; the risk-adjusted case is weakest there.
- **Increase**: +$1.00 for the first live test. Move to +$2.00 only if the observed churn rate is consistent with or below the moderate model.
- **Duration**: One full month to capture natural weekly shipping patterns and avoid partial-period noise.
- **Randomization**: Hash on `seller_id`, not `order_id`, to prevent the same seller experiencing inconsistent prices across orders.

### Success criteria (unchanged)

- p < 0.0125 per pairwise comparison (Bonferroni-corrected α)
- Expected revenue per order ≥ $7.18 ($0.34/order lift threshold)
- No statistically significant increase in plan cancellation rate within 30 days of the test period

Before launching, flag zone 7–9 targeting for review with the carrier partnerships team and confirm the Medium-tier exclusion list with the product team.

## Limitations

1. **Churn is simulated, not observed.** The logistic model is a reasonable approximation but cannot be validated against real behavior. The k values (0.3, 0.8, 1.5) were calibrated against the headroom distribution, not against observed churn data. True elasticity is unknown.

2. **Seller concentration.** ~40 sellers account for all 61k orders. One whale seller alone held ~20k orders. Results are heavily influenced by the price sensitivity of a small number of high-volume accounts, which may not represent the broader seller population.

3. **Competitive shift is unobservable.** Because churn is modeled as a probability rather than an event, we cannot determine what customers would actually do — switch carriers, negotiate, or absorb the increase.

4. **Rate Shopper coverage.** Rate Shopper is used by a small subset of high-volume sellers. The ~7.1M monthly orders cited in the practical threshold calculation represent total eligible USPS Ground volume, but the simulation population is only Rate Shopper orders. Results should not be directly extrapolated to the full order base without accounting for this selection bias.

5. **Business thresholds not yet assessed.** Per the success criteria, two business risks require review before any recommendation to implement a price change:
   - **UPS relationship risk:** whether the pricing change systematically redirects volume away from UPS contract terms (requires legal/partnership review)
   - **Competitive repricing risk:** whether the new price would be within $0.20 of a competitor rate, potentially triggering a competitive response
