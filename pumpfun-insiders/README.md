# PumpFun Insider Wallet Investigation

### Following the first buyers. Mapping recurring addresses. Tracing the capital behind them.

The first transactions after a token launch can reveal more than a price chart. They can show who arrived early, whether the same addresses keep appearing, and how those addresses obtained the funds they used to trade.

This project sets out a reproducible investigation into recurring early buyers across PumpFun launches. It connects launch activity, wallet histories, funding transfers, and subsequent exits into an evidence trail that other researchers can inspect.

The central question is simple:

> When apparently separate launches attract the same early wallets, are we seeing ordinary automated trading, shared infrastructure, coordinated capital, or a relationship that deserves closer investigation?

**Repeated wallet activity does not, by itself, prove insider trading.** Early entry is an observable behavior. Common control, privileged information, and intent require separate evidence.

## 1. Implementation Status and Quick Start

This repository contains working standard-library Python CLIs for scanning a supplied launch manifest and finding shared direct SOL funding sources. No live dataset has been collected and no wallet findings have been established.

**Decoder scope:** the scanner supports only the original 129-byte Pump `TradeEvent` layout. Extended events, newer quote-asset formats, and other instruction families are deliberately rejected. This means modern launches may produce no decoded trades. Check coverage and validate the event layout against the protocol version before interpreting output. This is a bounded research implementation, not a comprehensive current-protocol indexer.

Requires Python 3.10 or later. No third-party packages are required.

```bash
python3 -m unittest discover -s tests -v
export SOLANA_RPC_URL='https://YOUR_MAINNET_RPC_ENDPOINT'
python3 wallet_scanner.py --manifest data/launches.json
python3 funding_analysis.py --scan data/scan.json
```

Set your endpoint locally; do not commit credentials. RPC caches remain under ignored `work/`. Failed RPC requests are reported without echoing endpoint credentials.

Populate `data/launches.json` with independently verified records using this structure (replace every placeholder):

```json
[
  {
    "mint": "VERIFIED_TOKEN_MINT",
    "bonding_curve": "VERIFIED_BONDING_CURVE_ADDRESS",
    "creation_signature": "VERIFIED_CREATION_SIGNATURE"
  }
]
```

The empty manifest intentionally prevents an accidental run from appearing to be a completed investigation. The tool verifies that the supplied transaction succeeded; it does **not** independently prove that the supplied mint and curve were created by that transaction. Verify manifest roles manually and preserve supporting evidence.

`wallet_scanner.py` writes purchases, distinct-launch recurrence, and coverage to `data/scan.json`. It uses a slot window, not a first-N-buyer definition. Transactions within a slot are displayed deterministically by signature, which is **not** ledger order; no buyer ranks are assigned. The window includes the creation slot and `early_slot_window` subsequent slots. Creation-transaction purchases are flagged.

`funding_analysis.py` writes observed inbound transfers and shared-source candidates to `wallet_clusters.json`. It supports explicit parsed System Program SOL transfers, one hop, a configured slot floor and timestamp lookback. Same-slot funding is excluded because order is unresolved. It does not classify services, trace SPL funding, calculate profits, or establish common ownership.

`max_pages` bounds collection cost. A false `history_boundary_reached` means pagination stopped early. Missing transactions and transactions without matching supported events are recorded. The latter can be unrelated activity or unsupported trade formats; they must not be assumed to be non-trades. Current-slot collection is not a live stream: rerun after the observation window has finalized, and preserve the run interval separately.

The extended sections below distinguish implemented collection from the broader research roadmap. Statistical baselines, rank-based analysis, multi-hop paths, creator verification, and exit accounting describe future work unless explicitly documented above.

## 2. Why Investigate Early Buyers?

A single early purchase has many plausible explanations. A trader may operate a launch-monitoring bot, follow a public announcement, use an execution service, or simply buy quickly. Even repeated appearances can be expected when a wallet trades hundreds of launches.

The more useful question is whether multiple observations reinforce one another. Does an address enter unusually early across a defined sample? Do other recurring buyers receive funds from the same source? Were those transfers made before the launches? Do sale proceeds later converge? Does the pattern persist when ordinary high-frequency traders and public service wallets are considered?

This investigation focuses on the relationships between those observations. Speed is a starting point for analysis, not a verdict.

## 3. Research Questions

1. Which wallets repeatedly appear among the earliest successful buyers?
2. How often do those wallets trade launches outside the selected cases?
3. Do recurring buyers share direct or indirect funding sources?
4. Were relevant funds transferred before the launch and before the purchase?
5. Are common sources private wallets, exchanges, routers, or other services?
6. Do candidate groups enter and exit the same tokens repeatedly?
7. Do proceeds return to a common address after trading?
8. Are any observed links connected to the recorded launch creator?
9. Which patterns survive changes to the sample, timing window, and clustering rules?
10. What alternative explanation remains plausible for each proposed relationship?

## 4. Scope and Boundaries

The initial scope is public Solana transaction activity associated with PumpFun token launches and a bounded history of the participating wallets.

The unit of analysis is an address acting in a documented transaction role. A transaction signer, fee payer, token account, token-account owner, and economic beneficiary are not interchangeable. The analysis must identify those roles before attributing a purchase to a wallet.

The study distinguishes initial launch trading from later trading after migration. Pump's public documentation describes separate bonding-curve and swap components; the parser must identify the relevant program and instruction version for the study period. See the [official Pump documentation repository](https://github.com/pump-fun/pump-public-docs).

The investigation does not identify a natural person from an address alone. It also does not assume that different creator addresses represent different people or that one funding source implies one operator.

## 5. Proposed Repository Structure

```text
.
├── README.md                 # Research overview and methodology
├── wallet_scanner.py         # Planned launch and early-purchase parser
├── funding_analysis.py       # Planned bounded funding-path analysis
├── wallet_clusters.json      # Evidence-supported candidate relationships
├── investigation.md          # Verified findings and case studies
├── config.example.json       # Sample windows and collection parameters
├── data/
│   ├── launches/              # Launch manifest and inclusion decisions
│   ├── normalized/            # Decoded purchases and transfers
│   └── evidence/              # Transaction records used in published claims
└── reports/
    ├── coverage.md            # Missing data and collection limitations
    └── methodology.md         # Versioned definitions and analysis choices
```

The tree includes optional research artifacts that are not generated by the current CLIs. Raw provider responses may require separate storage because of size or redistribution restrictions. Public evidence exports should omit credentials and private endpoint details.

## 6. Define the Launch Sample Before Looking for Patterns

A defensible investigation begins with a defined universe of launches. Selecting only successful tokens, viral tokens, or launches already suspected of coordination will distort the result.

The launch manifest should record:

- Study start and end in UTC.
- Discovery source and collection method.
- Token mint and creation signature.
- Creation slot and instruction location.
- Recorded creator and the field used to identify that role.
- Relevant program and decoder version.
- Inclusion or exclusion decision with a reason.
- Data completeness and unresolved parsing issues.

Include failed and inactive launches when they meet the sampling rules. A token's later success must not determine whether its early buyers enter the dataset.

If comprehensive collection is impossible, describe the sample honestly. “Launches collected by this indexer during this interval” is more accurate than “all PumpFun launches” unless complete coverage has been established.

## 7. What Counts as an Early Buyer?

Use complementary definitions rather than a single arbitrary cutoff.

| Definition | Example research setting | Main limitation |
| --- | --- | --- |
| Time window | Purchases within 5, 15, or 30 seconds of creation | Block timestamps do not provide precise per-transaction arrival times |
| Transaction rank | First 5, 10, or 20 successful purchase transactions | One wallet can make several purchases |
| Unique-buyer rank | First 5, 10, or 20 distinct attributed buyers | Requires reliable role attribution and complete ordering |
| Slot window | Creation slot and the next few slots | Slots are not a fixed wall-clock duration |

These values are proposed analysis settings, not observed results.

For recurrence, count a wallet once per launch. Retain its individual purchases for trade analysis, but do not let repeated buys in one token inflate its cross-launch participation count.

Report creator-associated initial purchases separately. A launch transaction can contain creation and purchase instructions together; those events should not be silently mixed with later independent buyers.

## 8. Timing and Ordering

Define the launch reference as the successful creation event that initializes the relevant token market. Record its signature, slot, transaction position when available, and instruction position.

For a purchase with available timestamps:

```text
reported_time_offset = purchase_block_time - creation_block_time
```

This is a difference between reported block times. It is not a millisecond measurement of when a trader first learned about the token, submitted a transaction, or received confirmation.

Solana's [`getTransaction`](https://solana.com/docs/rpc/http/gettransaction) response can include a nullable `blockTime`. Missing timestamps must remain missing rather than becoming zero. [`getBlock`](https://solana.com/docs/rpc/http/getblock) can provide block transaction data for reconstructing ledger order within an available block.

Use the following distinctions:

- **Ledger order:** where transactions appear in the retrieved block representation.
- **Instruction order:** where creation and purchase instructions appear within a transaction.
- **Reported time:** the block timestamp exposed by the data source.
- **Submission time:** generally not established by finalized transaction records alone.

A same-slot purchase is not evidence of advance knowledge. Adjacent transactions do not establish a shared bundle or operator. Do not describe ordering as an exact race between traders when the dataset cannot support that precision.

## 9. Data Collection and Coverage

The proposed collection pipeline is:

```text
Launch manifest
    → transaction discovery
    → raw transaction retrieval
    → instruction and balance decoding
    → early-buyer attribution
    → cross-launch recurrence
    → bounded funding analysis
    → candidate relationship review
    → evidence-backed case studies
```

[`getSignaturesForAddress`](https://solana.com/docs/rpc/http/getsignaturesforaddress) returns signatures for transactions referencing an address, ordered newest first, with pagination parameters. It does not directly return a complete chronological trade ledger or prove that every referenced transaction is a purchase.

A collector should paginate to its declared boundary, retrieve transaction details, retain raw responses where permitted, and track failures. A null transaction response is unresolved data, not evidence that no transaction occurred.

Coverage reporting should include launches discovered, launches decoded, candidate transactions retrieved, successful purchases attributed, missing blocks, unsupported instructions, unavailable histories, and unresolved wallet roles. Keep denominators explicit: “12 of 100 collected launches” differs from “12 of 60 launches with complete early-trade data.”

## 10. Responsibilities of `wallet_scanner.py`

The broader scanner roadmap should identify successful launch and purchase events and produce an auditable normalized dataset.

Its responsibilities include:

1. Load a versioned launch manifest.
2. Retrieve relevant transactions and blocks as needed.
3. Reject failed transactions from executed-purchase counts.
4. Decode supported program instructions and relevant inner instructions.
5. Resolve account roles and versioned transaction account references.
6. Distinguish purchases from transfers, account creation, and other activity.
7. Attribute the buyer using decoded roles and token ownership information.
8. Preserve quote-asset and token amounts in integer base units.
9. Assign purchase rank, unique-buyer rank, and available timing fields.
10. Export evidence identifiers and explicit attribution uncertainty.

Do not infer a purchase from a positive token balance change alone. A transfer can increase a balance without representing a market buy. Likewise, a wallet's net SOL change can include fees, rent, transfers, and account closures rather than only trading expenditure.

Suggested purchase fields:

| Field | Meaning |
| --- | --- |
| `token_mint` | Asset under investigation |
| `creation_signature` | Launch evidence |
| `purchase_signature` | Purchase evidence |
| `slot` | Ledger slot |
| `transaction_index` | Block transaction position, if retrieved |
| `instruction_path` | Top-level or inner instruction location |
| `buyer_address` | Attributed trading wallet |
| `fee_payer` | Recorded separately from the buyer |
| `quote_mint` | Quote asset identifier or documented native-asset convention |
| `quote_amount_raw` | Decoded trade consideration in base units |
| `token_amount_raw` | Acquired token amount in base units |
| `time_offset_seconds` | Nullable difference in reported block times |
| `unique_buyer_rank` | Rank among distinct attributed buyers |
| `attribution_status` | Resolved, ambiguous, or unsupported |

## 11. Measuring Recurring Participation

For each wallet, calculate the number of distinct sampled launches in which it qualifies as an early buyer:

```text
early_launch_count(wallet) = count(distinct qualifying token launches)
early_sample_share(wallet) = early_launch_count / eligible_sample_launches
```

Also measure its broader launch activity where data permits:

```text
early_entry_rate(wallet) = early_launch_count / sampled_launches_bought_by_wallet
```

Report the underlying counts beside every rate. A wallet that buys nearly every launch may appear repeatedly without selectively targeting a particular creator or token group.

Useful descriptive outputs include rank distributions, distinct creator-address counts, entry-window sensitivity, purchase-size distributions, and participation across separate time periods. Separate observations of address diversity from claims about independent creators.

## 12. Wallet Co-occurrence

Let `L(A)` be the set of sampled launches where wallet A qualifies as an early buyer. For two wallets:

```text
shared_launches(A, B) = |L(A) ∩ L(B)|
jaccard_overlap(A, B) = |L(A) ∩ L(B)| / |L(A) ∪ L(B)|
```

These are descriptive overlap measures. They are not probabilities of shared ownership.

Two highly active bots can overlap often because both trade broadly. To assess whether overlap is unusual, compare against a baseline that preserves wallet activity and launch popularity. A suitable design is a degree-preserving randomization of the wallet–launch participation graph, constrained by relevant time periods so wallets are not assigned to launches outside their observed activity window.

If statistical testing is used, document the null model, random seed, number of randomizations, minimum sample requirements, and handling of multiple comparisons. Select thresholds on a development period and check them on a later period. A small p-value under one model does not identify an operator or establish intent.

## 13. Responsibilities of `funding_analysis.py`

The broader funding-analysis roadmap should reconstruct observed inbound flows before qualifying purchases.

It should distinguish:

- The earliest inbound transfer visible in the collected history.
- A transfer occurring shortly before a launch.
- A transfer contributing materially to available trading capital.
- A recurring source serving several candidate buyers.
- A source whose role is unresolved or publicly associated with a service.

Those categories answer different questions. The earliest visible transfer may not be a wallet's first-ever funding event. A transfer shortly before a buy may be incidental when the wallet already held sufficient capital.

For every edge, preserve sender, recipient, asset, amount, signature, slot, instruction location, timing relationship, source classification, and retrieval coverage.

Use explicit lookback and hop limits. Example sensitivity settings are 1 hour, 24 hours, and 7 days, with direct funding examined before two-hop paths. These are proposed settings and should be justified against the actual study sample.

## 14. Funding Paths and Their Interpretation

| Observed pattern | Supported observation | Question still open |
| --- | --- | --- |
| One address transfers to two buyers | A common immediate sender exists | Whether it is a public service or common controller |
| Separate buyers trace to a source through intermediaries | A bounded path exists | Whether each intermediary preserves meaningful economic linkage |
| Buyers receive funds shortly before launch | Funding and purchases are temporally close | Whether this is routine replenishment |
| Transfers use similar amounts | Funding sizes resemble one another | Whether amounts reflect common bot defaults |
| Buyers send later proceeds to one destination | Funds converge after trading | Whether the destination is an exchange or private treasury |
| A recorded creator funds a buyer | An observable creator-to-buyer transfer exists | Whether it reflects disclosed allocation, service payment, or coordination |

Trace native SOL and relevant token transfers separately. Wrapped assets, swaps, and account closures require explicit accounting; a graph built from raw balance differences alone can create false funding edges.

An observed transfer path does not necessarily establish the provenance of the exact units spent later. Funds can mix, split, and move through pooled accounts. Any allocation convention, such as proportional attribution, must be labeled as a model assumption.

## 15. Shared Infrastructure and False Connections

Public services can connect unrelated users. Exchanges, custodians, bridges, routers, relayers, and execution services may appear repeatedly in transaction histories.

A high-degree service address can make a graph look coordinated even when customers act independently. Therefore, keep service relationships separate from proposed private-wallet relationships and record the source and date of any service label.

An unlabeled address is not automatically private. When source classification is uncertain, leave it unresolved and show how the candidate relationship changes if that address is treated as infrastructure.

Useful checks include the source's recipient diversity, transfer frequency, amount distribution, persistence outside the selected launches, and whether it receives deposits from many unrelated addresses. These features guide review; they do not conclusively identify an exchange or custodian.

## 16. Wallet Clustering Without Overclaiming

Clustering should produce candidate relationships with traceable evidence. It should not convert every graph connection into a claim of common ownership.

Retain edge types such as:

- Repeated early-buyer co-occurrence.
- Direct pre-purchase funding.
- Shared immediate funding source.
- Repeated return of proceeds.
- Recorded creator connection.
- Shared execution characteristics.

Avoid automatic transitive ownership inference. Evidence connecting A to B and B to C does not necessarily justify treating A and C as one entity, particularly when B is a service.

Behavioral similarity alone should remain weak evidence. Similar fees, trade sizes, or instruction layouts can arise from shared software. More persuasive candidates combine separately verifiable observations, while accounting for signals that stem from the same underlying cause.

## 17. Suggested `wallet_clusters.json` Format

The following is an illustrative schema example. It contains placeholders, no real addresses, and no established cluster:

```json
{
  "schema_version": "0.1",
  "dataset_status": "illustrative_only",
  "clusters": [
    {
      "cluster_id": "candidate-example-001",
      "status": "unverified_example",
      "members": ["WALLET_A_PLACEHOLDER", "WALLET_B_PLACEHOLDER"],
      "relationship_hypothesis": "possible_shared_funding",
      "common_control_established": false,
      "evidence": [],
      "alternative_explanations": [
        "shared_public_service",
        "independent_users_of_the_same_trading_software"
      ],
      "coverage_limitations": ["no_transactions_supplied"]
    }
  ]
}
```

Published records should replace placeholders with verified identifiers and attach evidence to individual relationships. Avoid opaque confidence scores. If a score is introduced, publish its definition and validation; do not label it an “insider probability” without a defensible calibrated model and appropriate ground truth.

## 18. Entry, Exit, and Profit Analysis

After identifying a candidate group, examine what happened after entry. Did the wallets sell promptly, hold inventory, transfer tokens elsewhere, or send funds back to a shared destination?

For a fully traced position in one quote asset, a useful accounting starting point is:

```text
realized trading cash flow
    = attributable sale receipts
    - attributable purchase payments
    - separately incurred transaction and execution costs
```

Do not subtract fees twice if they are already included in decoded amounts. Do not call this complete profit when inventory, external transfers, or trading activity are missing.

Separate realized cash flow from remaining inventory valuation. Report quote assets independently unless a documented conversion method is applied. Token transfers between candidate wallets must not be counted as market sales, and external deposits must not be counted as trading revenue.

If exit tracking ends at migration or a transfer to an unobserved address, report the position as partially traced. A profitable trade can strengthen the description of outcomes; it does not establish advance knowledge.

## 19. Evidence Standards

Every substantive finding should connect to specific records.

| Evidence item | Minimum supporting material |
| --- | --- |
| Token launch | Mint, successful creation signature, decoded instruction |
| Early purchase | Successful purchase signature, attributed buyer, ordering basis |
| Funding transfer | Signature, instruction, sender, recipient, asset, amount |
| Recurring participation | Complete eligible launch list and per-launch purchase evidence |
| Candidate relationship | Explicit rule and supporting edges |
| Sale or proceeds transfer | Transaction and accounting interpretation |
| Service label | External source or documented classification basis |

Explorer links make review easier, but preserve normalized evidence and the original response or its integrity hash where feasible. Hashes establish that a saved artifact has not changed; they do not independently prove the accuracy of its interpretation.

Keep a strict separation between **observation**, **inference**, and **unresolved question**. For example, a transfer to two buyers is observable. Common capital management is an inference. Who controls the buyers can remain unknown.

## 20. Case Study Format for `investigation.md`

Each verified case should include:

1. **Claim:** A narrow statement that the evidence can support.
2. **Scope:** Tokens, dates, wallet roles, and selection criteria.
3. **Launch timeline:** Creation and qualifying purchases with ordering limits.
4. **Funding timeline:** Relevant transfers preceding those purchases.
5. **Cross-launch behavior:** Recurrence and baseline activity.
6. **Exit behavior:** Sales, remaining inventory, and traced destinations.
7. **Alternative explanations:** Public services, bots, incomplete history, or disclosed relationships.
8. **Assessment:** What is supported and what remains unresolved.
9. **Evidence index:** Transaction signatures, explorer links, and local evidence records.

Use explicit placeholders while drafting. Do not insert invented addresses, transaction signatures, dollar figures, or token names to make a case appear complete.

## 21. Hypotheses and Falsification

| Hypothesis | Evidence that would support further review | Evidence that would weaken it |
| --- | --- | --- |
| Recurrence reflects broad automated trading | High participation across many unrelated sampled launches | Concentrated participation after activity-adjusted comparison |
| Buyers share capital management | Repeated private-source funding and proceeds consolidation | Shared source resolves to a public pooled service |
| A group selectively targets creator-linked launches | Repeated documented creator links and selective entry | Similar behavior across an activity-matched control sample |
| Similar execution implies coordination | Similarity combined with independently verified capital links | Similarity explained by a common public tool |

The investigation should actively seek observations that weaken its preferred explanation. A credible report can conclude that a seemingly suspicious pattern is adequately explained by ordinary infrastructure or broad bot activity.

## 22. Robustness Checks

Repeat the analysis under reasonable alternative choices:

- Narrower and wider early-entry windows.
- Transaction rank and unique-buyer rank definitions.
- Inclusion and separate treatment of creator-associated buys.
- Direct funding only, then bounded additional hops.
- Different funding lookback periods.
- Service addresses included as context and excluded from private-cluster formation.
- Only launches with sufficiently complete retrieval.
- Separate study periods and an unseen validation period.
- Alternative minimum transfer sizes and dust handling rules.

Report relationships that disappear under small parameter changes. Stability can make a descriptive pattern more credible, but does not turn association into proof of control.

## 23. Known Limitations

**Coverage:** Missing launch discovery, pruned histories, provider limits, and unsupported instructions can change rankings and funding paths.

**Timing:** Reported block times cannot reveal precise submission latency or when information became available to a trader.

**Attribution:** Fee payers, routers, delegated authorities, and token-account owners may play different roles in a transaction.

**Identity:** One operator may use many addresses; one custodial address may represent many users.

**Selection:** Studying only winners or public controversies can manufacture an exaggerated appearance of coordination.

**Funding:** Shared infrastructure and mixed funds make economic provenance harder to establish than graph connectivity.

**Execution:** Shared software can produce similar transaction structures among unrelated traders.

**Interpretation:** On-chain data can document activity and relationships while leaving knowledge, intent, and off-chain agreements unresolved.

## 24. Reproducibility Requirements

A published run should include its launch manifest, UTC interval, code revision, decoder revision, configuration, commitment level, provider capabilities, retrieval date, and exclusion log.

Store asset quantities as integers with explicit decimals and asset identifiers. Deduplicate trades using transaction signatures and instruction locations; one transaction can contain multiple relevant instructions.

Retain cache metadata, retry outcomes, and coverage gaps. Pin the protocol documentation or interface version used for decoding rather than relying on a moving branch without recording its revision.

When sampling or randomization is involved, publish seeds and procedures. When labels or interpretations change, preserve a correction history so readers can understand which conclusions were affected.

## 25. Proposed Deliverables

### `wallet_scanner.py`

A documented collector and parser that exports successful early purchases, cross-launch participation, and attribution limitations.

### `funding_analysis.py`

A bounded transfer-analysis tool that preserves evidence for each funding edge and treats shared services explicitly.

### `wallet_clusters.json`

A machine-readable set of candidate relationships, including supporting transactions, alternative explanations, and unresolved fields.

### `investigation.md`

A narrative report containing only verified findings, transaction-backed case studies, and conclusions proportionate to the evidence.

The strongest deliverable is not a dramatic label. It is a result another researcher can reproduce, challenge, and correct.

## 26. Publication Checklist

- [ ] Publish the study interval and launch inclusion rules.
- [ ] Separate implemented functionality from planned functionality.
- [ ] Report collection coverage and parsing failures.
- [ ] Verify transaction roles and successful execution.
- [ ] Attach evidence to every published wallet relationship.
- [ ] Review common sources for public-service explanations.
- [ ] Compare recurrence against broader wallet activity.
- [ ] Run sensitivity checks before highlighting a cluster.
- [ ] Distinguish realized outcomes from incomplete position estimates.
- [ ] Remove illustrative records from any file presented as measured output.
- [ ] State clearly whether common control or privileged information remains unproven.

## 27. Research Position

This project treats “insider” as a hypothesis to examine, not a classification assigned to every fast wallet.

The useful progression is from verified purchases, to recurring participation, to documented financial relationships, to carefully qualified explanations. Each step needs its own evidence. Some investigations may stop at recurrence. Others may establish shared funding without establishing common ownership. A smaller number may justify deeper scrutiny of creator relationships.

An unresolved result is still useful when it explains exactly what was observed, how it was measured, and which missing facts would change the interpretation.

## 28. X Announcement

Use this version while the investigation is being built:

> I'm building an investigation into the first wallets entering PumpFun launches: recurring buyers, funding sources, and the evidence needed to distinguish automation from possible coordination.
>
> Methodology on GitHub. Findings will follow the transactions.

Use a findings-led version only after the underlying results are verified:

> I tracked the first buyers across a defined sample of PumpFun launches, then traced their funding and exits.
>
> The report separates recurring wallet patterns from evidence of coordination.
>
> Full methodology and transaction evidence on GitHub.

## 29. Technical References

- [Official Pump public documentation](https://github.com/pump-fun/pump-public-docs) — protocol interfaces and version-specific decoding references.
- [Pump program documentation](https://github.com/pump-fun/pump-public-docs/blob/main/docs/PUMP_PROGRAM_README.md) — bonding-curve accounts and trading context.
- [Solana: getSignaturesForAddress](https://solana.com/docs/rpc/http/getsignaturesforaddress) — address-based signature discovery and pagination.
- [Solana: getTransaction](https://solana.com/docs/rpc/http/gettransaction) — transaction retrieval and response fields.
- [Solana: getBlock](https://solana.com/docs/rpc/http/getblock) — block-level transaction retrieval.

These references support the technical collection design. They do not substantiate any wallet-specific finding, and the proposed analytical thresholds in this README are research choices rather than protocol requirements.
