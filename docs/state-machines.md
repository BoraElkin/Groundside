# State Machine Diagrams

This document defines the state machines used in the Ground Operations Intelligence Platform.

## Turnaround State Machine

The turnaround lifecycle from aircraft arrival to departure.

```mermaid
stateDiagram-v2
    [*] --> SCHEDULED: Flight created

    SCHEDULED --> IN_PROGRESS: Aircraft arrives at gate

    IN_PROGRESS --> ON_TIME: Progress normal
    IN_PROGRESS --> AT_RISK: Risk score > 0.5
    IN_PROGRESS --> DELAYED: Delay confirmed

    ON_TIME --> AT_RISK: Risk detected
    ON_TIME --> COMPLETED: All activities done

    AT_RISK --> ON_TIME: Risk mitigated
    AT_RISK --> DELAYED: Delay confirmed
    AT_RISK --> COMPLETED: Completed with minor delay

    DELAYED --> COMPLETED: Turnaround finished

    COMPLETED --> [*]
```

### Turnaround States

| State | Description |
|-------|-------------|
| `SCHEDULED` | Turnaround is planned but aircraft has not arrived |
| `IN_PROGRESS` | Aircraft at gate, ground operations underway |
| `ON_TIME` | Operations progressing within scheduled timeframe |
| `AT_RISK` | Potential delay detected (risk_score > 0.5) |
| `DELAYED` | Confirmed delay beyond scheduled completion |
| `COMPLETED` | All turnaround activities finished |

---

## Activity State Machine

Individual turnaround activities (cleaning, refueling, boarding, etc.)

```mermaid
stateDiagram-v2
    [*] --> PENDING: Activity scheduled

    PENDING --> IN_PROGRESS: Activity starts
    PENDING --> BLOCKED: Dependency not met

    BLOCKED --> PENDING: Blocker resolved
    BLOCKED --> IN_PROGRESS: Unblocked & started

    IN_PROGRESS --> COMPLETED: Activity finished
    IN_PROGRESS --> DELAYED: Behind schedule

    DELAYED --> COMPLETED: Finished late

    COMPLETED --> [*]
```

### Activity States

| State | Description |
|-------|-------------|
| `PENDING` | Activity scheduled, waiting to start |
| `IN_PROGRESS` | Activity currently being performed |
| `COMPLETED` | Activity finished successfully |
| `DELAYED` | Activity running behind schedule |
| `BLOCKED` | Cannot start due to unmet dependencies |

### Activity Types (Sequential Order)

```mermaid
flowchart LR
    A[Aircraft Arrival] --> B[Passenger Deboarding]
    B --> C[Cargo Unloading]

    C --> D[Cleaning]
    C --> E[Catering]
    C --> F[Refueling]
    C --> G[Water Service]
    C --> H[Lavatory Service]

    D --> I[Cargo Loading]
    E --> I
    F --> I
    G --> I
    H --> I

    I --> J[Passenger Boarding]
    J --> K[Pushback]
    K --> L[Aircraft Departure]
```

---

## Flight State Machine

Flight status progression through the system.

```mermaid
stateDiagram-v2
    [*] --> SCHEDULED: Flight scheduled

    SCHEDULED --> AIRBORNE: Takeoff confirmed
    SCHEDULED --> DELAYED: Delay announced
    SCHEDULED --> CANCELLED: Flight cancelled

    DELAYED --> AIRBORNE: Departed late
    DELAYED --> CANCELLED: Cancelled due to delay

    AIRBORNE --> LANDED: Touchdown

    LANDED --> AT_GATE: Arrived at gate

    AT_GATE --> BOARDING: Boarding begins

    BOARDING --> DEPARTED: Pushback complete

    DEPARTED --> [*]
    CANCELLED --> [*]
```

### Flight States

| State | Description |
|-------|-------------|
| `SCHEDULED` | Flight is planned |
| `AIRBORNE` | Aircraft is in flight |
| `LANDED` | Aircraft has touched down |
| `AT_GATE` | Aircraft parked at gate |
| `BOARDING` | Passengers boarding |
| `DEPARTED` | Aircraft has left |
| `DELAYED` | Flight is delayed |
| `CANCELLED` | Flight cancelled |

---

## Alert State Machine

Alert lifecycle from creation to resolution.

```mermaid
stateDiagram-v2
    [*] --> ACTIVE: Alert triggered

    ACTIVE --> ACKNOWLEDGED: User acknowledges
    ACTIVE --> DISMISSED: User dismisses
    ACTIVE --> RESOLVED: Auto-resolved

    ACKNOWLEDGED --> RESOLVED: Issue fixed
    ACKNOWLEDGED --> DISMISSED: No action needed

    RESOLVED --> [*]
    DISMISSED --> [*]
```

### Alert States

| State | Description |
|-------|-------------|
| `ACTIVE` | Alert is active and requires attention |
| `ACKNOWLEDGED` | User has seen and accepted the alert |
| `RESOLVED` | Issue has been addressed |
| `DISMISSED` | Alert was dismissed without action |

### Alert Severity Levels

```mermaid
flowchart TB
    subgraph Severity
        INFO[INFO - Informational]
        WARNING[WARNING - Action recommended]
        CRITICAL[CRITICAL - Immediate action required]
    end

    INFO --> |Escalate| WARNING
    WARNING --> |Escalate| CRITICAL
```

---

## Combined System Flow

Overview of how states interact across the system.

```mermaid
flowchart TB
    subgraph Flight Lifecycle
        F1[SCHEDULED] --> F2[AIRBORNE]
        F2 --> F3[LANDED]
        F3 --> F4[AT_GATE]
        F4 --> F5[BOARDING]
        F5 --> F6[DEPARTED]
    end

    subgraph Turnaround Lifecycle
        T1[SCHEDULED] --> T2[IN_PROGRESS]
        T2 --> T3{Risk Assessment}
        T3 --> |Low Risk| T4[ON_TIME]
        T3 --> |High Risk| T5[AT_RISK]
        T3 --> |Delay Confirmed| T6[DELAYED]
        T4 --> T7[COMPLETED]
        T5 --> T7
        T6 --> T7
    end

    subgraph Alert System
        A1[ACTIVE] --> A2[ACKNOWLEDGED]
        A2 --> A3[RESOLVED]
    end

    F3 --> |Triggers| T1
    T2 --> |Activities| Activities
    T3 --> |Risk Detected| A1
    T7 --> |Enables| F5

    subgraph Activities
        ACT1[Deboarding]
        ACT2[Ground Services]
        ACT3[Boarding]
    end
```

---

## State Transition Rules

### Turnaround Transitions

| From | To | Trigger |
|------|-----|---------|
| SCHEDULED | IN_PROGRESS | `actual_start` is set |
| IN_PROGRESS | ON_TIME | `risk_score < 0.3` and on schedule |
| IN_PROGRESS | AT_RISK | `risk_score > 0.5` |
| IN_PROGRESS | DELAYED | `predicted_delay > threshold` |
| ON_TIME | AT_RISK | `risk_score` increases above 0.5 |
| AT_RISK | ON_TIME | Risk factors mitigated |
| AT_RISK | DELAYED | Delay becomes certain |
| * | COMPLETED | `actual_end` is set |

### Activity Transitions

| From | To | Trigger |
|------|-----|---------|
| PENDING | IN_PROGRESS | `actual_start` is set |
| PENDING | BLOCKED | Dependency activity not completed |
| BLOCKED | PENDING | Dependency resolved |
| IN_PROGRESS | COMPLETED | `actual_end` is set |
| IN_PROGRESS | DELAYED | `delay_minutes > 0` |
| DELAYED | COMPLETED | Activity finished despite delay |
