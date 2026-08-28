# Agent-Enabled Organization and Communication Bus

A shareable model for coordinating builders, customer-facing agents, independent assurance, specialist research, and temporary mission teams. Names are illustrative.

**Model updated:** 2026-08-24

## 1. Core organization with mission overlays

```mermaid
flowchart TB
    CEO["{CEO}<br/>Strategy and material company decisions"]
    CSO["{Strategy & Portfolio Lead}<br/>Sequencing, cross-team conflicts, and strategic evidence"]

    CEO -->|"approves strategy and material decisions"| CSO
    CSO -->|"decision briefs and proposals"| CEO

    subgraph BUILD["Build and Operations Organization"]
        direction LR
        DELIVERY["Product and Delivery<br/>Relay — Product<br/>Relay Forge — Engineering"]
        TRUST["Trust and Evidence<br/>Socrates — Quality Assurance<br/>Signal Loom — Performance Evaluation<br/>Forward-Deployed Agent"]
        DISCOVERY["Strategic Discovery<br/>Research agents<br/>Design contractors<br/>Domain experts"]

        TRUST -->|"independent evidence and gates"| DELIVERY
        DISCOVERY -->|"time-bounded recommendations"| DELIVERY
    end

    subgraph CUSTOMER_AGENTS["Customer-Facing Agent Organization"]
        direction LR
        PROFILE["Guidance and Profile<br/>Understand intent<br/>Collect approved context<br/>Route work"]
        DIRECTION["Direction and Discovery<br/>Synthesize evidence<br/>Present options<br/>Explain uncertainty"]
        PROGRESS["Application and Progress<br/>Draft and organize<br/>Prepare the customer<br/>Track progress"]

        PROFILE -->|"approved context"| DIRECTION
        DIRECTION -->|"approved direction and selected options"| PROGRESS
    end

    CUSTOMER["Customer<br/>Retains consequential decisions, review, and approval"]
    CUSTOMER <-->|"intent, evidence, corrections, and approval"| PROFILE
    CUSTOMER <-->|"review and action"| PROGRESS

    DELIVERY -->|"approved capabilities and operating rules"| PROFILE
    PROGRESS -->|"recurring friction and customer-impact signals"| TRUST
    TRUST -->|"independent risk and performance evidence"| CSO
    CSO -->|"coordinates portfolio without replacing owners"| DELIVERY

    MISSIONS["Mission overlay<br/>Features, investigations, experiments, audits, contractors, and temporary custody<br/>Driver + destination owner + writer + reviewer + start + end + handoff"]
    DELIVERY <-->|"staffs and integrates"| MISSIONS
    TRUST <-->|"observes and verifies"| MISSIONS
    DISCOVERY <-->|"provides bounded expertise"| MISSIONS

    PLATFORM["Cross-organization platform mission<br/>Temporary implementation lead<br/>Product and Engineering acceptance<br/>Independent assurance and measurement<br/>No automatic executive layer"]
    DELIVERY <-->|"implements and integrates"| PLATFORM
    TRUST <-->|"verifies risk, quality, and economics"| PLATFORM
    PLATFORM <-->|"operates as a bounded mission"| MISSIONS

    BUS["Communication Bus<br/>Directory + direct messages + durable records + decision boundaries"]
    DELIVERY <-->|"registered direct consultations"| BUS
    TRUST <-->|"findings and verification"| BUS
    DISCOVERY <-->|"advice and evidence"| BUS
    MISSIONS <-->|"requests and handoffs"| BUS
    BUS -->|"missing owner, conflict, expansion, sequencing, or strategy"| CSO
```

Functional lanes clarify durable accountability without creating extra management layers. Temporary teams are mission overlays and disappear from the active structure when their end condition is accepted.

A platform capability that spans organizations does not automatically require a third organization or executive. Place it in one execution lane, assign independent assurance and measurement, name its acceptance owners, and keep it temporary until evidence justifies durable ownership.

## 2. Communication-bus anatomy

```mermaid
flowchart LR
    TRIGGER["Collaboration trigger<br/>Overlap, dependency, contradiction, risk, or missing evidence"]

    subgraph BUS["Communication Bus"]
        direction LR
        DIRECTORY["1. Directory<br/>Owners, contacts, specialties, availability, and writer scope"]
        TRANSPORT["2. Transport<br/>Bounded direct messages across tasks"]
        RECORD["3. Durable record<br/>Request, evidence, confidence, decision, and handoff"]
        BOUNDARY["4. Decision boundary<br/>Who recommends, verifies, blocks, decides, and approves"]

        DIRECTORY --> TRANSPORT
        TRANSPORT --> RECORD
        RECORD --> BOUNDARY
    end

    TRIGGER --> DIRECTORY
    BOUNDARY --> EXECUTE["Execution or remediation<br/>One accountable owner and registered writer"]
    BOUNDARY --> VERIFY["Independent verification<br/>Predefined acceptance or release gate"]
    BOUNDARY --> ESCALATE["Exception route<br/>Missing owner, conflict, material expansion, sequencing, or strategy"]

    EXECUTE --> LEARN["Durable outcome<br/>Decision, evidence, unresolved risk, and downstream impact"]
    VERIFY --> LEARN
    ESCALATE --> LEARN
```

The bus is shared infrastructure—not a department, manager, or autonomous decision-maker. A coordinator handles exceptions; registered owners handle routine consultations directly.

## 3. Consultation and debugging flow

```mermaid
flowchart LR
    A["Agent encounters a dependency or problem"] --> B["Find the accountable owner and writer scope"]
    B --> C{"Owner, contact, and scope registered and clear?"}

    C -->|"Yes"| D["Send a bounded direct request across tasks"]
    C -->|"No"| E["Coordinator identifies owner or arbitrates scope"]

    D --> F{"Consequential, cross-owner, or release risk?"}
    E --> F
    F -->|"No"| G["Quick consultation<br/>Record the material conclusion"]
    F -->|"Yes"| H["Structured case<br/>Name driver, writer, reviewer, severity, and gate"]

    H --> I["Single registered writer investigates or implements"]
    I --> J["Independent reviewer verifies the predefined gate"]
    J --> K{"Decision required"}

    K -->|"Operational"| L["Product or Engineering decides<br/>Quality Assurance may block"]
    K -->|"Ownership, sequencing, or expansion"| M["Coordinator arbitrates"]
    K -->|"Strategy"| N["Strategy lead evaluates<br/>CEO approves or rejects"]

    G --> O["Publish the durable conclusion and handoff"]
    L --> O
    M --> O
    N --> O
```

## 4. Mission lifecycle

```mermaid
flowchart LR
    PROPOSED["Proposed<br/>Question and owner identified"] --> READY["Ready<br/>Packet, capacity, contacts, and gates defined"]
    READY --> ACTIVE["Active<br/>Registered mission and writer scope"]
    ACTIVE --> REVIEW["In review<br/>Independent evidence against end condition"]
    ACTIVE --> BLOCKED["Blocked<br/>Missing decision, evidence, or external condition"]
    BLOCKED --> ACTIVE
    REVIEW --> COMPLETE["Complete<br/>Destination owner accepts handoff"]
    REVIEW --> ACTIVE
    COMPLETE --> ARCHIVE["Archived<br/>Temporary contacts and scopes cleared"]
```

`Ready` does not consume active capacity. A mission name does not create permanent headcount, reporting authority, or a new strategic priority.

## Operating principles

- Keep permanent accountability separate from temporary missions.
- Assign one accountable owner to every customer-facing experience area.
- Let assurance report independently from the work it evaluates.
- Let registered owners consult directly; use the coordinator for exceptions and conflicts.
- Keep one registered writer for overlapping files or product areas.
- Require independent verification when a quality or release gate applies.
- Keep operational, assurance, coordination, and strategy decisions distinct.
- Archive temporary missions and clear their contacts and writer scopes when their end condition is accepted.
- Keep sensitive customer content and secrets out of coordination records.
- Treat cross-organization platform programs as bounded missions with explicit execution, assurance, measurement, and acceptance owners before considering a new department or executive role.
