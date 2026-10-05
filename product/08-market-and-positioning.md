# Market, Positioning and Pricing

- Status: Draft v0.1 (2026-10-04), proposed — requires founder ratification
- Owner: Product
- Basis: spec v0.2, [decision record](02-strategy-decisions.md)

Part of the product doc set ([index](README.md)). This document expands three decisions in the [decision record](02-strategy-decisions.md): D1 (beachhead and ICP), D7 (pricing, unit of value and pilot terms) and D8 (positioning, category and never-claim guardrails). It also covers the market side of risk R5 (market squeeze and willingness to pay). Why the product exists is in the [product brief](01-product-brief.md). Scope is in [MVP scope](03-mvp-scope.md). Phases and the proposed scenarios PA-P01 to PA-P19 are in the [roadmap](04-roadmap.md). Metric definitions are in [metrics](06-metrics.md), risk triggers in [risks and assumptions](07-risks-and-assumptions.md), and partner recruiting and contract terms in the [design-partner program](09-design-partner-program.md).

**How to read this document**

- Three kinds of statement are kept apart:
  - **Spec requires**: normative text in [spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md) or the [acceptance catalog](../acceptance/production_acceptance_catalog.yaml).
  - **Package implements**: what the reference package in this repository contains today.
  - **Proposed**: what this document recommends. It needs founder ratification.
- Nothing is deployed. The reference package has no running service, connector, verifier, UI, metering or billing. Prices, thresholds and dates are hypotheses unless the spec states them.
- Market facts come only from the two market research notes (market-accounting and market-implementation, compiled by October 4, 2026; the implementation note checked its facts against search results dated before that day). Each fact cites a numbered source in [section 11](#11-sources). Source numbers are local to this document; sibling documents number their sources independently.
- The "How Plumb differs" column in the landscape tables describes the specified design (spec v0.2), not shipped capability.
- Vendor capabilities are as described by the vendors and were not independently tested. Several 2026 launches may not yet be generally available, or may have changed.

**Reliability flags** used in the tables:

| Flag | Meaning |
|---|---|
| vendor page | Price or claim read from the vendor's own page |
| vendor-reported | Traction, efficiency or customer claims made by the vendor, directly or through trade press. Not independently checked |
| third-party | Price from a listing, aggregator, review site or blog rather than the vendor. Treat as approximate |
| snippet | Seen only in a search-result summary. The page was not fetched |
| vendor-run survey / small sample | Survey caveats are in [section 4](#4-market-size-and-pain-evidence) |

---

## 1. Summary

**The market is crowded at the workflow layer and filling up at the agent layer.**

- Plumb's wedge is monthly-close evidence readiness and review-package preparation for accounting firms, planned to be released preparation-only first (D2). Seven layers of players compete with it or substitute for it ([section 2](#2-market-landscape-for-the-accounting-wedge)).
- Chase-and-remind is table stakes. Practice-management suites, per-client close tools and point tools sell it at roughly $5-$99 a month, per user or per client. Xero and Intuit are bundling it: Xero's Document Requests (pricing not disclosed) and Intuit's Accountant Suite, whose entry tiers are free during the introductory period (US pricing from a secondary source) [M9], [M10].
- We found no incumbent producing, across a mixed stack, a provenance-backed review package that keeps UNKNOWN separate from CONFIRMED_ABSENT (PL-010). We also found none that does the implementation for the firm, verifies independently and publishes a human-labor ledger. This is absence of evidence from web searches (the implementation search was US-only), not proof.

**The "who implements AI for SMBs" market leaves a gap, but connectors are commoditizing** ([section 3](#3-who-implements-ai-for-smbs)).

- DIY builders (Zapier, n8n, Make, Copilot Studio) leave the customer as the systems integrator.
- Forward-deployed engineering (FDE) is priced for enterprises, and boutique agencies sell project labor with handoff risk. Gartner predicts 70% of enterprises will abandon agentic AI built through vendor FDE by 2028 (secondary coverage) [M76].
- Agentic implementation startups (superglue, Membrane, Rocketlane Nitro) sell to software vendors and resellers, not to end firms.
- Agent-built connectors are becoming table stakes. The spec's substrates (Nango, Airbyte, Temporal, Pulumi) are partners, and "we build integrations automatically" is not a headline.

**The pain is documented; the binding barrier is implementation, not price** ([section 4](#4-market-size-and-pain-evidence)).

- Getting documents from clients is the #1 workflow issue in Financial Cents' 2025 survey of 816 professionals (vendor-run; a rank, not a percentage) [M59]. 68% of firms in Uku's small 2026 survey would hand document chasing to an agent first (directional) [M61].
- 41% of small accounting firms cite time to learn and implement as the top AI barrier, against 6% for cost (Financial Cents 2026, n=486, vendor-run) [M60].
- Hiring experienced staff is the #1 issue for CPA firms with 11-30 professionals (AICPA PCPS, June 2026) [M62].
- No reputable source gives hours per client-month for close work or chasing. Every value claim must come from the firm's own month-0 baseline (D2).

**The beachhead is countable, but the ICP filters are unmeasured** ([section 5](#5-beachhead-icp-and-qualify-out)).

- D1: independent US firms of 10-40 staff that lean to CAS and bookkeeping, with at least 50 recurring monthly-close clients and mixed stacks.
- Census SUSB 2022 gives a reference band of about 16.7k employer firms: 13,415 CPA firms with 5-19 employees, plus 2,015 CPA firms and 1,247 other-accounting firms with 20-99 [M54]. How many of them pass the ICP filters is unknown. The P0-P1 funnel measures it.

**Positioning follows evidence** ([sections 6-8](#6-positioning)).

- Category: "verified implementation", glossed as "implementation you can audit". Short form: "Close-ready, with receipts."
- "Automatically constructed" is allowed only after M1R. "One owner and one request per missing item" is allowed only after Send-canary evidence. "Autonomous" is never used without PA-027-level evidence and the labor ledger shown.
- The 12-item never-claim checklist (D8) is a formal gate for sales, marketing and investor material, owned by the founder.

**Pricing is a hypothesis to test from day one** ([section 9](#9-pricing-and-packaging-hypothesis)).

- D7: price per active client-month. Prepare $15; Prepare + Chase $25, only once Send ships (earliest Send canary close around July 2027). Annual contract, $500 firm minimum, no seats, no implementation fee. Bill only attested packages. Price at no more than one-third of measured value.
- At 100 active clients, Prepare costs $18,000 a year. That is close to the average firm's entire tech spend of about $21,000 a year (vendor-run survey) [M58]. The price must therefore be justified against labor and outsourcing spend, not against the software budget.

**Channels are direct first** ([section 10](#10-channels)). Founder-led sales to firms, with one optional roll-up slot as a channel probe. MSPs and marketplace or MCP surfaces (Xero App Store, Karbon and Uku MCP servers) come later, as integration and distribution surfaces, never as coverage claims.

### 1.1 What the spec and package say about this topic

| Topic | Spec requires | Package implements | This document proposes |
|---|---|---|---|
| Commercial model | PL-001: every run ends in a verified operating intervention, an actionable external dependency, or an explained terminal failure. A recommendation, prompt or code archive alone does not count. The spec sets no price or packaging | No metering or billing. The proposed `listOutcomes` API returns an OutcomeObservation with `realized_value` and `review_minutes` ([OpenAPI](../api/openapi.yaml)). The verification levels include ECONOMIC_RESULT | Pricing per active client-month, billed only for attested packages, with credits keyed to PL-001 outcomes ([section 9.4](#94-billing-rules-tied-to-pl-001-outcomes)) |
| Value claims | spec §7 L136: no causal cycle-time claims from historical replay; report theoretical capacity, usable capacity and realized cash separately. PL-012: every opportunity needs a baseline and a prospective measurement plan | The OpportunitySpec contract allows only prospective measurement methods (STAGED_ROLLOUT, COMPARABLE_CASE_COHORTS) | Month-0 time study before shadow (D2). No ROI or hours-saved claim without a baseline and denominator. PA-P12 (economic-result attestation) before any external value claim |
| Integration claims | PL-007: an application logo is not an operation capability. PL-008: four maturity levels, with probe evidence for the higher ones | A synthetic [capability registry](../plumb/registry/capability_registry.json): 25 records covering 23 step types, 15 of the records PRODUCTION_VERIFIED, all placeholders | A published "supported environments v1" list per operation and maturity level (D3). No logo walls |
| Autonomy claims | PL-003: no autonomy claim if a person secretly did the implementation. PL-062: count manual engineering and failed builds. ADR-010: measure implementation autonomy separately from runtime autonomy. spec §1 L51 allows a supervised first delivery. Appendix A.6 (L580): avoid statuses that obscure manual engineering | The HumanEffortCategory enum and a SQL `human_effort` table exist. There is no effort-capture API and no autonomy-metric computation | The labor ledger as a customer-facing proof point, and a claim ladder tied to milestones ([section 6.5](#65-claim-ladder-what-we-may-say-when)) |
| Native features | PL-013: compare every candidate against the current process and a reasonable native-feature baseline; include configuration of existing products | The OpportunitySpec contract requires both CURRENT_PROCESS and NATIVE_FEATURE comparison entries | Qualify out single-ecosystem firms whose native tools work. Bill native-setting outcomes at the same rate as built ones (D7) |
| Claim limits | spec §25 L398, §26 L418, §28 L450, §29 L492, §15 L248, §20 L318 | The local contract tests pass (counts in [VALIDATION_REPORT.md](../VALIDATION_REPORT.md)). They do not validate models, business outcomes, tenant security, cloud isolation or integrations. The spec's "56 tests" figure (header table and Appendix C) is stale | The never-claim checklist as a formal gate ([section 8](#8-messaging-guardrails)) |

---

## 2. Market landscape for the accounting wedge

The market-accounting research found seven layers. Each subsection below has one table per layer. Pricing signals are as found, with reliability flags. Overlap ratings are the researcher's judgment.

### 2.1 Layer 1: Practice-management suites with client portals

These sell per user at roughly $19-$99 a month. All of them already ship document requests with automated client reminders. Through 2026 each is adding an AI agent or an MCP surface.

| Player | What they do | Overlap | How Plumb differs | Pricing signal | Source |
|---|---|---|---|---|---|
| Karbon | Workflow, email triage, client portal with tasks and documents, automatic client reminders (Business plan). Launched Kai, an "AI coworker", in early access on June 3, 2026, with agentic workflows, "agentic period close checks", an AI notetaker and a public MCP server | Medium-high | Kai works inside Karbon's data. Plumb builds verified collectors across systems Karbon does not own (document stores, ledger detail, mail history) and assembles the evidence package. Karbon's MCP server is a surface Plumb can use rather than compete with | Team $59/user/mo annual or $79 monthly; Business $89 annual or $99 monthly; Enterprise custom; Kai not disclosed (vendor page) | [karbonhq.com/pricing](https://karbonhq.com/pricing/) [M1] |
| Financial Cents | Workflow, CRM, passwordless client portal, document requests with automated follow-ups by email and SMS, time and billing, QBO integration, and a Month-End Close add-on. Publishes the annual workflow automation report | High for document requests and auto-chasing; medium for close | Reminders run on checklists humans configure. It does not join evidence to ledger obligations across systems or verify completeness against source state. Plumb can sit on top and configure its automations as a native setting (PL-013) | Solo $19/user/mo (annual); Team $49 annual or $69 monthly; Scale $69 annual or $89 monthly; Month-End Close add-on $5 per client per month, billed annually (vendor page) | [financial-cents.com/pricing](https://financial-cents.com/pricing/) [M2] |
| TaxDome | All-in-one practice management with client portal, itemized client requests, pipelines and reminders, e-sign and billing. TaxDome AI renames and tags uploaded W-2s and 1099s. The Atlas agent acts across clients, jobs and invoices: beta in summer 2026, GA planned for the end of Q3 2026 | Medium (tax-season intake rather than monthly close) | A closed suite oriented to tax intake. Plumb targets monthly-close evidence across external ledgers and stores, with verification and obligation-level de-duplication. Tax-return data is out of scope for v1 (IRC 7216; D1) | Essentials $800/yr; Pro $1,000/user/yr; Business $1,200/user/yr (third-party; vendor page returned 403) | [assembly.com/blog/taxdome-pricing](https://assembly.com/blog/taxdome-pricing) [M3] |
| Uku | Recurring tasks, time, billing and BI for small firms (Estonia-based). Uku MCP lets Claude or ChatGPT operate Uku directly on Elite and Enterprise plans. Publishes the AI in Accounting 2026 report | Medium | A system of record plus an MCP surface. It does not build collectors or verify evidence. A partner or integration candidate | Per user per month: Solo $19 annual or $25 monthly (1 member, 20 clients); Team $38/$49; Elite $48/$62; Enterprise $88/$99 (vendor page) | [getuku.com/pricing](https://getuku.com/pricing/) [M4] |
| Liscio | Client portal: secure document exchange, requests and organizers, Gmail and Outlook integration, e-sign. "File Intelligence" reads, classifies and names documents on arrival | Medium | A portal with AI filing. Plumb adds ledger-linked obligation tracking, verification and review-package assembly | File Intelligence $19/user/mo; Platform $49; Tax Team $99, billed annually; extra organizers and deliveries $5 each (vendor page) | [liscio.me/pricing](https://liscio.me/pricing) [M5] |
| Canopy | Modular, tax-oriented practice management: workflow, document management, time and billing, transcripts and notices, client portal | Low-medium | A module suite staff operate. Plumb's value is cross-system evidence work done for the firm | Time & Billing $24, Workflow $30, Transcripts $33, Document Management $40 per user/mo (annual); client management about $2.50 per client per year; a $150/mo engagement bundle (third-party, not verified on vendor site) | [capterra.com Canopy](https://capterra.com/p/150647/Canopy-Tax/) [M6] |

What this layer means for Plumb: firms will keep their practice-management tool. The message is "keep your PM tool" (D8). Where native reminders are enough, configuring them is a valid PL-013 outcome and bills at the same rate as a built one (D7).

### 2.2 Layer 2: Ledger-connected close and review tools

These sell per client at roughly $5-$50 a month, keep client questions attached to transactions, and add AI for coding errors and flux.

| Player | What they do | Overlap | How Plumb differs | Pricing signal | Source |
|---|---|---|---|---|---|
| Double (formerly Keeper) | Month-end close workspace linked to QBO, Xero, Sage Intacct and NetSuite: recurring workflows, file review and QC checks, client questions on transactions, document collection, receipts, accruals, 1099s, reports. AI codes bank feeds, catches coding errors, builds schedules and runs flux. Rebranded October 2025; $6.5M Series A December 2025 (over $12.5M total). Claims 4,000+ North American firms and 150% NDR (vendor-reported) | Very high: same monthly-close loop, same buyer | SaaS that staff operate, with fixed integrations to four ledgers. Plumb builds and verifies integrations into the whole stack (mail, document stores, PM tool, several ledgers), assembles provenance-backed packages and de-duplicates chases at obligation level. For a firm happy on Double, Plumb's added value is mostly cross-tool evidence | Per connected client per month, unlimited users; a tier with a $200/mo annual commitment; extra team email accounts $10/mo (vendor page). Core $10, Plus $25, Scale $50 per client/month (third-party; not confirmed on vendor page) | [doublehq.com/pricing](https://doublehq.com/pricing) [M7] |
| Xenett | Automated checks for coding errors and anomalies, structured reviews, monthly close workflow, client communication, accruals add-on | Medium-high on review-package preparation | A ledger-review product with fixed checks. Plumb adds evidence from outside the ledger, provenance, and workflows built for the firm | About $7.5 per client/mo (AI Review); about $10 (Workflow); Accruals + AI add-on $15 (vendor pages) | [xenett.com/pricing](https://www.xenett.com/pricing) [M8] |
| Financial Cents Month-End Close add-on | Close checklist add-on to the practice-management suite (see layer 1) | Medium | As above: checklists humans configure, without cross-system evidence joins | $5 per client per month, billed annually (vendor page) | [financial-cents.com/pricing](https://financial-cents.com/pricing/) [M2] |

What this layer means for Plumb: per-client pricing is accepted by bookkeeping firms (Double's model "mirrors how you package services") and sets the closest price anchor ([section 9.9](#99-benchmarks)). A firm on Double with a single ledger is a qualify-out (D1 item 4).

### 2.3 Layer 3: Ledger platforms

| Player | What they do | Overlap | How Plumb differs | Pricing signal | Source |
|---|---|---|---|---|---|
| Intuit QuickBooks (AI agents and Intuit Accountant Suite) | July 1, 2025: Accounting, Payments, Finance and Customer agents in QBO. October 28, 2025: Intuit Accountant Suite with consolidated client management, Books Close at Scale (beta) with standardized review templates and AI Client Insights (beta); document sharing "coming soon". UK launch February 11, 2026. Intuit claims customers are paid up to 5 days faster and save up to 12 hours a month (vendor-reported) | High for QBO-centric firms: close review at scale, at zero incremental price | Intuit optimizes inside QBO. Plumb's value is cross-ledger (QBO plus Xero) and cross-tool evidence, verified packages and firm-specific workflows. Intuit sets a $0 anchor for basic close tooling | Accountant Suite entry tiers free during the introductory period (UK and Australia explicit; US per a secondary source). QBO agents included in QBO plans; tier specifics not verified | [cpapracticeadvisor.com ?p=171765](https://www.cpapracticeadvisor.com/?p=171765) [M9] |
| Xero (JAX, Partner Hub, XeroForce, Hubdoc) | JAX finds unreconciled items, duplicates and missing documents. Partner Hub gives a view of client book health and month-end readiness; its Document Requests chase clients, send reminders and match documents to transactions. XeroForce is a natural-language custom agent builder with a month-end agent. Auto bank reconciliation (about 50% time saved, vendor-reported). Claude and M365 Copilot integrations. Announced July 9 and August 20, 2026. 5M customers. Hubdoc bundled free | Very high for Xero-standardized firms. XeroForce overlaps Plumb's "builds workflows for you" promise | Xero's agents work inside Xero. Plumb is ecosystem-neutral, verifies independently, accounts for labor, and brings evidence from outside the ledger (mail history, document stores, PM tools). Plumb must not compete head-on inside Xero-only firms | Not disclosed for JAX, XeroForce or Partner Hub. Hubdoc included in Xero Business plans | [itbrief.co.uk Xero](https://itbrief.co.uk/story/xero-expands-ai-tools-for-accountants-small-firms) [M10] |

What this layer means for Plumb: this is the strongest squeeze (R5). "A Xero-only firm should use Xero" (D8). The opening is the firm whose books are split across QBO and Xero, or whose evidence lives in inboxes and drives the ledger does not see.

### 2.4 Layer 4: AI-native ledgers and AI bookkeeping engines

| Player | What they do | Overlap | How Plumb differs | Pricing signal | Source |
|---|---|---|---|---|---|
| Digits | Autonomous General Ledger (March 2025) that categorizes, reconciles and reports. Accounting Agents (June 2025) run whole workflows and pause for human judgment. Partner program with wholesale pricing for firms; 700+ firms applied (vendor-reported). Nearly $100M raised | Medium | Digits requires moving clients to its ledger. Plumb works over the firm's existing systems and is not a ledger | Partner-only wholesale pricing; figures not disclosed | [cpapracticeadvisor.com Digits agents](https://www.cpapracticeadvisor.com/2025/06/23/digits-rolls-out-ai-agents-for-accounting-workflows/163521/) [M11] |
| Puzzle | AI-native ledger for startups and their bookkeepers: up to 98% auto-categorization (vendor-reported), AI accuracy review, automated reconciliations, agent-driven close management. Also sells software plus service | Low-medium | A ledger replacement. Plumb is an implementation layer over existing systems | Starter $30/mo, Core $72, Complete $120, Scale $360; Expert Reviewed service from $171/mo; catch-up bookkeeping $300+ per month of books (vendor page) | [puzzle.io/pricing](https://puzzle.io/pricing) [M12] |
| Truewind | AI bookkeeping and financial modeling for firms. $13M Series A (January 2025), over $17M total. Cites EisnerAmper and Frank Rimerman as customers (vendor-reported) | Medium | Aimed at mid-to-large firms' CAS teams. Plumb focuses on evidence collection, verification and implementation for smaller firms | Not found | [cpapracticeadvisor.com Truewind](https://www.cpapracticeadvisor.com/2025/01/08/truewind-accounting-ai-platform-raises-13-million-in-series-a-funding/154157/) [M13] |
| Botkeeper, Booke.ai, Docyt | Automated categorization, reconciliation, OCR and financial statements across many client files on QBO and Xero. Botkeeper sells only to firms | Low-medium: ledger work, not evidence collection or review packaging | Fixed products. Plumb builds firm-specific collectors and workflows and verifies outcomes | Booke AI $129/business/mo, firm plan by quote; Docyt from $299/mo; Botkeeper about $149/license/mo with volume bands (all third-party) | [rework.com roundup](https://resources.rework.com/tools/ai-agents/best-ai-agents-for-bookkeeping-2026) [M14] |
| Dext, Hubdoc | Receipt, bill and statement capture and extraction posted to QBO and Xero. Hubdoc is owned by Xero and bundled free; it retired bank and utility auto-fetch in June 2022 (secondary source) | Low-medium: capture is an input to Plumb's package | Capture only, with no obligation tracking, chasing logic or verification. Integration sources for Plumb rather than competitors | Dext Business from about $25.21/mo (US, 250 docs) (third-party); Hubdoc free with Xero | [datamolino.com comparison](https://datamolino.com/blog/pricing-and-features-autoentry-vs-hubdoc-vs-dext-vs-datamolino-in-2026) [M15] |

What this layer means for Plumb: these players automate ledger work or replace the ledger. Plumb does not post and does not replace ledgers (D3; spec Appendix B L598). Capture tools are sources to integrate.

### 2.5 Layer 5: Well-funded agent and close companies moving upmarket

| Player | What they do | Overlap | How Plumb differs | Pricing signal | Source |
|---|---|---|---|---|---|
| Basis | Long-horizon agents completing accounting workflows end to end across CAS, tax and audit; demonstrated an autonomous end-to-end 1065 return. $100M Series B at $1.15B (February 24, 2026), $138M total. Works with about 30% of the top 25 firms and 20% of the top 150, and claims 20-50% efficiencies (vendor-reported) | Conceptually high, different segment | Basis targets the largest firms with heavy deployment and ships fixed vertical agents. Plumb targets 10-40-staff firms, implements each firm's workflow on its own stack, and shows its labor. Basis could move down-market | Not found | [cpapracticeadvisor.com Basis](https://www.cpapracticeadvisor.com/2026/02/24/basis-raises-100-million-to-deploy-ai-agents-for-accounting-firms/178759/) [M16] |
| FloQast | Close checklists, reconciliations, AI Matching, auditable AI agents and the FloQast Transform agent builder. Passed $200M ARR (January 21, 2026), 3,500+ customers, EY alliance. A case study shows a top-100 firm's CAS practice using it | Low for small firms; conceptually high for close evidence | Priced and designed for in-house finance teams and large CAS practices | Quote-based. About $30k-$80k/yr; SMB contracts average about $43k (third-party estimates, unverified) | [itbrief.news FloQast](https://itbrief.news/story/floqast-surpasses-200m-arr-seals-ey-ai-alliance) [M17] |
| Numeric | Close management expanding into cash management (90%+ auto-match claim, vendor-reported). $51M Series B led by IVP (November 2025), $89M total | Low for the small-firm wedge | Serves in-house finance teams (for example Brex, Public.com), not small accounting firms | Not found | [numeric.io Series B](https://numeric.io/blog/numeric-raises-51m-series-b) [M18] |

What this layer means for Plumb: top-100 and 100+-staff firms are a qualify-out (D1 item 2). The watch item is down-market movement by Basis or Digits (R5).

### 2.6 Layer 6: PBC and document-collection point tools

| Player | What they do | Overlap | How Plumb differs | Pricing signal | Source |
|---|---|---|---|---|---|
| Content Snare | No-login, checklist-style request pages with unlimited automated email reminders, SMS, templates and an AI Request Builder. Listed in the Xero App Store | High on the chasing sub-task only | No ledger or obligation awareness, no verification of evidence against source systems, no package assembly. Shows that standalone chasing is a commodity | Annual: Basic $35/mo (20 active requests, 2 users), Plus $71, Pro $119, Custom $215+. Monthly: $42 / $85 / $143 / $258+ (vendor page) | [contentsnare.com/pricing](https://contentsnare.com/pricing/) [M20] |
| SmartVault (SmartRequestAI) | Document management with AI intake for tax firms. SmartRequestAI (announced July 22, 2025) generates per-client AI questionnaires, bulk requests, status dashboards and organized workpapers; claims 60-90 minutes saved per return (vendor-reported). Added automated reminders (up to five) in 2026, per search results | Medium: AI document collection, tax-season focused | Tax-return intake rather than monthly-close evidence; no cross-system verification or obligation de-duplication. SmartVault is also one of the document stores in the D1 stack, so it is a likely integration source | Not found | [cpapracticeadvisor.com SmartRequestAI](https://www.cpapracticeadvisor.com/2025/07/22/smartvault-to-launch-smartrequestai-to-automate-document-collection-and-client-intake-process-for-tax-professionals/165337/) [M21] |
| Suralink, AuditDashboard | Prepared-by-client (PBC) request lists for audit and tax: dynamic lists, secure file exchange, tracking dashboards. Suralink adds AI agents (Document Prescreen, Data Vouching, Financial Statement Tie Out) and a Workpaper Suite; claims up to 20 hours saved per engagement (vendor-reported) | Medium for evidence request and verification in an audit context | Engagement-oriented request lists for audit. Plumb's first scenario is recurring monthly close with ledger-linked obligations and automatic collection | Suralink custom/quote-based; a third-party listing cites $17/$29/$39 per user/mo (unverified). AuditDashboard not found | [suralink.com/pricing](https://www.suralink.com/pricing) [M19] |
| ClientClose, Chazy AI | Document-chasing startups | Chasing sub-task | As Content Snare | Not found | Seen only in directory and review listings; funding and traction not verified; no source URL recorded in the research notes |

What this layer means for Plumb: do not lead with chasing (D8). Leading with it puts Plumb in a $5-$99 category.

### 2.7 Layer 7: Substitutes for the firm or its labor

| Player | What they do | Overlap | How Plumb differs | Pricing signal | Source |
|---|---|---|---|---|---|
| Pilot (AI Accountant) | Tech-enabled bookkeeping sold directly to SMBs. On February 4, 2026 it launched a "fully autonomous" AI Accountant that onboards, configures, closes historical books and produces statements "with zero human intervention" (vendor-reported). 7,000+ clients served over a decade | Indirect: competes for the firm's end clients | Pilot replaces the firm; Plumb strengthens it. Plumb's labor ledger contrasts with unverifiable "zero human" claims | AI Accountant not found; bookkeeping from about $599/mo (secondary mention, unverified) | [cpapracticeadvisor.com Pilot](https://www.cpapracticeadvisor.com/2026/02/04/pilot-rolls-out-fully-autonomous-ai-accountant/177453/) [M22] |
| Zeni | AI bookkeeping with a dedicated finance team for startups; flat monthly fee based on spend | Indirect: end-client substitute | A service business. Plumb is infrastructure for firms | Starter from $549/mo ($494 annual); Growth from $799/mo ($719 annual) (vendor page) | [zeni.ai/pricing](https://www.zeni.ai/pricing) [M23] |
| Puzzle (software plus service) | See layer 4. Its Expert Reviewed service competes for the same end clients | Indirect | As layer 4 | Service from $171/mo (vendor page) | [puzzle.io/pricing](https://puzzle.io/pricing) [M12] |
| Offshore and outsourced staffing | Firms outsource AP/AR, tax preparation and financial statements. 80% outsource at least one service and 65% plan to increase (Intuit 2026 survey, vendor-run) | High: the budget Plumb competes for is often labor, not software | Plumb must beat offshore cost and quality per completed review package. Its labor ledger makes a like-for-like comparison possible | Offshore bookkeepers about $8-$45/hr; outsourced bookkeeping $300-$2,500/mo per SMB (vendor blogs, unverified) | [vjmglobal.com blog](https://www.vjmglobal.com/feeds/blog/cost-outsourcing-accounting-services-us) [M26], [M58] |
| Current (formerly Crete Professionals Alliance) | Thrive-backed roll-up acquiring majority stakes in CPA firms; a $500M plan reported June 4, 2025 (Reuters, via syndication); over $300M revenue, 20+ firms and 900 employees at that time. Thrive's in-house team builds OpenAI-powered tools. Rebranded as Current in June 2026; reports 31% average savings in tax-prep time (vendor-reported) | Builds its own AI tooling for acquired firms, so it competes for the same workflows | Roll-ups build in-house. Plumb could be the buy option for roll-ups and PE platforms without in-house AI teams, especially to standardize heterogeneous acquired stacks | Not applicable | [kfgo.com (Reuters)](https://kfgo.com/2025/06/04/thrive-backed-accounting-firm-crete-to-spend-500-million-in-ai-roll-up/) [M24] |
| Bench (shut down) | Tech-enabled bookkeeping service. Went dark December 27, 2024 after raising $113M, leaving about 35,000 US customers; acquired by Employer.com days later | None directly; a trust signal | Shows that firms and SMBs worry about vendor continuity and data portability. Tenant-owned storage, exportable artifacts and a vendor-continuity clause (D9) are designed to answer it | Not applicable | [geekwire.com Bench](https://www.geekwire.com/2024/vancouver-fintech-company-bench-accounting-announces-sudden-shutdown/) [M25] |

What this layer means for Plumb: the realistic comparison for a buyer is often "hire, offshore or Plumb". Pricing per active client-month ([section 9](#9-pricing-and-packaging-hypothesis)) and the labor ledger let a firm owner compare like for like. Direct-to-SMB autonomous accountants (Pilot, Zeni, Puzzle) could also shrink the small-firm market over time (R5).

### 2.8 Reading across the layers

Threat ratings are this document's judgment, drawn from the overlap ratings above and the R5 risk entry.

| Layer | Where incumbents are strong | Where Plumb's design is different | Threat to Plumb |
|---|---|---|---|
| 1. Practice-management suites | Workflow, portal, reminders; installed base; agents and MCP arriving | Cross-system evidence joins; verification; implementation done for the firm | Medium. Mostly integrate-with |
| 2. Ledger-connected close tools | Same buyer, same loop, per-client pricing, AI review inside the ledger | Evidence from outside the ledger; provenance; obligation-level de-duplication across staff | High, especially Double |
| 3. Ledger platforms | Free or bundled; native chase-and-match; agent builders | Ecosystem-neutral; mixed QBO and Xero books; mail and drive evidence | High for single-ecosystem firms (qualify them out) |
| 4. AI-native ledgers and engines | Automated ledger work | Not a ledger; no posting; works over existing systems | Low-medium |
| 5. Upmarket agents | Capital, top-firm penetration, end-to-end agents | Segment (10-40 staff); verified implementation with labor shown | Medium, rising if they move down-market |
| 6. Point tools | Cheap chasing | Knows what is already held, per client-period-obligation | Low as competitors; they set the commodity price for chasing |
| 7. Substitutes | Replace the firm or its labor | Strengthens the firm; like-for-like labor comparison | Medium; labor is the real budget |

Plumb is redundant for a firm standardized on one ecosystem that already covers chase, match and review: Xero Partner Hub plus JAX plus XeroForce; QBO plus Intuit Accountant Suite; or Double on one ledger. Plumb differentiates in mixed stacks: QBO and Xero clients, documents in Gmail or Outlook, Drive, SharePoint or SmartVault, a practice-management tool, and client-specific folders. That variation is exactly Appendix B's expansion test (different folder structures, chart-of-account conventions and minor API differences, spec Appendix B L654).

---

## 3. Who implements AI for SMBs

The market-implementation research found four ways a small business can get AI implemented today. Each leaves part of the job undone. Tables use the same shape as section 2.

### 3.1 DIY agent builders and iPaaS

All now offer "describe it in plain English and we build the workflow" copilots. The customer still has to find the opportunity, own the data plumbing, test the result and keep it running. In effect the owner becomes the systems integrator, which spec §1 L51 says Plumb must not require.

| Player | What they do | Overlap | How Plumb differs | Pricing signal | Source |
|---|---|---|---|---|---|
| Zapier (Agents, Copilot, MCP) | SMB-dominant no-code automation across 8,000+ apps; AI Agents billed by activity; Copilot builds Zaps from a prompt; Canvas; MCP access | Same SMB buyer and the same promise of cross-app automation without engineers | Zapier assumes the customer knows what to automate and will wire, test and maintain it. Plumb's design discovers the work, builds collectors, verifies against external state, and de-duplicates effects at the business-obligation level. No equivalent of the labor ledger or verification receipts | Free (100 tasks/mo); Pro from $19.99/mo annual ($29.99 monthly) for 750 tasks; Team from $69/mo annual; Agents add-on free tier 400 activities/mo, Pro about $33.33/mo annual (vendor page as fetched October 2026; may vary by region or promotion) | [zapier.com/pricing](https://zapier.com/pricing) [M27] |
| n8n | Visual and code workflow automation with AI agent nodes and an AI Workflow Builder; self-hostable. Reports 1,400+ enterprise customers and 1.7M monthly active builders. $180M at a $2.5B valuation (October 2025); SAP strategic investment at $5.2B (May 2026), to be embedded in Joule Studio | A common substrate for SMB AI agencies | A tool for builders. Someone still does discovery, data engineering, evaluation and maintenance | Starter EUR 20/mo (2,500 executions); Pro EUR 50/mo (10,000); Business EUR 667/mo (self-hosted), annual; Community Edition free (vendor page) | [n8n.io/pricing](https://n8n.io/pricing/) [M28] |
| Make (Maia, Make AI Agents) | Visual automation. Maia turns plain language into configured scenarios (reported launch June 2026); AI Agents decide at runtime (reported launch February 2026) | Natural-language construction for SMBs | Maia builds the scenario the user describes. Plumb's job starts earlier (finding the work) and continues later (independent verification, staged release, repair after schema change) | Free 1,000 credits/mo; Core $9/mo; Pro $16; Teams $29; Enterprise custom; Maia draws from credits (third-party, June 2026) | [make.com Maia](https://www.make.com/en/blog/maia-conversational-ai-coworker-for-ai-agents-and-automation) [M29] |
| Lindy | Credit-metered "AI teammate" agents for sales, support, ops and finance, with 40+ built-in skills and computer use | Sells to non-technical teams that want AI to do work | Lindy's output is the agent conversation. Plumb produces verified, versioned workflows with durable cases and typed operations | Free $50 in credits for 7 days; Team from $29.99/mo for 3,000 credits, up to $9,999.50/mo; top-ups $10 per 1,000 credits (vendor page) | [lindy.ai/pricing](https://www.lindy.ai/pricing) [M30] |
| Gumloop | No-code AI agents and workflows built by employees. $50M Series B led by Benchmark (March 12, 2026); named customers include Shopify, Ramp, Gusto, Samsara, Instacart | Automation without engineers | Targets tech-forward companies whose employees build for themselves. Plumb targets firms where nobody will build | Not found | [gumloop.com Series B](https://gumloop.com/blog/series-b) [M31] |
| Relevance AI | "AI agent operating system": Invent generates agents from prompts; Workforce builds multi-agent systems. $24M Series B led by Bessemer (May 2025) | Generates agents from a description | Agent generation is not implementation. Plumb treats connectors, collectors, verification and release as artifacts with acceptance gates | Not found | [techcrunch.com Relevance AI](https://techcrunch.com/2025/05/06/relevance-ai-raises-24m-series-b-to-help-anyone-build-teams-of-ai-agents/) [M32] |
| Microsoft Copilot Studio | Builds agents inside Microsoft 365 and Teams, billed by Copilot Credits | The default "AI implementation" many Microsoft 365 firms consider first | Bounded to Microsoft's ecosystem and still needs a builder. Plumb works across the ledger, document and email stack and owns verification and maintenance | $0.01 per credit pay-as-you-go or $200 per 25,000-credit pack per month; Copilot Business $21/user/mo; M365 Copilot $30/user/mo (third-party, 2026) | [cloudzero.com Copilot Studio](https://www.cloudzero.com/blog/copilot-studio-pricing/) [M33] |
| OpenAI AgentKit / Agent Builder | Visual Agent Builder launched October 6, 2025. On June 3, 2026 OpenAI announced shutdown on November 30, 2026, together with the Evals dashboard and API and the reusable prompts API; users are pointed to the Agents SDK or ChatGPT Workspace Agents | Model vendors moving into agent building | Shows platform-churn risk for businesses that build on a vendor's visual builder. Plumb's answer is customer-owned specs, tests and adapters (D9 exit terms) | Included in standard API model pricing | [developers.openai.com deprecations](https://developers.openai.com/api/docs/deprecations) [M34] |
| Workato (Genies) | Prebuilt agents ("Genies") for functions such as CPQ and HR onboarding on an enterprise integration platform (August 2025) | Production agents across thousands of apps | Sold to enterprises with integration teams | No public pricing. Entry around $10k/yr, median around $65k, mid-market $50k-$130k (third-party estimates) | [workato.com/genie](https://www.workato.com/genie) [M35] |
| Intuit QuickBooks native agents; Xero XeroForce | Agents embedded in the system of record (see section 2.3) | Directly touches reconciliation, categorization and reminders | Native agents act inside one vendor's data. Plumb reuses native settings where they suffice (PL-013) | Included in QBO tiers; XeroForce not disclosed | [tearsheet.co Intuit agents](https://tearsheet.co/artificial-intelligence/how-intuit-is-designing-embedded-ai-agents-in-quickbooks-to-serve-smbs/) [M9], [M10] |

### 3.2 Human-delivered implementation: FDEs, agencies, MSPs and roll-ups

FDE job postings rose more than 800% from January to September 2025 (Financial Times via Fast Company; the FT original was not accessed) [M41]. On September 29-30, 2026 Gartner predicted that 70% of enterprises will abandon agentic AI built through vendor FDE by 2028, because of cost and dependency. It also expects fewer than 20% of FDE engagements to turn custom requirements into standard product features, and advises defining IP ownership, knowledge transfer and an exit strategy from day one (Gartner page returned 403; details from secondary coverage) [M76].

| Player | What they do | Overlap | How Plumb differs | Pricing signal | Source |
|---|---|---|---|---|---|
| OpenAI forward-deployed engineering | Reportedly embeds FDEs with clients to customize models and build bespoke apps (reported July 2025) | Sells implementation as the product | Out of reach for small firms. Plumb's thesis is to automate the FDE's repeatable engineering and report the remaining human labor | Reported minimum of $10M per engagement | [the-decoder.com OpenAI consulting](https://the-decoder.com/openai-is-charging-at-least-10-million-per-client-for-its-enterprise-ai-consulting-services/) [M36] |
| Distyl AI | Ex-Palantir founders; FDEs plus software for enterprise processes (for example T-Mobile). $175M at a $1.8B valuation (September 2025) | Implementation as a product | Enterprise-only and staffed by humans | Not found | [siliconangle.com Distyl](https://siliconangle.com/2025/09/22/enterprise-ai-consultancy-distyl-ais-valuation-soars-1-8b-bumper-funding-round/) [M37] |
| Ema | Teams of agents automating HR, IT and finance; $77M Series B (September 23, 2026). The founder says AI can do "implementation, integration, and consulting work" that IT services firms were paid for | Targets the implementation and integration services budget | Enterprise-focused, with "AI employee" framing (a phrase Plumb avoids, D8). Coverage makes no specific claim of autonomous construction | Not found | [techcrunch.com Ema](https://techcrunch.com/2026/09/23/ema-raises-77m-as-ai-starts-eating-into-enterprise-software-and-services/) [M38] |
| Managed service providers (MSPs) | The SMB's outsourced IT provider. Informa's 2026 MSP 501 survey (600+ MSPs, published September 29, 2026): 91% offer or use AI solutions (up from 79%), 36% offer custom AI solutions (up from 21%), 57% expect AI to be among their biggest revenue gainers | Competes for the role of who implements AI for the SMB | MSPs lack engineering depth for data and ML work and scale with headcount. A likely channel: Plumb as the implementation engine MSPs resell ([section 10.3](#103-managed-service-providers)) | Not found | [channelinsider.com MSP 501](https://www.channelinsider.com/ai/msp-ai-revenue-growth-2026/) [M39] |
| Boutique SMB AI agencies | Done-for-you agent and automation builds, often on n8n or Zapier. Example: Implement AI (UK; GBP 1.3M raised in 2025) and many small agencies in vendor-written roundups | Same promise: "we implement AI for you" | Project-based human labor with handoff risk. Plumb's claim is repeatable implementation with verification and maintenance included, and Plumb never bills its engineering hours (D7) | About $4,500-$25,000 for a first SMB AI system (vendor-written guide; low reliability) | [layer3labs.io guide](https://www.layer3labs.io/ai-consulting-for-small-business) [M40] |
| Current (formerly Crete) | AI-enabled roll-up: buy the firm and implement centrally (see section 2.7) | Another answer to who brings AI to small accounting firms | Capital-intensive ownership. Plumb serves independent firms; roll-ups may be design partners or channels | Not applicable | [cpapracticeadvisor.com rebrand](https://www.cpapracticeadvisor.com/2026/06/03/crete-professionals-alliance-rebrands-as-current/184461/) [M24] |

### 3.3 Agentic implementation startups

These are real but narrow, and mostly aimed at software vendors, ERP implementers or enterprise data teams rather than SMB end customers.

| Player | What they do | Overlap | How Plumb differs | Pricing signal | Source |
|---|---|---|---|---|---|
| superglue (YC W25) | Calls itself "an agentic implementation platform" and "AI agents for enterprise implementations". Agents map and migrate legacy data, configure ERPs (NetSuite, Sage Intacct, SAP, Business Central, Acumatica) and keep syncs aligned; "you make the decisions and approve every write". Approved mappings run as saved tools with no AI at execution time. Claims an 80% cut in migration hours at a Sage VAR; customers include Cherry Bekaert and The Vested Group (vendor-reported) | Closest in category language | Sells to ERP implementation partners, value-added resellers (VARs) and SaaS onboarding teams, for migration and configuration. Plumb sells to the end firm and covers discovery, collectors, workflow runtime, independent verification and labor accounting. The naming collision is why Plumb does not use "agentic implementation platform" (D8) | Not found; funding unverified ($500K pre-seed per an aggregator, March 2025) | [superglue.ai](https://superglue.ai/) [M42] |
| Membrane (formerly Integration.app) | Membrane Agent builds integrations from prompts; Membrane Engine provides self-healing infrastructure; Membrane Packages are customer-owned, version-controlled integration code. Launched November 18, 2025; claims 100+ B2B SaaS customers (vendor-reported) | Agent-built integrations, self-healing maintenance, customer-owned code | Serves SaaS vendors building product integrations, not small-business operations. A possible substrate; evidence that agent-built connectors are commoditizing | Not found | [getmembrane.com announcement](https://getmembrane.com/articles/all/announcing-membrane-the-era-of-self-integrations) [M43] |
| Rocketlane Nitro | Agents inside professional-services automation software that migrate data (map, validate, sync), configure and set up, with approvals at every step; claims up to 50% less delivery effort (vendor-reported) | Agents doing implementation tasks with checks and approvals | A tool for implementation teams at software vendors. Plumb replaces the implementation team for the end firm | Not found; a reported $60M raise is unverified | [rocketlane.com Nitro](https://www.rocketlane.com/lp/nitro-competitor) [M44] |
| Ardent AI, Definity | Agentic data engineering: Ardent ($2.15M pre-seed, September 2025) builds an "AI Data Engineer"; Definity ($12M Series A, April 2026) optimizes Spark and lakehouse pipelines | Collector construction and repair | Targets data teams with a modern data stack. Plumb targets firms with no data team | Not found | [siliconangle.com Ardent](https://siliconangle.com/2025/09/25/ardent-ai-beats-odds-launch-worlds-first-agentic-engineer-data-pipeline-maintenance/) [M45] |
| Mimica | Task mining: observes desktop activity, ranks automation opportunities by ROI, produces implementation blueprints. $26.2M Series B (September 2025); large enterprises | Plumb's discovery step | Enterprise discovery that stops at blueprints. Plumb discovers from authorized system data, then builds, verifies and operates. Capture is out of scope for Plumb's first 180 days (D3) | Not found | [mimica.ai/about](https://www.mimica.ai/about) [M46] |
| Workday + Pipedream | Workday agreed to acquire Pipedream (November 19, 2025): 3,000+ connectors and 5,000+ customers, to let agents act across third-party systems | Agent integration infrastructure | Shows connector layers being absorbed by large vendors. Plumb keeps connector suppliers swappable behind contract tests (spec §3 L84) | Not found | [newsroom.workday.com](https://newsroom.workday.com/2025-11-19-Workday-Signs-Definitive-Agreement-to-Acquire-Pipedream) [M47] |

### 3.4 Substrates: partners, not competitors

The spec names Nango (integration management), Airbyte (source ingestion) and Pulumi Automation API (infrastructure) as candidate substrates that must pass Plumb's contract tests, and Temporal as the durable coordinator that does not supply business-level exactly-once guarantees for external APIs (spec §3 L84). All four are repositioning around AI agents.

| Player | What they do | Overlap | How Plumb differs | Pricing signal | Source |
|---|---|---|---|---|---|
| Nango | "Integrations for your products & agents": 1,000+ APIs, 7,000+ templates, integrations generated in code from plain-English use cases, MCP tools. The Management MCP (guide published September 4, 2026) lets coding agents create and update integrations, mint connect sessions, call APIs through a proxy, deploy functions and query logs, with development keys separate from runtime keys. Nango says the Management MCP is "still growing toward the full public API" | Provides the primitives Plumb's integration factory needs; its "build integrations with AI" pitch overlaps Plumb's connector claims | Developer infrastructure. Plumb adds discovery, business-object identity, verification, the authority envelope and delivery to firms. The candidate certified-transport substrate for M1 (D3) | Not found on homepage | [nango.dev blog](https://nango.dev/blog/how-to-build-ai-agent-integrations-using-the-nango-management-mcp) [M49] |
| Airbyte | 600+ replication connectors and a declarative Connector Builder. Agent Engine public beta (February 19, 2026); Airbyte Agents (May 4, 2026) with a Context Store, 50 agent connectors, controlled writes, MCP, SDK and CLI; claims 40% fewer tool calls and up to 80% fewer tokens (vendor-reported) | Ingestion and agent context; now writes too | A substrate. Plumb still separates ingestion from action execution and verifies each operation ("A test that reads an invoice does not establish access to bank statements", spec Appendix B L604) | Not found | [airbyte.com Airbyte Agents](https://airbyte.com/blog/airbyte-agents) [M50] |
| Temporal | Durable workflow orchestration marketed as the reliability layer for agents. $550M Series E at $12.55B led by Lightspeed (September 14, 2026) after a $300M Series D (February 2026); revenue run-rate up more than 200% year over year; 1.9T billable actions in August 2026; 4,300+ paying customers | Plumb's business runtime is specified on Temporal | Temporal supplies durable coordination. Plumb's effect ledger, UNKNOWN-effect reconciliation and obligation-level de-duplication sit on top | Not found | [temporal.io Series E](https://temporal.io/blog/temporal-raises-usd550m-series-e-at-usd12-55b-valuation-ai) [M51] |
| Pulumi (Automation API, Neo) | Programmatic preview, apply and refresh; Neo, an "AI platform engineer" agent (September 16, 2025; expanded May 2026). Pulumi reports agents drive about 20% of operations on its platform (snippet) | Agentic infrastructure changes with guardrails | Infrastructure scope only; Plumb wraps it in a narrow deployment adapter inside the envelope | Not found | [info.pulumi.com Neo](https://info.pulumi.com/press-release/pulumi-neo) [M52] |
| Composio | Prebuilt integrations and tools for AI agents; $25M led by Lightspeed (2025) | Agent access to business apps | Developer infrastructure for agent builders; a possible substrate | Not found | [cxodigitalpulse.com Composio](https://www.cxodigitalpulse.com/agentic-ai-startup-composio-secures-25-million-to-accelerate-workflow-automation-innovation/) [M48] |

### 3.5 What this means for Plumb

- **The gap is real but unproven.** The research found no well-funded player that combines opportunity discovery, building, independent verification and ongoing operation for ordinary small businesses. The search was US-only, and stealth or non-English entrants may be missed.
- **Agent-built connectors are becoming table stakes.** Nango, Membrane, superglue, Make's Maia, Zapier Copilot and n8n's AI Workflow Builder all claim a version of it. Plumb's defensible layer sits above connectors: verification, the authority envelope, effect and obligation integrity, and an honest accounting of human labor.
- **More entrants are coming.** Y Combinator's Fall 2026 Requests for Startups include "Self-Maintaining APIs" (agents that detect breaking API changes and open fix PRs) [M53].
- **Platform churn is a selling point.** OpenAI's Agent Builder shutdown and Workday's Pipedream acquisition support "your automation survives vendor churn because you own the specs, tests and adapters". The D9 exit terms make it contractual.
- **The FDE backlash is a positioning opening.** Buyers who expect "FDE work behind a UI" can be shown the labor ledger.

---

## 4. Market size and pain evidence

### 4.1 How many firms

| Measure | Figure | Source | Caveat |
|---|---|---|---|
| US NAICS 5412 (accounting, tax preparation, bookkeeping, payroll) | 120,085 employer firms; 135,960 establishments; 1,231,004 employees; $215.7B receipts. 114,312 firms (95.2%) have fewer than 20 employees; 88,381 have fewer than 5 | Census SUSB 2022 [M54] | Employer firms only; excludes nonemployer sole proprietors, a large share of bookkeepers. 2022 data, released April 10, 2025 |
| Offices of CPAs (541211) | 50,885 employer firms; 48,511 with fewer than 20 employees (35,096 fewer than 5); under-20 receipts $27.7B; 2,015 firms with 20-99 employees | Census SUSB 2022 [M54] | As above |
| CPA firms with 5-19 employees (derived) | 13,415 (48,511 minus 35,096) | Derived from [M54] | Derived by subtraction from the two published counts |
| Other accounting services (541219, includes bookkeeping firms) | 45,390 employer firms; 43,612 with fewer than 20 employees (receipts $13.75B); 1,247 with 20-99 employees | Census SUSB 2022 [M54] | Includes non-bookkeeping "other accounting services". The 5-19 band is not in the research notes |
| Tax preparation services (541213) | 19,464 firms | Census SUSB 2022 [M54] | Tax-only practices are a qualify-out (D1 item 3) |
| IBISWorld business counts | 85,223 accounting services businesses; 331,316 payroll and bookkeeping services businesses (2026, +2.2% vs 2025) | IBISWorld [M55] | Snippet only; methodology unknown and likely includes nonemployers |
| BLS accountants and auditors | 1,595,200 jobs (2025); projected +5% to 2035; about 115,300 openings a year; median pay $83,680 (May 2025) | BLS [M57] | Context for the capacity squeeze. Not used to compute any value figure |
| Canada NAICS 5412 | 62,102 establishments; 99.4% have 0-99 employees | ISED Canada [M56] | Canada is not in the beachhead (D1: Xero dominance makes much of it a qualify-out) |

### 4.2 Pain and adoption signals

| Finding | Figure | Source and sample | Caveat |
|---|---|---|---|
| Getting documents from clients is the biggest workflow issue | Ranked #1, ahead of manual administrative tasks. Clients take 5 days on average to submit requested documents | Financial Cents 2025 State of Accounting Workflow Automation; 816 accounting, bookkeeping and tax professionals, mostly North America; published April 2025, covering 2024 [M59] | Vendor-run survey. Gives a rank, not a percentage |
| Chasing is the first task firms would delegate to an agent | 68% want an AI agent to chase clients for missing documents; 62% require human approval before anything is sent or filed; 53% demand no model training on their data; zero firms fully trust AI | Uku AI in Accounting 2026; "dozens" of firms in 8 countries, mostly 1-10 employees; fielded May-June 2026 [M61] | Small, self-selected sample (mostly the Uku community). Directional only |
| Implementation time, not cost, is the barrier | 95% use or explore AI; 11% have embedded it across much of the firm; 20% report clear measurable ROI; 13% have a formal AI policy. Top barriers: time to learn and implement 41%, trust and accuracy 21%, data security 11%, skills gap 9%, cost 6%. Only 24% use AI for bank reconciliation | Financial Cents State of AI in Accounting & Bookkeeping 2026; n=486, mostly 2-30-person firms plus 27% solo; July 15-August 7, 2026 [M60] | Vendor-run survey |
| Training and implementation time is the top barrier in California | 56% use generative AI; 10% have it integrated across operations. Top barrier: training and implementation time (31%). Data security is the top client-facing concern (39%) | Ramp and CalCPA, Benchmarking the Modern CPA Firm 2026; 400+ California professionals [M63] | Vendor co-run; California only |
| Capacity pain is sharpest at 11-30 professionals | For firms with 11-30 professionals: hiring experienced staff is #1 and managing workload and capacity is #3. Solo and 2-10 firms rank tax-law complexity #1. Change management for technology and AI is #1 for 5-year impact at all sizes | AICPA PCPS CPA Firm Top Issues Survey, June 23, 2026 [M62] | Bands are counted in professionals, not total staff or Census employees |
| Firms already use AI and run fragmented stacks | 88% use AI for at least one client service; 30% have it fully embedded. 77% had hiring struggles; 56% say entry-level hires take 6+ months to reach billable capacity. Average tech spend $21,000 a year. About 10 apps per firm; 48% call their setup "functional but fragmented"; 41% fully integrated. Average 5 hours a week per accountant lost to data re-entry. 80% outsource at least one service; 65% plan to increase. 60% of clients ask accountants for proof of AI data protection | Intuit QuickBooks 2026 Accountant Technology Survey; 725 US accounting and bookkeeping professionals, May 2026; published July 2, 2026 [M58] | Vendor-run survey (Intuit). The 60% client figure is attributed to this survey in the research notes |
| CAS practices are growing | Median CAS growth 17%; median CAS net client fees per professional $156,250 (+29% vs 2022), driven by recurring fixed-fee engagements | AICPA and CPA.com 2024 CAS Benchmark, December 2024 (2023 data) [M71] | Older data |
| Agentic AI is early in tax firms | 14% of tax firms have agentic AI in their workflow; 80% expect it to be central within 5 years. 34% deploy AI at organizational level (21% a year earlier). 62% of professionals use generative AI daily | Thomson Reuters 2026 AI in Professional Services, April 16, 2026 [M66] | Tax-firm focus |
| AI use is weekly in many firms | 72% of firms use AI at least weekly, 35% daily; 77% plan to increase AI investment over 3 years | Wolters Kluwer 2025 Future Ready Accountant; 2,700+ professionals globally; October 8, 2025 [M67] | Snippet only; page returned 403 |
| Fear of errors and data integration block finance teams | 63% exploring AI; 16% implemented in day-to-day work. Barriers include fear of errors or hallucinations (35%) and data integration (34%) | Accounting Seed 2026; n=128 finance professionals; December 2025-January 2026 [M68] | Small sample |
| Small businesses use AI but have not embedded it | 76% use AI; 93% of users report positive impact; 14% have fully integrated it into core operations; 73% would benefit from more training and implementation resources. Barriers among users: data privacy and security (50%), lack of technical expertise (49%), choosing the right tools (48%) | Goldman Sachs 10,000 Small Businesses; n=1,256; January 27-February 4, 2026; published March 17, 2026 [M64] | Goldman pages returned 403. Headline figures confirmed by CPA Practice Advisor and Fortune; the barrier percentages come only from a search summary |
| AI use is flat at firms under 20 employees | 17-20% of US businesses used AI between December 14, 2025 and May 3, 2026: 37% at 250+ employees, 32% at 100-249, under 20% at 4 or fewer. Use rose at firms with 20+ employees; no significant change under 20 | US Census Bureau, Business Trends and Outlook Survey (BTOS), May 26, 2026 [M65] | The question was revised in November 2025 to "any business function"; not comparable with earlier BTOS rates |
| Lack of expertise blocks non-adopters | 92% of small firms use generic AI tools; 30% customize AI (up from 22%). Among non-users: lack of technical expertise 31%, lack of time 28%, finance 17% | Ireland's Small Firms Association; n=404; August 10, 2026 [M69] | Irish sample |
| Close delays come from waiting for data | Nearly 8 in 10 corporate finance professionals blame month-end close delays on waiting for data from other systems or departments | CFO Dive [M70] | Snippet only; corporate finance, not accounting firms |

**A recorded tension (D1).** 88% of accounting professionals already use AI for at least one service [M58], while spec §1 L49 targets "an ordinary business with little or no existing AI". In this wedge Plumb's value is implementation and verification, not first exposure to AI. The ICP is defined by implementation pain, not by absence of AI.

### 4.3 Trust and failure signals buyers have absorbed

| Finding | Source | Caveat |
|---|---|---|
| Trust in fully autonomous AI agents fell from 43% to 27% in one year; 2% of organizations have deployed agents at scale | Capgemini Research Institute; 1,500 executives, 14 countries [M80] | Publication date not stated on the page; coverage places it around July 2025 |
| More than 40% of agentic AI projects will be canceled by end-2027; "agent washing"; only about 130 of thousands of "agentic" vendors are genuine | Gartner, June 25, 2025 [M75] | From a search summary of the gartner.com page |
| 70% of enterprises will abandon agentic AI built through vendor FDE by 2028 | Gartner, September 29-30, 2026 [M76] | Page returned 403; details from secondary coverage |
| By 2028 over half of enterprises will stop paying for assistive AI and favor platforms that commit to workflow results | Gartner, April 2, 2026 [M77] | Page title and secondary coverage only |
| 63% of organizations lack, or are unsure they have, AI-ready data practices; 60% of AI projects without AI-ready data will be abandoned through 2026 | Gartner, February 26, 2025 [M78] | Search summary |
| 42% of companies abandoned most AI initiatives in 2025 (17% in 2024); the average organization scrapped 46% of proofs of concept | S&P Global Market Intelligence, 1,000+ enterprises [M74] | Enterprise sample |
| Only 5% of companies achieve bottom-line AI value at scale; 60% report no material value | BCG, September-October 2025 [M79] | Enterprise sample |
| About 5% of generative AI pilots achieve rapid revenue acceleration; buying from specialized vendors succeeds about 67% of the time versus about one-third for internal builds | MIT NANDA "The GenAI Divide", via Fortune, August 18, 2025 [M73] | Contested; methodology described inconsistently. Do not use in Plumb's own marketing |
| Builder.ai, once valued at about $1.5B, filed for bankruptcy after reports that its "AI" relied heavily on hundreds of human engineers | TechSpot, May-June 2025 [M81] | Press reports |
| The FTC's Operation AI Comply continues to pursue deceptive AI capability claims ("AI washing") | Holland & Knight analysis, August 18, 2026 [M82] | Law-firm analysis |

These signals shape the guardrails in [section 8](#8-messaging-guardrails): buyers are primed to distrust "autonomous" and "AI employee" and respond to verified outcomes, ownership and transparency.

### 4.4 What the evidence does not tell us

- **No reputable source for hours per client-month** on close work or document chasing. Blog figures were not used. The only time figure found (9.3 hours a week on client communication, CPA Practice Advisor 2024, cited via a Liscio blog [M5]) is secondary and is not used for pricing or value. Consequence: the month-0 time study (D2) is the only basis for a time-saving claim, and PA-P12 (economic-result attestation) is proposed before any external value claim.
- **Vendor bias.** The Intuit (725), Financial Cents (816 and 486) and Ramp/CalCPA (California) surveys are run by vendors. Uku's sample is "dozens" of firms. Accounting Seed's is 128.
- **Willingness to pay for this product is untested.** Cost is the least-cited barrier (6%) [M60], but that is not a price point. D7 tests it with paid pilots from day one.
- **The ICP pass rates are unknown** ([section 5.4](#54-addressable-pool-estimate)).
- **Fast-moving market.** Several facts (n8n and SAP, Temporal's Series E, the Agent Builder shutdown, Airbyte Agents, Gartner's FDE prediction, Karbon Kai, TaxDome Atlas, XeroForce) are recent and could change.

---

## 5. Beachhead ICP and qualify-out

### 5.1 ICP profile

From D1. Thresholds are hypotheses, ratified at M0.

| Attribute | D1 requirement | Why | Evidence |
|---|---|---|---|
| Firm type | Independent US accounting firm whose revenue leans to CAS and bookkeeping | Monthly-close work recurs, so the platform proof gets many similar but not identical tenants | Spec Appendix B is an accounting trace; 13 of the 30 catalog scenarios are accounting |
| Size | 10-40 staff | Capacity pain is sharpest around 11-30 professionals; solo and 2-10 firms rank tax-law complexity first | AICPA PCPS [M62] |
| Revenue mix | At least 60% from recurring bookkeeping/CAS (hypothesis) | Tax season (February to April 15) must not stall the domain owner | D1; the 60% filter may shrink the pool because most small CPA firms do both CAS and tax (dissent record) |
| Book | At least 50 recurring monthly-close clients with 12-24 months of history | Enough client-periods for a 30-client-period shadow cohort; history for backfill and baseline | D2 (at least 30 client-periods per firm); D5 (12-24 months backfill) |
| Stack | QBO and/or Xero client ledgers; Google Workspace or Microsoft 365 mail; a document store separate from the ledger (Drive, SharePoint/OneDrive, Dropbox or SmartVault); optionally Karbon, Financial Cents or Double, read-only | Mixed stacks are where incumbents are weakest | About 10 apps per firm; 48% "functional but fragmented" (vendor-run survey) [M58] |
| Region | One US region | Single-region deployment. The accounting envelope and plan fixtures are EU/EUR (eu-west-1) and must be re-templated to US/USD | Accounting [envelope](../fixtures/envelopes/accounting_evidence_preparation.json) and [plan](../fixtures/plans/accounting_evidence_preparation.json) fixtures |
| Commitments | Read OAuth; a named domain owner with about 2 hours a week; a 2-week baseline time study; anonymized labor-ledger publication; a paid pilot | Without these, M0 cannot pass and value cannot be measured | D1, D7, D9 |

### 5.2 Buying roles

| Persona | Role in the deal | What they need to see | Effort category when working with Plumb |
|---|---|---|---|
| Firm owner (buyer; HUMAN_OWNER of the envelope). Managing partner, COO or CAS director | Signs the pilot, the DPA and the envelope; approves data use and implementation | Measured value against the firm's own baseline; data-rights terms (TRAIN off by default, tax-return data excluded); a pre-agreed exit; the labor ledger | CUSTOMER_AUTHORIZATION for grants, envelope decisions and approving the reminder policy; DOMAIN_CLARIFICATION for convention answers, the baseline study and scheduled weekly check-ins |
| Reviewing accountant (champion, primary user). Reviewing manager or senior accountant who assembles packages today | Champions internally; runs the review surface; signs off packages | Correct, attributed packages that cut assembly minutes; sign-off stays with them; no "please send what you already sent" errors | NORMAL_BUSINESS_REVIEW; DOMAIN_CLARIFICATION for baseline-study recording |
| Bookkeeper (secondary user) | Uses the readiness ledger; later reviews and sends drafts | One shared obligation owner instead of per-person reminder lists | NORMAL_BUSINESS_REVIEW for draft review |
| Firm's client (affected party, not a principal) | Not in the deal. Receives staff-sent drafts only after the Draft gate, and Plumb-sent requests only after the Send gate | One consolidated request per missing item, never a stale one; proof that their data is protected | None (proposed): the client is not a principal, so its replies are business events, not labor-ledger entries |

Effort categories follow the amended D6 rubric in the [decision record](02-strategy-decisions.md) (founder decision 18, to ratify). All partner time lands in one of the five categories, and implementation work by anyone, firm staff included (wiring, mapping, writing the workflow), is ENGINEERING_INTERVENTION (spec Appendix B L652).

The Plumb domain expert joins first calls where the month-0 time study is designed. Plumb's engineers and the independent verifier do not sell. Plumb staff time appears in the labor ledger (the contracts still lack a principal type for Plumb staff, a recorded gap), and verifier results appear as verification receipts.

### 5.3 Qualify-out

| # | Qualify out (D1) | Why | What we offer instead |
|---|---|---|---|
| 1 | Solo and 2-4-person firms | Low budget; tax-law complexity is their top issue [M62] | Point tools or native reminders |
| 2 | Top-100 and 100+-staff firms | Basis and FloQast compete there; Basis works with about 30% of the top 25 firms (vendor-reported) [M16] | Nothing in the first 180 days |
| 3 | Tax-only or seasonal practices, and any in-scope source holding tax-return information (IRC 7216) | Tax season stalls the domain owner; IRC 7216 consent obligations (secondary commentary; verify with counsel) [M83] | Revisit only if counsel confirms monthly-close sources are outside 7216 (D9) |
| 4 | Firms standardized on one ecosystem whose native chase-and-match already works (Xero Partner Hub/JAX/XeroForce, Intuit Accountant Suite, Double on one ledger) | Plumb is redundant there (R5) | "Use Xero" (or Intuit, or Double). Exception: the firm wants Plumb to configure and verify those native features, a valid PL-013 outcome |
| 5 | Desktop or on-prem ledgers, and NetSuite or Intacct | Outside the certified operations for v1 | Nothing in v1 |
| 6 | Evidence held in closed portals that cannot be probed | PL-007 and PL-008 need probeable operations | Nothing in v1. The opportunity stays in the backlog with its blocking condition (spec §7 L132) |
| 7 | Document stores without webhooks plus overlap polling, or mail providers without request-id lookup | PA-005 and PA-009 cannot pass on them | Nothing until the provider supports it |
| 8 | Firms expecting posting or an "autonomous close" | Plumb does not post; a package is "ready for review" until sign-off (spec §15 L248; Appendix B L652) | Explain the boundary; walk away if posting is the requirement |
| 9 | Firms that will not grant read OAuth, name a domain owner with about 2 hours a week, run a 2-week baseline study, or allow anonymized labor-ledger publication | M0 and value measurement cannot happen | Nothing |
| 10 | Firms needing on-prem or multi-region | Single US region in v1 | Nothing in v1 |

### 5.4 Addressable pool estimate

**Reference band.** Census SUSB 2022 gives three employer-firm counts that bracket the ICP size range [M54]:

| Band | Firms |
|---|---|
| CPA firms (541211) with 5-19 employees | 13,415 |
| CPA firms (541211) with 20-99 employees | 2,015 |
| Other accounting firms (541219) with 20-99 employees | 1,247 |
| **Reference band** | **16,677 (about 16.7k)** |

**Why this is a reference band, not a market size.** It both overcounts and undercounts:

- Overcounts: it includes firms with 5-9 and 41-99 employees (outside 10-40), tax-heavy firms, single-ecosystem firms, and firms on desktop ledgers.
- Undercounts: it excludes other-accounting (bookkeeping) firms with 5-19 employees, which the research notes do not break out, and it is 2022 data.
- Units differ: Census counts employees, D1 counts staff, and AICPA counts professionals.
- It excludes nonemployer firms, which matters little here because the ICP needs 10 or more staff.

**ICP filters and what we know about each.** The pass rate of each filter is unknown. The funnel records it.

| Filter | What we know | How we measure it |
|---|---|---|
| 10-40 staff | Census bands do not align | Qualification call |
| At least 60% recurring CAS/bookkeeping revenue | Untested; may shrink the pool substantially (dissent record) | Qualification call |
| At least 50 recurring monthly-close clients with 12-24 months of history | Unknown | Qualification call |
| Mixed stack | About 10 apps per firm and 48% "functional but fragmented" [M58]. That is fragmentation, not necessarily mixed ledgers | D1 trigger: if fewer than 30% of the first 25 qualified calls have materially mixed stacks, narrow to QBO-centric firms whose evidence lives in email and drives |
| Not single-ecosystem with working native chase-and-match | Unknown | D1 trigger: 60% or more single-ecosystem re-opens the vertical; R5 trigger: at least 3 of 5 qualified prospects choose native tools after a PL-013 comparison |
| Provider assumptions (webhooks plus overlap polling; request-id lookup) | Unknown per provider | M0 probes |
| Commitments (OAuth, domain owner, baseline, ledger publication, paid pilot) | Unknown | D7 and D9 trigger: fewer than 2 paid pilot LOIs after about 30 qualified conversations |

**Illustrative arithmetic only.** The combined pass rate is unknown, so these rows are not estimates. They show what the funnel has to establish:

| If this share of the reference band qualifies | Qualified firms |
|---|---|
| 5% | about 830 |
| 10% | about 1,670 |
| 20% | about 3,340 |

Two readings follow:

- The pool is not the constraint for the first 180 days. D9 needs 5 design partners and at least 25 qualified conversations by week 8.
- It is the constraint for a venture-scale business. At D7 list prices, a qualified firm with 50-150 active client-months is worth about $9,000-$27,000 a year in Prepare revenue ([section 9.6](#96-per-firm-arithmetic)). Whether thousands, not hundreds, of firms qualify decides whether the beachhead is big enough. Proposed: report measured pass rates in the day-180 packet.

### 5.5 Cohort design

D1 varies stacks on purpose so that M1R and M5 test replication, not repetition:

- Tenants 1 and 2 share provider families but differ in folder structure and chart-of-accounts conventions (the PA-027 preconditions).
- Tenant 3 swaps one provider, forcing a non-VERIFIED_ADAPTER path.
- At least one cohort firm has both QBO and Xero clients.
- One optional slot for a PE- or VC-backed roll-up as a channel probe, off the critical path.

Recruiting, selection and contract terms are in the [design-partner program](09-design-partner-program.md).

### 5.6 Qualification checklist for first calls (proposed)

Each answer maps to a filter in section 5.4 and is recorded per conversation, so measured pass rates replace the illustrative ones by week 8.

1. How many staff, and how many are accountants versus bookkeepers?
2. What share of revenue is recurring bookkeeping/CAS versus tax?
3. How many clients do you close every month, and how many months of history do you hold for them?
4. Which ledgers do your clients use (QBO, Xero, both, other)? Any desktop or on-prem ledgers?
5. Where do client documents arrive: email (Google or Microsoft), a document store (Drive, SharePoint/OneDrive, Dropbox, SmartVault), a portal?
6. Which practice-management tool do you use, and do its reminders work for you today?
7. Who chases clients, and how do you know when two people chased the same item?
8. Do any of those sources hold tax-return information?
9. Who would be the domain owner, and can they give about 2 hours a week?
10. Will you run a 2-week baseline time study with our domain expert?
11. Will you grant read access by OAuth and allow anonymized publication of the labor ledger, failures included?
12. Are you prepared to pay a pilot fee credited to year one?

---

## 6. Positioning

### 6.1 Category

**"Verified implementation" for accounting firms**, glossed as **"implementation you can audit"** (D8).

Avoid:

- "Agentic implementation platform": superglue already uses it [M42].
- "AI employee", "AI teammate", "fully autonomous": trust in autonomous agents fell from 43% to 27% [M80], and "AI washing" draws enforcement [M82].
- "We build integrations automatically" as a headline: it is becoming table stakes ([section 3.5](#35-what-this-means-for-plumb)).

### 6.2 Headline and short form

**Headline (D8):** "Plumb connects the tools your firm already uses and builds your month-end evidence workflow for you, then proves it works on your own data: every document traced to its source, a review package ready for your accountant, and a receipt for every hour a human spent."

- Add "one owner and one request per missing item" only once the Send canary has evidence (never-claim item 12).

**Short form:** "Close-ready, with receipts."

### 6.3 Positioning statement (proposed)

For independent US accounting firms of 10-40 staff whose client accounting work runs across more than one ledger, inbox and document store, Plumb is verified implementation. It connects the tools the firm already uses, builds the month-end evidence workflow, and proves it works on the firm's own data. Unlike practice-management suites and ledger-native agents, which work inside one system and leave configuration to the firm, Plumb does the implementation across the stack, keeps unknown evidence separate from confirmed absence, and shows a receipt for every hour a human spent.

This statement describes the intended product. Until the evidence in [section 6.5](#65-claim-ladder-what-we-may-say-when) exists, external material says "we are building" or "designed to", not "does".

### 6.4 Proof points and when each first exists

The proof points are D8's. The phase in which evidence first exists comes from the phased plan in the [decision record](02-strategy-decisions.md) and the [roadmap](04-roadmap.md). Windows are hypotheses.

| Proof point (D8) | Evidence source | First exists | Spec basis |
|---|---|---|---|
| The per-deployment labor ledger across the five categories (CUSTOMER_AUTHORIZATION, DOMAIN_CLARIFICATION, NORMAL_BUSINESS_REVIEW, ENGINEERING_INTERVENTION, OPERATIONAL_REPAIR) | Effort ledger with the frozen rubric | P0 (ledger records entries end to end); per tenant from P1 | PL-003, PL-062, ADR-010 |
| Verification receipts | Independent verifier attestations | P2 (PA-001 attested on tenant 1) | PL-042, ADR-007 |
| Engineering hours per verified deployment, including failed attempts (EIH/VD) | Effort ledger plus build ledger | Tenant 1 baseline in P2; a three-tenant trend in P3 | PL-062, PA-027 |
| Correct-package rate, with denominators that include failures | Review surface plus verifier | P4 (sandbox); first full-close reading in P5 | Spec Appendix B L650-652 |
| Accountant minutes against the firm's own baseline | Month-0 time study plus review-surface timing | P5 (first full shadow close on tenant 1) | Spec §7 L136 |
| Duplicate and stale requests per client-period | Effect ledger plus provider logs, beside the 24-month reminder-history baseline (historical, non-causal) | Send canary in P6 or later: the earliest policy-approved Send canary close is around July 2027 (about weeks 39-41) | PA-005, PA-007 |

The customer-facing co-headline from M3-lite onward is accepted review packages per month, always shown with its rate over all eligible client-periods and with Plumb human minutes per accepted package (D10). The north star, EIH/VD, is a platform metric and an investor proof point, not a sales headline: it means little to a customer on its own, though each partner sees its own labor ledger (D9).

### 6.5 Claim ladder: what we may say when

Every external claim must match the evidence that exists at that moment and the released tier (Prepare, Draft, Send). Phases and windows are hypotheses from the phased plan.

| Stage | Evidence that unlocks it | What we may say | Still not allowed |
|---|---|---|---|
| Now (P0, weeks 0-2) | Spec v0.2; reference package (local contract tests, contracts and checkers only; counts in [VALIDATION_REPORT.md](../VALIDATION_REPORT.md)); synthetic scenarios | "We are building verified implementation for accounting firms and recruiting paid design partners." Describe the design and the partner terms | Any customer result; any integration coverage; "automatically"; any time-saving figure; any registry maturity |
| M0 (P1) | SANDBOX_TESTED probe receipts on tenant 1's real accounts; effort ledger live | "These exact operations are tested on a real firm's accounts at SANDBOX_TESTED", per operation | Logos; "integrates with X" in general |
| M1 (P2) | PA-001 attested on tenant 1 with the safety bundle; tenant 1 EIH/VD baseline; supported environments v1 published | "Agent-configured certified connectors and agent-built collection, verified on a live firm's data." Label the deployment "supervised", with labor shown | "Automatically constructed"; "generated integrations"; "autonomous" |
| M1R (P3) | PA-001 re-attested on tenants 2 and 3, with at least one non-VERIFIED_ADAPTER operation; an auditor outside the delivery team finds zero unrecorded manual work; EIH/VD falls at each tenant, with tenant 3 at or below 50% of tenant 1 (hypothesis, D4) | "The collection path was automatically constructed for three firms, with a published labor ledger including failed attempts." If workflow authoring dominates engineering minutes (D5 revisit trigger), say only "collection path reproduced" | "Autonomous"; claims about review packages |
| M3-lite sandbox (P4) | PA-002 run as written in sandbox; PA-003, PA-004, PA-006, PA-008, PA-010 and PA-011 pass in sandbox | "The preparation workflow passed its acceptance scenarios in sandbox" | Any production or customer result |
| Shadow results (P5) | Verifier-attested ready-for-review packages on at least 30 client-periods on tenant 1 across a full close; correct-package rate with exclusions in the denominator; accountant minutes against the month-0 baseline; PA-P12 first read | "In shadow at one firm, Plumb prepared N verifier-attested ready-for-review packages; X% were correct over all eligible client-periods; accountant minutes changed by Y against the firm's own baseline" | "Fewer duplicate requests"; "one request per missing item"; generalizing from one firm; any figure without its denominator |
| Draft tier (P6) | Production gateway passes the draft gates; a Draft canary for at least one close | "Plumb drafts consolidated requests in your mailbox; your staff send them" | "Sends for you"; duplicate-reduction outcomes |
| Send canary (P6 or later; earliest close around July 2027, about weeks 39-41, because the D6 ladder needs at least two Draft closes) | Canary report with denominators and effect receipts; zero duplicate, stale or wrong-client requests reached real clients | Add "one owner and one request per missing item" to the headline; report duplicate and stale requests per client-period | Claims beyond the canary's scope |
| M5 (starts in P6; completes P6 or later) | PA-027 passes on tenants 2-4 with falling EIH/VD and stable quality; PA-P12 attested | "Replicated on the next three firms with falling engineering hours." "Autonomously implemented" only for a path with PA-027-level evidence, the ledger shown, and (if ratified) the PA-P13 HIGH-severity gate | "Fully autonomous", "zero human", "AI employee": never, at any stage |

### 6.6 Message testing

D8 sets the test:

- Run landing pages and first calls across at least 200 ICP firm contacts.
- Compare verification-led framing ("Close-ready, with receipts") with outcome-led framing (for example "stop chasing, close faster"; outcome claims must still respect the claim ladder).
- If outcome-led framing gets more than 2x the qualified-meeting rate of verification-led framing among mixed-stack firms, lead with the outcome and keep verification and the ledger as proof points.
- The never-claim checklist is not relaxed under any result.

Proposed timing: start in P1 alongside outreach, read out with the first 25 qualified conversations, and report in the day-180 packet.

---

## 7. Competitive framing

Responses marked (D8) are the decision record's framing. Unmarked responses are proposed and need ratification. "When to walk away" applies the D1 qualify-out and PL-013: when a native or cheaper tool is enough, Plumb says so. Configuring that tool for the firm is a valid outcome that bills at the same rate (D7).

| Competitor class | Examples | Their pitch | Our response | When to walk away |
|---|---|---|---|---|
| Practice-management suites | Karbon, Financial Cents, TaxDome, Uku, Liscio, Canopy | Workflow, client portal and automated reminders in one place; now AI coworkers and agents (Karbon Kai, TaxDome Atlas) and MCP servers | "Keep your PM tool; Plumb makes your whole stack work together and proves it." (D8) Integrate through the Karbon and Uku MCP servers, and configure native reminders when they are enough | The firm's evidence already lives inside the suite plus one ledger, and native reminders work. Offer to configure and verify them, or walk away |
| Per-client close tools | Double, Xenett, Financial Cents close add-on | A close workspace across the whole book, per client, with AI review of coding and flux (Double claims 4,000+ firms, vendor-reported) | "Excellent inside the ledgers they connect to. Plumb assembles provenance-backed evidence from mail, drives and more than one ledger, keeps unknown separate from confirmed absence, and can sit alongside your close tool" | A firm on Double with a single ledger whose evidence already lives in Double (D1 item 4) |
| Ledger platforms | Xero (JAX, Partner Hub, Document Requests, XeroForce); Intuit (QBO agents, Accountant Suite) | Native agents and document requests matched to transactions, bundled or free | "Excellent inside one ledger; Plumb is for firms whose evidence spans ledgers, inboxes and drives." (D8) | A Xero-only firm should use Xero. A QBO-only firm whose Accountant Suite workflow works should use it |
| AI-native ledgers and engines | Digits, Puzzle, Truewind, Botkeeper, Booke, Docyt | Move to an autonomous ledger, or automate categorization and reconciliation | "Plumb is not a ledger and does not post. It works over the systems you already have, and capture tools are sources it connects" | The firm is migrating clients to a new ledger, or wants categorization or posting automation, which is out of scope for 180 days (D3) |
| Upmarket agents and close platforms | Basis, FloQast, Numeric | End-to-end agents; 20-50% efficiencies (Basis, vendor-reported); enterprise close | "Built and priced for 10-40-staff firms, implemented on your stack, with the labor shown" | Top-100 and 100+-staff firms (D1 item 2) |
| PBC and document-collection point tools | Content Snare, SmartVault SmartRequestAI, Suralink, AuditDashboard | No-login request lists, unlimited reminders, AI request builders | "Chasing is the easy part. Plumb knows what is already held for each client, period and obligation, with its source, before anyone asks" | The firm only wants reminders: recommend the point tool or native reminders. Tax-season intake is out of scope (IRC 7216) |
| Substitutes for the firm or its labor | Pilot, Zeni, offshore staffing, Current (formerly Crete) | Replace the firm, use cheaper labor, or buy the firm and implement centrally | "Plumb strengthens your firm. The labor ledger and cost per package let you compare Plumb with offshore or new hires like for like" | A roll-up that builds in-house; a firm whose plan is to offshore the whole close unchanged |
| DIY builders | Zapier, n8n, Make, Copilot Studio, XeroForce's builder | "Describe it in plain English and we build it" | "They make you the systems integrator; we implement and keep it running." (D8) OpenAI's Agent Builder shutdown on November 30, 2026 is the churn example | A firm with an in-house operations engineer who wants to build and maintain it themselves |
| FDEs, agencies and MSPs | Forward-deployed engineering teams, boutique agencies, MSPs | "We build it for you" | "Customer-owned specs, tests and adapters, an itemized labor ledger, and an exit path." (D8) Gartner predicts 70% of enterprises will abandon agentic AI built through vendor FDE by 2028 (secondary coverage) | A buyer who wants a bespoke project billed by the hour, posting, or on-prem. MSPs may be a later channel ([section 10.3](#103-managed-service-providers)) |
| Agentic implementation startups | superglue, Membrane, Rocketlane Nitro | Agents doing implementation for vendors, VARs and services teams | Rarely met in a firm deal. Keep the category distinct ("verified implementation", not "agentic implementation platform") | Not applicable |

**Win/loss instrumentation (proposed).** Record, for every qualified prospect that declines, the competitor class chosen and the reason, alongside the PL-013 comparison Plumb presented. R5 fires if at least 3 of 5 qualified prospects choose native tools after a PL-013 comparison, or if 50% or more of qualified mixed-stack prospects pick an incumbent head-to-head ([risks and assumptions](07-risks-and-assumptions.md)).

---

## 8. Messaging guardrails

### 8.1 Never-claim checklist (D8)

A formal gate for sales, marketing and investor materials. The founder owns it. It is not relaxed under any message-test result.

| # | Never claim | Say instead | Basis |
|---|---|---|---|
| 1 | That local tests validate models, business outcomes, tenant security, cloud isolation or integrations. Never quote the spec's stale "56 tests" figure (header table and Appendix C) | "More than 800 local contract and failure tests pass" (current counts in [VALIDATION_REPORT.md](../VALIDATION_REPORT.md)), presented only as local test results of the reference package | spec §28 L450; spec header table and Appendix C |
| 2 | Cross-industry autonomy from the three synthetic scenarios | "The three synthetic scenarios show representational reuse, not verified cross-industry autonomy" | spec §25 L398 |
| 3 | 90 days as anything but a planning hypothesis | "Our planning hypothesis is a 90-day supervised reference deployment, contingent on access and staffing." The 90-day pilot clock is a contract window that starts at the first attested collection path, not a delivery promise | spec §26 L418 |
| 4 | Product-video results as evidence | Show only measured results with their denominators | spec §29 L492 |
| 5 | An "autonomous close", or any posting | "A review package ready for your accountant." A package is "ready for review" until sign-off | spec §15 L248; Appendix B L652 |
| 6 | "Fully autonomous", "zero human", "no humans needed" or "AI employee". No autonomy claim if any hidden human implementation occurred | "Supervised deployment, with every human hour shown." Label deployments "supervised" until that path has PA-027-level evidence | PL-003; PA-027 |
| 7 | "Automatically constructed" before M1R | "Agent-configured certified connectors and agent-built collection" | PL-063; D4 |
| 8 | Logo walls. The synthetic registry's PRODUCTION_VERIFIED entries are synthetic and are never cited | "Supported environments v1": each operation at its maturity level (DISCOVERED, DOCUMENTED, SANDBOX_TESTED or PRODUCTION_VERIFIED) with probe evidence | PL-007, PL-008 |
| 9 | Any hours-saved or ROI figure without a baseline and a denominator, or any causal claim from historical replay | "Accountant minutes per client-period against your own month-0 baseline, over N eligible client-periods." The historical duplicate-chase baseline is labeled historical and non-causal | spec §7 L136 |
| 10 | Exact unlearning | "Affected derived data is quarantined or retired, with a deletion certificate" | spec §20 L318 |
| 11 | That a message was not sent after the provider accepted it | "The provider accepted it before the revocation landed; here is the receipt and the remediation" | PA-014 |
| 12 | Anything beyond the released tier, including a "fewer duplicate requests" outcome before Send-canary evidence | Claims from the claim ladder ([section 6.5](#65-claim-ladder-what-we-may-say-when)) for the current tier | D4 release tiers |

### 8.2 Claims buyers distrust

From the market-implementation research. Buyers have absorbed the failure and trust signals in [section 4.3](#43-trust-and-failure-signals-buyers-have-absorbed).

| Distrusted claim | Why | Credible alternative |
|---|---|---|
| "95% of AI fails, but not ours" | The MIT NANDA figure is contested and measures rapid revenue acceleration, not pilot success [M73] | Do not cite it. Show Plumb's own denominators, failures included |
| "Deploy in minutes" | Time to learn and implement is the top barrier small firms cite (41%) [M60]; the calendar floors in D5 (backfill, a full shadow close) rule it out | "Time to first verified event", split into Plumb-controlled and dependency time |
| "No humans needed" / "fully autonomous" | Builder.ai [M81]; trust drop [M80]; FTC enforcement [M82] | The labor ledger across five categories |
| "AI employee" / "AI teammate" | The same signals; Ema and Lindy use this framing | "Verified implementation" |
| Hours-saved figures with no denominator | Only 20% of respondents, mostly at small accounting and bookkeeping firms, report clear measurable ROI (vendor-run survey) [M60] | Measured review minutes against the firm's own baseline, with the eligible population stated |
| ROI without a baseline | As above; spec §7 L136 | Value as a range with assumptions, tested prospectively (PL-012) |
| "We build integrations automatically" | Table stakes (Nango, Membrane, superglue, Make, Zapier, n8n) | Evidence coverage, verification receipts, cost per verified deployment including failed attempts |
| Integration logo walls | PL-007: a logo is not an operation capability | Operations at maturity level |

### 8.3 Vocabulary (proposed)

| Use | Instead of | Why |
|---|---|---|
| "Ready for review" | "Done", "closed", "complete" (before sign-off) | Appendix B L652 |
| "Supervised deployment, labor shown" | "Autonomous deployment" | PL-003; D8 item 6 |
| "Verified" | "Live", "working" | Only with an independent verifier attestation (PL-042) |
| "Agent-configured certified connectors and agent-built collection" (until M1R) | "Generated integrations", "automatically constructed" | D4 claim rule |
| "Evidence readiness", "close readiness" | "Autonomous close" | spec §15 L248 |
| "Prepare", "Draft", "Send" | "Autopilot", "hands-free" | Release tiers; claims match the tier |
| "Unknown" vs "confirmed absent" | "Missing" for both | PL-010 |
| "Supported environments v1" | "Integrates with 100+ apps" | PL-007, PL-008 |

### 8.4 Review procedure (proposed)

- Every external asset (website, deck, case study, investor update, sales email template) passes the never-claim checklist before use. The founder signs off.
- Every quantitative claim carries an evidence pointer: a verifier attestation, a labor-ledger export, or a results-view report showing the denominator and exclusions. Keep a simple claims register (claim, asset, evidence pointer, date, tier) so a claim can be withdrawn when its evidence changes.
- Partner names and quotes appear only with written consent (D9 reference and case-study rights). No logo walls.
- Before any external value claim, PA-P12 must have attested the value figure (roadmap). The first read is planned for P5.

---

## 9. Pricing and packaging hypothesis

All prices, minimums, fees and thresholds in this section are hypotheses from D7, to be tested. The spec sets no price.

### 9.1 Unit of value

**The active client-month**: a recurring in-scope client-period for which Plumb delivered a verifier-attested ready-for-review package (D7).

Why this unit:

- It puts PL-001 into practice: customers pay for verified operating interventions, not recommendations, attempts or build count.
- It mirrors how firms package their own services. Double's per-connected-client model reports 150% NDR (vendor-reported) [M7].
- It rewards PL-013 behavior. A native-setting outcome bills at the same rate, so Plumb is never paid more for building more.
- Gartner expects buyers to move toward paying for workflow results (secondary coverage) [M77].

### 9.2 Tiers and what each includes

Pricing tiers and release tiers share the word "Prepare". This table maps them.

| Pricing tier (D7) | Price per active client-month | Release tiers covered | Includes | Available from |
|---|---|---|---|---|
| Prepare | $15 | Prepare (preparation-only: SHADOW for at least one full close, then CANARY on a subset of client-periods whose accountants use the prepared packages in their real review, then ACTIVE; no EXTERNAL_COMMUNICATION in any state) and Draft (mailbox drafts staff send) | Close-readiness ledger; ready-for-review package per client-period; later, consolidated requests as mailbox drafts | Annual billing starts at conversion: a partner converts after one full close in ACTIVE at or above the correct-package threshold (founder decision 17 in the [decision record](02-strategy-decisions.md), to ratify). The day-180 packet records tenant 1's evidence to date; tenant 1's conversion is expected in P6 (see the [roadmap](04-roadmap.md)). Drafts arrive no earlier than P6 |
| Prepare + Chase | $25 | Send (policy-approved sending, canary first) | Everything in Prepare, plus policy-approved consolidated sending with cross-staff de-duplication | Only once Send ships, after Send-canary evidence. The earliest Send canary close is around July 2027 (about weeks 39-41) |

Never included, at any price, in the first 180 days: posting or any FINANCIAL_COMMITMENT, tax-return data, training on firm data (no training runs in the first 180 days; afterwards TRAIN stays off by default and opt-in per source), screen capture, and second domains (D3).

### 9.3 Contract terms

- Annual contract.
- Firm minimum of $500 a month. At $15 that equals about 33 active client-months, so it rarely binds for a firm with at least 50 recurring clients. It does apply while customer-side dependencies are open.
- No per-seat price. Per-seat pricing fights an average tech budget of about $21,000 a year [M58] and positions Plumb as one more app.
- No implementation fee for supported environments. Plumb absorbs its own engineering interventions and never bills by the hour, so that labor stays a measured cost rather than revenue (ADR-010 measures implementation autonomy separately). Hourly implementation would reward hidden labor.
- No price discount in exchange for training rights.

### 9.4 Billing rules tied to PL-001 outcomes

| Outcome (PL-001 framing) | Billing treatment (D7) |
|---|---|
| Verified operating intervention: an attested ready-for-review package for the client-month | Billed |
| Package the accountant rejects as materially wrong | Credited |
| Client-month in which a Plumb-caused DEGRADED collector covered more than 20% of the period | Credited |
| Actionable external dependency on the customer side (for example, a missing grant or an unanswered domain question) | Not billed while open; the firm minimum still applies. A client blocked for 2 cycles drops off the billable roster until resolved |
| Actionable external dependency on the Plumb side, or a vendor outage | Never billed. Shown in the results view with what was attempted and why it stopped |
| Terminal failure with explanation | Never billed. Shown in the results view |
| Native-setting outcome (PL-013), for example configuring the firm's Xero or Financial Cents reminders | Billed at the same rate as a built outcome |

**What exists today (package implements):** none of this. There is no metering, billing, verifier service, effort-capture API or results view. The package provides seeds: the VerificationAttestation contract and the ECONOMIC_RESULT verification level; the OpenAPI proposal's OutcomeObservation with `realized_value`, `review_minutes` and a nullable `human_effort_category`; and the SQL `outcome_observations` and `human_effort` tables. Billing therefore depends on the verifier, the effort ledger and the results view in the [backlog](05-backlog.md).

### 9.5 Price guardrail and measured value

**Guardrail (D7):** price at no more than one-third of measured value per client-month, taken from the results view. If measured value does not support $15, lower the price or exit the segment.

| List point | Measured value per client-month needed to stay within the guardrail |
|---|---|
| $15 | $45 or more |
| $25 | $75 or more |
| $35 | $105 or more |

Measured value under about $45 per client-month fires a D7 revisit trigger ([section 9.11](#911-revisit-triggers)).

**How measured value is computed (proposed, to ratify with the domain expert).** The definition follows spec §7 L136, which separates theoretical labor capacity, usable capacity and realized cash or contribution margin:

- **Inputs:** accountant and bookkeeper minutes per client-period from the month-0 time study (baseline) and from review-surface timing (measured), over the same eligible client-periods, measured prospectively by staged rollout or comparable cohorts (PL-012). The firm supplies its loaded cost per hour.
- **Value for the guardrail:** usable capacity released (baseline minus measured minutes, including the firm's added review minutes, valued at the firm's loaded rate), plus documented avoided outsourcing spend where the firm has it. Theoretical capacity is reported but not used for price.
- **Never used:** causal claims from the historical duplicate-chase baseline, or industry hours-per-client figures (no reputable source exists).
- **Attestation:** PA-P12 (economic-result attestation) attests the figure before it is used externally.

### 9.6 Per-firm arithmetic

Arithmetic at D7 list prices. These are not forecasts.

| Active client-months per month | Prepare ($15), per year | Prepare + Chase ($25), per year |
|---|---|---|
| 20 (the $500 minimum binds for Prepare) | $6,000 (the minimum; 20 x $15 is only $300 a month) | $6,000 (20 x $25 = $500 a month) |
| 50 (ICP floor) | $9,000 | $15,000 |
| 100 | $18,000 | $30,000 |
| 150 | $27,000 | $45,000 |

**The budget tension.** The average firm's total tech spend is about $21,000 a year (Intuit survey, vendor-run; the notes do not break it down by firm size) [M58]. A 100-client firm on Prepare would pay about 86% of that average, and on Prepare + Chase more than all of it. So the purchase cannot come out of the software line. It has to be justified against labor: hiring (77% had hiring struggles [M58]), outsourcing (80% outsource at least one service [M58]) and reviewer capacity. This is why the guardrail, the month-0 baseline and the labor ledger matter commercially, not only for honesty. It is also a reason to watch R5's cost and conversion triggers closely.

### 9.7 Pilot terms

From D7:

- A paid design-partner pilot of $1,500-$3,000 by firm size, invoiced at signature, so willingness to pay is tested from day one.
- Credited to year one. Refundable only if Plumb misses the M0-agreed gate for Plumb-side reasons.
- The 90-day pilot clock starts at the first attested collection path, because packages cannot exist before then.
- Partners convert to annual at $15 Prepare with a 24-month price lock, once the workflow has been ACTIVE through one full close at or above the correct-package threshold.
- Exit is pre-agreed whether or not the gate is met.

**Proposed size bands for the pilot fee** (within D7's range; to ratify):

| Firm size | Pilot fee |
|---|---|
| 10-19 staff | $1,500 |
| 20-29 staff | $2,250 |
| 30-40 staff | $3,000 |

**Fallback (D7, D9):** the free-pilot trigger in [section 9.11](#911-revisit-triggers). Qualification is never lowered instead.

### 9.8 Price test design

D7: test three list points ($15, $25, $35) and a per-accepted-package alternative unit, with tenants 4-5 and new prospects. The phased plan starts the test with new prospects in P5. Design details below are proposed.

| Element | Design |
|---|---|
| Population | Tenants 4 and 5 and new ICP prospects. Tenants 1-3 are excluded: they convert at $15 with the 24-month lock |
| Arms | A: $15, B: $25, C: $35 per active client-month (Prepare scope). D: the same scope priced per accepted package, where a package counts only when the accountant explicitly accepted it without material correction and with zero wrong-client attribution (D10 definition) |
| Assignment | Rotate the quoted arm in sequence across qualified prospects, stratified by firm size band, so each arm sees a similar mix |
| Readouts | LOI and close rate per arm; realized price per active client-month; time to decision; coded objections; stated preference between per-client-month and per-package units |
| Sample | Small, likely tens of quotes in the first half of 2027. Results are directional. No statistical significance is claimed |
| Guardrails | Once a firm's measured value exists, no quote above one-third of it. No discount for training rights. The never-claim checklist applies to every price conversation (no unsupported ROI) |
| Decisions | Apply the D7 revisit triggers ([section 9.11](#911-revisit-triggers)) and report in the day-180 packet |

### 9.9 Benchmarks

Prices as found in the research notes, with reliability flags. Units differ, so compare with care.

| Category | Examples | Price signal | Unit | Reliability | Source |
|---|---|---|---|---|---|
| Per-client close tools | Double | Core $10, Plus $25, Scale $50; a tier with a $200/mo annual commitment | Per connected client per month | Tier prices third-party; model and $200 commitment from vendor page | [M7] |
| | Xenett | About $7.5 (AI Review), about $10 (Workflow), $15 (Accruals + AI add-on) | Per client per month | Vendor pages | [M8] |
| | Financial Cents Month-End Close add-on | $5 | Per client per month, annual | Vendor page | [M2] |
| Practice-management seats | Financial Cents, Karbon, Uku, Liscio | $19-$99 | Per user per month | Vendor pages | [M1], [M2], [M4], [M5] |
| | TaxDome | $800-$1,200 | Per user per year | Third-party (vendor page 403) | [M3] |
| | Canopy | $24-$40 per module | Per user per month | Third-party | [M6] |
| Ledger bundles | Intuit Accountant Suite | Entry tiers free during the introductory period | Per firm | US pricing from a secondary source | [M9] |
| | Hubdoc | Free with Xero Business plans | Per firm | Third-party listing | [M10] |
| | Xero JAX, XeroForce, Partner Hub | Not disclosed | Not applicable | Not applicable | [M10] |
| Document-collection point tools | Content Snare | $35-$215+ annual; $42-$258+ monthly | Per account per month | Vendor page | [M20] |
| AI bookkeeping engines and capture | Booke AI; Docyt; Botkeeper; Dext | $129/business/mo; from $299/mo; about $149/license/mo; from about $25.21/mo | Mixed | Third-party | [M14], [M15] |
| Outsourced bookkeeping | Offshore staff; outsourced bookkeeping | $8-$45/hr; $300-$2,500/mo | Per hour; per end client per month | Vendor blogs, unverified | [M26] |
| End-client substitutes | Zeni; Puzzle; Pilot | From $549 (Starter) or $799 (Growth) a month, less if billed annually; $30-$360/mo software plus service from $171/mo; about $599/mo | Per end client per month | Zeni and Puzzle vendor pages; Pilot unverified | [M23], [M12], [M22] |
| DIY builders | Zapier; n8n; Make; Lindy | $19.99-$69/mo; EUR 20-667/mo; $9-$29/mo; from $29.99/mo | Per account per month | Zapier, n8n and Lindy vendor pages; Make third-party | [M27], [M28], [M29], [M30] |
| | Microsoft Copilot Studio | $200 per 25,000 credits/mo; Copilot Business $21/user/mo | Credits; per user | Third-party | [M33] |
| Agencies | Boutique SMB AI agencies | $4,500-$25,000 for a first system | Per project | Vendor-written guide, low reliability | [M40] |
| Enterprise iPaaS | Workato | About $10k-$130k/yr | Per year | Third-party estimates | [M35] |
| Enterprise close | FloQast | About $30k-$80k/yr | Per year | Third-party estimates | [M17] |
| FDE consulting | OpenAI | $10M minimum | Per engagement | Reported | [M36] |
| Firm budget context | Average firm tech spend | About $21,000/yr | Per firm per year | Vendor-run survey | [M58] |

**Where Plumb sits.** Prepare at $15 sits inside the per-client close-tool range ($5-$50), above the Financial Cents add-on and Xenett's plans (about $7.5-$10), and level with Xenett's $15 accruals-and-AI add-on. Prepare + Chase at $25 matches Double's Plus tier as reported by third-party listings. Both sit far below outsourced bookkeeping per end client, which is a broader service. Against agencies, a 50-client firm on Prepare would pay $9,000 a year at the D7 list hypothesis, with implementation, maintenance and verification meant to be included and no project fee. The market-implementation research suggests positioning between DIY tools and human services, ideally per verified outcome. D7 does that.

### 9.10 What we will not do

- Per-seat pricing.
- Hourly or project implementation fees for supported environments.
- Discounts in exchange for training rights.
- Charging more for building more: native-setting outcomes bill at the same rate.
- Billing failures, Plumb-side blocks or vendor outages.
- ROI arithmetic in sales material without a baseline and a denominator.

### 9.11 Revisit triggers

From D7, read with the R5 triggers:

- Fewer than 2 of the first 4 partners convert to annual at $15 or more: re-examine the ICP (capacity-constrained firms, roll-ups) before cutting price.
- Pilot time studies show measured value under about $45 per client-month: cap Chase at $15 or fold it into Prepare.
- Fully loaded cost per active client-month at tenant 4 exceeds 2x price with no downward trend: re-price (per package, or firm tiers) or move to the roll-up/MSP channel.
- Firms strongly prefer flat fees: move to per-client tiers with outcome credits.
- Fewer than 2 paid pilot LOIs after about 30 qualified conversations: offer a free pilot with a pre-committed conversion price and a measurable gate.

---

## 10. Channels

### 10.1 Direct to firms first

- **Who sells.** The founder owns design-partner sales, because sales is on the critical path (D12). The first sales hire waits until 2 paid conversions.
- **Funnel hypothesis:** at least 8 qualified ICP conversations by the end of P0 (P0 exit evidence); tenant 1 signed by about week 4; at least 25 qualified conversations and tenants 2-4 LOIs by week 8 (D9). Tenant baseline studies finish before mid-January, ahead of tax season (D5).
- **Lead sources (proposed):** an outbound list built from the ICP filters, referrals from signed partners, and the message test across at least 200 ICP contacts ([section 6.6](#66-message-testing)). The research notes do not evaluate specific lead sources.
- **Why direct.** The first five firms are evidentiary tenants with designed stack variation. Plumb has to choose them, not inherit them from a channel.

### 10.2 Optional roll-up slot

- **Signal.** Consolidation creates centralized buyers. There were about 180 PE deals in accounting in 2025 and 57 in the first two months of 2026, three times a year earlier. The CPA Trendlines tracker counts 525 events, about $49B in enterprise value and about 96,000 staff through May 2026 (partly paywalled; the 2025 count is from snippets) [M72]. Roll-ups need standardized close across heterogeneous acquired stacks, which is Plumb's "next three customers" test.
- **Counter-signal.** Well-funded roll-ups build in-house: Current (formerly Crete), with Thrive and OpenAI [M24].
- **Decision (D1, D9).** One optional slot, as tenant 5 or a sixth slot, off the critical path. Roll-ups are not the primary buyer because of procurement drag and in-house builds. Promote the channel only if R5 fires.

### 10.3 Managed service providers

- **Signal.** 91% of MSPs offer or use AI solutions, and 36% offer custom AI solutions (Informa MSP 501, 600+ MSPs) [M39]. MSPs are the SMB's existing implementer but lack engineering depth for data and ML work.
- **Fit.** Later. MSPs are a plausible reseller of Plumb as their implementation engine. If R1 fires (replication does not get cheaper), one pivot is to sell the factory as tooling for human implementers (MSPs, VARs, roll-ups) and drop the autonomous-implementation claim (D11).
- **Proposed.** No MSP channel work in the first 180 days beyond exploratory conversations. Revisit in the day-180 packet, or earlier if R1 or R5 fires.

### 10.4 Marketplaces and MCP surfaces

| Surface | What the research found | How Plumb uses it (proposed) |
|---|---|---|
| Xero App Store | Accountant tools such as Content Snare are listed there [M20] | A listing after supported environments v1 is published (P2 at the earliest), stating operations at maturity level. Aim it at mixed-stack firms, not Xero-only firms (qualify-out 4) |
| QBO APIs and the Intuit ecosystem | Intuit ships agents and Accountant Suite natively [M9] | Integration surface for certified operations; no marketplace claim until operations are probed |
| Karbon MCP server | Public MCP server launched with Kai [M1] | Integration surface for firms on Karbon, read-only in v1 (D1). Configure Karbon's native reminders when they are enough (PL-013) |
| Uku MCP | Lets Claude or ChatGPT operate Uku directly on Elite and Enterprise plans [M4] | Integration surface where cohort firms use Uku |
| Nango, Airbyte and other substrates | Agent-ready connector catalogs [M49], [M50] | Supply side, not distribution. Connectors pass contract tests before use (spec §3 L84) |

Rules for every surface:

- An MCP server is an interface, not proof of tool correctness or business authorization. Plumb enforces customer-specific scope and destination rules itself (spec §4 L98).
- A marketplace listing or a connector catalog is never presented as integration coverage. Coverage is stated per operation at its maturity level (PL-007, PL-008; never-claim item 8).

### 10.5 Channel sequencing

| Channel | Role | When (hypothesis) | Gate to expand |
|---|---|---|---|
| Direct, founder-led | Design partners, then early customers | P0 onward | 2 paid conversions before the first sales hire (D12) |
| Roll-up slot | Channel probe | Tenant 5 or a sixth slot, off the critical path | R5 fires |
| Marketplaces and MCP surfaces | Integration first; distribution later | Listings after supported environments v1 (P2 at the earliest) | Operations at SANDBOX_TESTED or above for the listed stack |
| MSPs | Reseller of the implementation engine | Not before the day-180 packet | R1 or R5 fires, or M5 shows falling EIH/VD |

---

## 11. Sources

Numbering is local to this document. Access and recency notes come from the research notes, which were compiled by October 4, 2026 (the implementation note checked its facts against search results dated before that day).

**A. Accounting-market players**

1. [M1] Karbon. Pricing: https://karbonhq.com/pricing/ . Kai launch (June 3, 2026, early access; MCP server): https://karbonhq.com/resources/karbon-launches-kai/ . Kai pricing not disclosed.
2. [M2] Financial Cents pricing, including the Month-End Close add-on: https://financial-cents.com/pricing/ .
3. [M3] TaxDome. Pricing (third-party; vendor pricing page returned 403): https://assembly.com/blog/taxdome-pricing . Summer 2026 update (Atlas beta; GA planned end of Q3 2026): https://taxdome.com/blog/webinar-recap-and-qa-summer-update-2026 . TaxDome AI launch: https://accountingtoday.com/news/taxdome-launches-taxdome-ai-for-document-management-and-organization .
4. [M4] Uku pricing and Uku MCP plans: https://getuku.com/pricing/ .
5. [M5] Liscio. Pricing: https://liscio.me/pricing . Blog (source of the secondary 9.3 hours a week client-communication figure, CPA Practice Advisor 2024): https://www.liscio.me/blog-posts/how-accounting-firms-can-automate-client-document-collection .
6. [M6] Canopy pricing (third-party, not verified on vendor site): https://capterra.com/p/150647/Canopy-Tax/ ; https://toolradar.com/tools/canopy/pricing .
7. [M7] Double (formerly Keeper). Vendor pricing page (confirms per-connected-client model, unlimited users, $200/mo annual-commitment tier, $10/mo email add-ons): https://doublehq.com/pricing . Series A (December 11, 2025; 4,000+ firms; 150% NDR, vendor-reported): https://www.cpapracticeadvisor.com/2025/12/13/double-raises-6-5-million-series-a/174948/ . Rebrand (October 24, 2025): https://www.cpapracticeadvisor.com/2025/10/24/keeper-has-rebranded-to-double/171596/ . Tier prices $10/$25/$50 (third-party): https://www.capterra.com/p/10012825/Keeper/ ; https://yespress.io/products/keeper ; https://doublehq.com/?p=1296 .
8. [M8] Xenett pricing: https://help.xenett.com/en/articles/13349026-xenett-pricing-overview ; https://www.xenett.com/pricing .
9. [M9] Intuit. QBO agents (July 1, 2025): https://investors.intuit.com/_assets/_08ee5483ec4c057568cc8774f3fd6aad/intuit/news/2025-07-01_Intuit_Introduces_Ground_Breaking_Virtual_Team_of__1258.pdf . Accountant Suite launch (October 28, 2025; no pricing in article): https://www.cpapracticeadvisor.com/?p=171765 . UK launch, free during introduction (February 11, 2026): https://itbrief.co.uk/story/intuit-debuts-ai-native-accountant-suite-for-uk-firms . US "no charge during introductory period" (secondary source): https://my-cpe.com/insights/news-and-insights/technology/intuit-rolls-out-smartest-ai-accountant-suite-for-next-gen-accounting . Embedded agents and claims (paid up to 5 days faster, up to 12 hours a month saved; vendor-reported): https://tearsheet.co/artificial-intelligence/how-intuit-is-designing-embedded-ai-agents-in-quickbooks-to-serve-smbs/ ; https://cmswire.com/customer-experience/intuit-gets-conversational-ai-agents-tackle-crm-finance-and-cx-tasks .
10. [M10] Xero (JAX, Partner Hub, Document Requests, XeroForce; announced at Xerocon London July 9, 2026; reported August 20, 2026): https://itbrief.co.uk/story/xero-expands-ai-tools-for-accountants-small-firms ; https://www.cpapracticeadvisor.com/?p=186427 . Hubdoc (bundled free): https://www.capterra.com/p/165724/Hubdoc/ . Pricing for JAX, XeroForce and Partner Hub not disclosed.
11. [M11] Digits. Autonomous General Ledger (March 10, 2025): https://www.globenewswire.com/news-release/2025/03/10/3039814/0/en/AI-Startup-Digits-Takes-on-QuickBooks-with-the-World-s-First-Autonomous-General-Ledger-for-Accounting-Xero-Co-founder-Craig-Walker-Joins-Digits.html . Accounting Agents (June 23, 2025): https://www.cpapracticeadvisor.com/2025/06/23/digits-rolls-out-ai-agents-for-accounting-workflows/163521/ .
12. [M12] Puzzle pricing and close management: https://puzzle.io/pricing ; https://puzzle.io/blog/accounting-firm-month-end-close-software .
13. [M13] Truewind Series A (January 8, 2025): https://www.cpapracticeadvisor.com/2025/01/08/truewind-accounting-ai-platform-raises-13-million-in-series-a-funding/154157/ .
14. [M14] Botkeeper, Booke.ai, Docyt pricing (third-party): https://resources.rework.com/tools/ai-agents/best-ai-agents-for-bookkeeping-2026 ; https://costbench.com/software/tax-software/booke-ai/ .
15. [M15] Dext and Hubdoc pricing (third-party, 2026): https://datamolino.com/blog/pricing-and-features-autoentry-vs-hubdoc-vs-dext-vs-datamolino-in-2026 .
16. [M16] Basis. Series B (February 24, 2026; BusinessWire release returned 403, figures verified through CPA Practice Advisor): https://www.cpapracticeadvisor.com/2026/02/24/basis-raises-100-million-to-deploy-ai-agents-for-accounting-firms/178759/ ; https://siliconangle.com/2026/02/24/ai-accounting-startup-basis-secures-100m-1-15b-valuation-firms-adopt-agent-based-workflows/ ; https://www.builtinnyc.com/articles/basis-raises-100m-series-b-20260226 . Penetration and efficiency figures are vendor-reported.
17. [M17] FloQast. $200M ARR (January 21, 2026): https://itbrief.news/story/floqast-surpasses-200m-arr-seals-ey-ai-alliance . Pricing estimates (third-party, unverified): https://www.erpresearch.com/erp-add-ons/financial-close/floqast/pricing . CAS case study: https://www.floqast.com/stories/cas-practice-uses-floqast-ai-matching-to-scale-support .
18. [M18] Numeric Series B (November 20, 2025): https://numeric.io/blog/numeric-raises-51m-series-b ; https://www.cpapracticeadvisor.com/2025/11/20/ai-accounting-platform-numeric-raises-51m-series-b/173638/ .
19. [M19] Suralink and AuditDashboard: https://www.suralink.com/pricing ; third-party pricing (unverified): https://softwarefinder.com/accounting-software/suralink ; https://www.auditdashboard.com/pbc-requests .
20. [M20] Content Snare. Pricing: https://contentsnare.com/pricing/ . Xero App Store listing: https://apps.xero.com/us/app/content-snare .
21. [M21] SmartVault SmartRequestAI (announced July 22, 2025; time-saving claims vendor-reported; 2026 reminders per search results): https://www.cpapracticeadvisor.com/2025/07/22/smartvault-to-launch-smartrequestai-to-automate-document-collection-and-client-intake-process-for-tax-professionals/165337/ .
22. [M22] Pilot AI Accountant (February 4, 2026; claims vendor-reported; pricing not found, about $599/mo bookkeeping unverified): https://www.cpapracticeadvisor.com/2026/02/04/pilot-rolls-out-fully-autonomous-ai-accountant/177453/ ; https://pilot.com/blog/pilot-unveils-ai-accountant-a-major-leap-toward-artificial-general-intelligence-in-accounting .
23. [M23] Zeni pricing: https://www.zeni.ai/pricing .
24. [M24] Current (formerly Crete Professionals Alliance). $500M roll-up plan (Reuters, June 4, 2025, via syndication; original not accessed): https://kfgo.com/2025/06/04/thrive-backed-accounting-firm-crete-to-spend-500-million-in-ai-roll-up/ ; https://finance.yahoo.com/news/thrive-backed-accounting-firm-crete-130200467.html . Rebrand as Current (June 3, 2026; 31% tax-prep savings, vendor-reported): https://www.cpapracticeadvisor.com/2026/06/03/crete-professionals-alliance-rebrands-as-current/184461/ .
25. [M25] Bench shutdown (December 2024): https://www.geekwire.com/2024/vancouver-fintech-company-bench-accounting-announces-sudden-shutdown/ .
26. [M26] Offshore and outsourced bookkeeping rates (vendor blog, unverified): https://www.vjmglobal.com/feeds/blog/cost-outsourcing-accounting-services-us . Outsourcing shares come from [M58].

**B. AI-implementation players**

27. [M27] Zapier pricing (fetched October 2026; may vary by region or promotion): https://zapier.com/pricing ; https://www.capterra.com/p/10042120/Zapier-Agents/ .
28. [M28] n8n. Pricing: https://n8n.io/pricing/ . $2.5B round (October 9, 2025): https://www.bloomberg.com/news/articles/2025-10-09/ai-agent-startup-n8n-nets-2-5-billion-valuation-with-backing-from-nvidia . SAP investment at $5.2B (May 12, 2026): https://pulse2.com/n8n-valuation-doubles-to-5-2-billion-as-sap-makes-strategic-investment-and-embeds-platform-into-joule-studio/ ; https://dealroom.co/news/132833-n8ns-valuation-doubles-to-5-2b-with-sap-strategic-investment/ .
29. [M29] Make. Maia announcement: https://www.make.com/en/blog/maia-conversational-ai-coworker-for-ai-agents-and-automation . Pricing and launch dates (third-party): https://automationatlas.io/tools/make/ .
30. [M30] Lindy pricing: https://www.lindy.ai/pricing .
31. [M31] Gumloop Series B (March 12, 2026): https://gumloop.com/blog/series-b ; https://betakit.com/?p=401984 .
32. [M32] Relevance AI Series B (May 6, 2025): https://techcrunch.com/2025/05/06/relevance-ai-raises-24m-series-b-to-help-anyone-build-teams-of-ai-agents/ .
33. [M33] Microsoft Copilot Studio pricing (third-party blogs, 2026): https://www.getmacha.com/blog/copilot-studio-pricing-explained ; https://www.cloudzero.com/blog/copilot-studio-pricing/ .
34. [M34] OpenAI AgentKit and Agent Builder deprecation (announced June 3, 2026; shutdown November 30, 2026): https://openai.com/index/introducing-agentkit/ ; https://developers.openai.com/api/docs/deprecations ; https://www.spotdev.co.uk/blog/agent-builder-wind-down-what-to-do .
35. [M35] Workato Genies (August 19, 2025): https://www.businesswire.com/news/home/20250819262113/en ; https://www.workato.com/genie . Pricing estimates (third-party): https://composio.dev/content/workato-alternatives .
36. [M36] OpenAI consulting, reported $10M minimum (July 2025): https://the-decoder.com/openai-is-charging-at-least-10-million-per-client-for-its-enterprise-ai-consulting-services/ ; https://www.business-standard.com/companies/news/openai-custom-ai-consulting-service-10-million-grab-accenture-125070200681_1.html .
37. [M37] Distyl AI ($1.8B valuation, September 2025): https://siliconangle.com/2025/09/22/enterprise-ai-consultancy-distyl-ais-valuation-soars-1-8b-bumper-funding-round/ ; https://pulse2.com/distyl-ai-175-million-at-1-8-billion-valuation-raised-for-helping-businesses-become-ai-native .
38. [M38] Ema Series B (September 23, 2026): https://techcrunch.com/2026/09/23/ema-raises-77m-as-ai-starts-eating-into-enterprise-software-and-services/ .
39. [M39] Informa 2026 MSP 501 (published September 29, 2026): https://www.channelinsider.com/ai/msp-ai-revenue-growth-2026/ .
40. [M40] Boutique SMB AI agencies. Implement AI: https://en.wikipedia.org/wiki/Implement_AI . Agency pricing guide (vendor-written, low reliability): https://www.layer3labs.io/ai-consulting-for-small-business . Directory: https://aiimplementationcompanies.com/ .
41. [M41] FDE job postings up more than 800% (Financial Times via Fast Company, November 2025; FT original not accessed): https://fastcompany.co.za/work-life/2025-11-08-forward-deployed-engineers-a-new-role-in-the-evolving-ai-job-market .
42. [M42] superglue (claims vendor-reported; pricing page not retrieved; funding from an aggregator, unverified): https://superglue.ai/ ; https://superglue.ai/docs/getting-started/introduction.md ; https://pitchbook.com/profiles/company/761476-69 .
43. [M43] Membrane (launched November 18, 2025): https://tools.prnewswire.com/en-us/live/20813/release/20251118EN24222 ; https://getmembrane.com/articles/all/announcing-membrane-the-era-of-self-integrations .
44. [M44] Rocketlane Nitro (effectiveness figures vendor-reported; $60M raise seen only as a headline, unverified): https://www.rocketlane.com/lp/nitro-competitor ; https://inc42.com/?p=553099 .
45. [M45] Ardent AI and Definity: https://siliconangle.com/2025/09/25/ardent-ai-beats-odds-launch-worlds-first-agentic-engineer-data-pipeline-maintenance/ ; https://app.dealroom.co/news/feed/definity-raises-12m-series-a-for-agentic-data-engineering-platform .
46. [M46] Mimica: https://www.mimica.ai/about ; https://dealroom.co/companies/mimica-automation/ .
47. [M47] Workday to acquire Pipedream (November 19, 2025): https://newsroom.workday.com/2025-11-19-Workday-Signs-Definitive-Agreement-to-Acquire-Pipedream ; https://siliconangle.com/2025/11/19/workday-acquire-pipedream-extend-ai-agent-integrations-across-enterprise-apps/ .
48. [M48] Composio funding (2025): https://www.cxodigitalpulse.com/agentic-ai-startup-composio-secures-25-million-to-accelerate-workflow-automation-innovation/ .
49. [M49] Nango (Management MCP guide published September 4, 2026): https://nango.dev/ ; https://nango.dev/blog/how-to-build-ai-agent-integrations-using-the-nango-management-mcp .
50. [M50] Airbyte (Airbyte Agents, May 4, 2026; efficiency claims vendor-reported): https://airbyte.com/blog/airbyte-agents ; https://airbyte.com/connector-builder ; https://docs.airbyte.com/ai-agents/platform/context-store .
51. [M51] Temporal (Series E, September 14, 2026; Series D, February 2026): https://temporal.io/blog/temporal-raises-usd550m-series-e-at-usd12-55b-valuation-ai ; https://temporal.io/news/temporal-raises-550m-at-a-12-55b-valuation ; https://temporal.io/news/temporal-raises-300M-to-make-agentic-ai-real-for-companies .
52. [M52] Pulumi Neo and Automation API ("agents drive about 20% of operations" from a The New Stack article seen only through a search summary): https://info.pulumi.com/press-release/pulumi-neo ; https://siliconangle.com/2025/09/16/pulumi-debuts-first-ai-agents-take-cloud-platform-engineering/ ; https://thenewstack.io/pulumi-infrastructure-agent-era/ ; https://www.pulumi.com/docs/iac/concepts/automation-api/ .
53. [M53] Y Combinator Requests for Startups, Fall 2026: https://www.ycombinator.com/rfs .

**C. Market counts, surveys and signals**

54. [M54] US Census Bureau, Statistics of U.S. Businesses 2022 (NAICS 5412, 541211, 541213, 541219 by enterprise size; released April 10, 2025; employer firms only; parsed directly by the researcher): https://www2.census.gov/programs-surveys/susb/tables/2022/us_state_6digitnaics_2022.xlsx .
55. [M55] IBISWorld business counts (2026; search-snippet values, page not fetched): https://www.ibisworld.com/industry-statistics/number-of-businesses/payroll-bookkeeping-services-united-states/ .
56. [M56] ISED Canada, NAICS 5412 summary (2025): https://ised-isde.canada.ca/app/ixb/cis/summary-sommaire/5412 .
57. [M57] BLS Occupational Outlook Handbook, accountants and auditors (2025 data): https://www.bls.gov/ooh/business-and-financial/accountants-and-auditors.htm .
58. [M58] Intuit QuickBooks 2026 Accountant Technology Survey (725 US professionals, May 2026; vendor-run), via CPA Practice Advisor (July 2, 2026): https://www.cpapracticeadvisor.com/2026/07/02/the-2026-accountant-technology-survey-turning-data-revelations-into-a-firm-of-the-future/185807/ .
59. [M59] Financial Cents 2025 State of Accounting Workflow Automation (816 professionals; April 2025, covering 2024; vendor-run; rank only): https://financial-cents.com/?p=9086 ; coverage: https://www.cpapracticeadvisor.com/2025/04/16/third-annual-state-of-accounting-workflow-automation-report-released/159243/ .
60. [M60] Financial Cents State of AI in Accounting & Bookkeeping 2026 (n=486; July 15-August 7, 2026; vendor-run): https://financial-cents.com/?p=39931 .
61. [M61] Uku AI in Accounting 2026 (dozens of firms in 8 countries, mostly 1-10 employees; fielded May-June 2026; small, self-selected; directional): https://getuku.com/ai-in-accounting-report/ .
62. [M62] AICPA PCPS CPA Firm Top Issues Survey, via CPA Practice Advisor (June 23, 2026): https://www.cpapracticeadvisor.com/?p=185547 .
63. [M63] Ramp and CalCPA, Benchmarking the Modern CPA Firm 2026 (400+ California professionals): https://ramp.com/reports/benchmarking-the-modern-cpa-firm-2026-or-calcpa-and-ramp .
64. [M64] Goldman Sachs 10,000 Small Businesses AI survey (n=1,256; published March 17, 2026; Goldman pages returned 403; headline figures confirmed by CPA Practice Advisor and Fortune; barrier percentages from a search summary): https://www.goldmansachs.com/pressroom/press-releases/2026/small-businesses-embrace-ai-but-need-training-and-support-to-fully-harness-it ; https://fortune.com/2026/03/18/small-business-ai-slow-integration-across-operations/ .
65. [M65] US Census Bureau, AI use in businesses (BTOS; May 26, 2026; question revised November 2025, not comparable with earlier rates): https://census.gov/library/stories/2026/05/ai-use-businesses.html .
66. [M66] Thomson Reuters, 2026 AI in Professional Services (April 16, 2026): https://www.thomsonreuters.com/en-us/posts/innovation/the-real-ai-story-in-tax-and-audit-isnt-adoption-its-impact/ .
67. [M67] Wolters Kluwer 2025 Future Ready Accountant (October 8, 2025; search snippet only, page returned 403): https://www.wolterskluwer.com/en/news/wolters-kluwer-releases-its-2025-future-ready-accountant-report .
68. [M68] Accounting Seed, The State of AI in Accounting 2026 (n=128; December 2025-January 2026): https://www.accountingseed.com/resources/the-state-of-ai-in-accounting-2026 .
69. [M69] Ireland's Small Firms Association (n=404; August 10, 2026): https://www.ibec.ie/sfa/news-insights-and-events/news/2026/08/10/small-firms-association-sound-alarm-over-shallow-ai-adoption .
70. [M70] CFO Dive on month-end close delays (search snippet only; article not fetched): https://www.cfodive.com/news/cfo-push-faster-month-end-close-stalled-data-bottlenecks-ai/819283/ .
71. [M71] AICPA and CPA.com 2024 CAS Benchmark (December 2024; 2023 data): https://www.cpa.com/news/aicpa-and-cpacom-benchmark-survey-client-advisory-services-cas-practices-report-17-growth .
72. [M72] CPA Trendlines PE deal tracker (March and June 2026; partly paywalled; 2025 count from snippets): https://cpatrendlines.com/2026/03/01/pe-deal-tracker-for-feb-2026-57-deals-in-60-days/ .
73. [M73] MIT NANDA "The GenAI Divide", via Fortune (August 18, 2025; contested methodology; not for Plumb marketing): https://fortune.com/2025/08/18/mit-report-95-percent-generative-ai-pilots-at-companies-failing-cfo/ .
74. [M74] S&P Global Market Intelligence on abandoned AI initiatives (2025), via CIO Dive: https://www.ciodive.com/news/ai-project-fail-data-spglobal/742590/ .
75. [M75] Gartner, agentic AI projects canceled by end-2027 (June 25, 2025; from a search summary): https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027 .
76. [M76] Gartner, 70% abandonment of FDE-built agentic AI by 2028 (September 29-30, 2026; Gartner page returned 403; details via secondary coverage): https://www.gartner.com/en/newsroom/press-releases/2026-09-29-gartner-predicts-70-percent-of-enterprises-will-abandon-agentic-ai-built-by-vendor-forward-deployed-engineering-by-2028 ; https://techstrong.ai/articles/gartner-warns-70-of-vendor-built-ai-agent-projects-face-abandonment-by-2028/ .
77. [M77] Gartner, enterprises to abandon assistive AI for outcome-focused workflow by 2028 (April 2, 2026; page title and secondary coverage): https://www.gartner.com/en/newsroom/press-releases/2026-04-02-gartner-expects-most-enterprises-to-abandon-assistive-ai-for-outcome-focused-workflow-by-2028 .
78. [M78] Gartner, lack of AI-ready data (February 26, 2025; search summary): https://www.gartner.com/en/newsroom/press-releases/2025-02-26-lack-of-ai-ready-data-puts-ai-projects-at-risk .
79. [M79] BCG, the widening AI value gap (September-October 2025): https://www.bcg.com/publications/2025/are-you-generating-value-from-ai-the-widening-gap .
80. [M80] Capgemini Research Institute, AI agents and trust (date not stated on page; coverage places it around July 2025): https://www.capgemini.com/insights/research-library/ai-agents/ .
81. [M81] Builder.ai collapse (May-June 2025): https://www.techspot.com/news/108173-builderai-collapses-after-revelation-ai-since-2017-really-hundreds-engineers.html .
82. [M82] FTC Operation AI Comply, two years on (Holland & Knight, August 18, 2026): https://www.hklaw.com/en/insights/publications/2026/08/operation-ai-comply-2-years-later-continued-enforcement .
83. [M83] IRC Section 7216 and AI tools (secondary compliance commentary, not IRS guidance or legal advice; verify with counsel): https://my-cpe.com/blogs/ai-compliance-for-cpa-accounting-firms-irc-7216-aicpa-ftc .

**Repository sources:** [spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md) (§1 L49, L51; §3 L84; §4 L98; §7 L132, L136; §15 L248; §20 L318; §25 L398; §26 L404-418; §28 L450; §29 L492; Appendix A.6 L580; Appendix B L596, L598, L604, L650-654; the stale "56" test count at L15 and Appendix C L662); [requirements index](../spec/requirements_index.json); [acceptance catalog](../acceptance/production_acceptance_catalog.yaml); [capability registry](../plumb/registry/capability_registry.json) (synthetic; 25 records covering 23 step types); [OpenAPI proposal](../api/openapi.yaml) (`listOutcomes`, OutcomeObservation); [contracts](../plumb/contracts/) (VerificationAttestation, HumanEffortCategory, OpportunitySpec); [SQL design](../sql/001_initial_design.sql) (`outcome_observations`, `human_effort`); accounting [envelope](../fixtures/envelopes/accounting_evidence_preparation.json) and [plan](../fixtures/plans/accounting_evidence_preparation.json) fixtures (eu-west-1, EUR; the envelope expires 2027-03-31); [validation report](../VALIDATION_REPORT.md) (current local test counts); [README](../README.md).
