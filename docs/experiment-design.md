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

## Phase 5 Analysis: Segmentation (Pending)

Secondary metrics 2–4 will be addressed here once the following SQL analyses are complete:

- **Transit time gap segmentation** — churn rate by gap between USPS and competitor transit days
- **Price elasticity curve** — simulated churn rate across a continuous range of price increases to identify the acceleration point
- **Plan tier and zone segmentation** — revenue and churn by billing plan tier and shipping zone

## Conclusions and Recommendation (Pending)

*To be completed after Phase 5 segmentation analysis.*

## Limitations

1. **Churn is simulated, not observed.** The logistic model is a reasonable approximation but cannot be validated against real behavior. The k values (0.3, 0.8, 1.5) were calibrated against the headroom distribution, not against observed churn data. True elasticity is unknown.

2. **Seller concentration.** ~40 sellers account for all 61k orders. One whale seller alone held ~20k orders. Results are heavily influenced by the price sensitivity of a small number of high-volume accounts, which may not represent the broader seller population.

3. **Competitive shift is unobservable.** Because churn is modeled as a probability rather than an event, we cannot determine what customers would actually do — switch carriers, negotiate, or absorb the increase.

4. **Rate Shopper coverage.** Rate Shopper is used by a small subset of high-volume sellers. The ~7.1M monthly orders cited in the practical threshold calculation represent total eligible USPS Ground volume, but the simulation population is only Rate Shopper orders. Results should not be directly extrapolated to the full order base without accounting for this selection bias.

5. **Business thresholds not yet assessed.** Per the success criteria, two business risks require review before any recommendation to implement a price change:
   - **UPS relationship risk:** whether the pricing change systematically redirects volume away from UPS contract terms (requires legal/partnership review)
   - **Competitive repricing risk:** whether the new price would be within $0.20 of a competitor rate, potentially triggering a competitive response
