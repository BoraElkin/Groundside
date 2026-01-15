# GroundCrew AI

**AI agents that handle the busywork ground handlers hate.**

## The Problem

Ground handlers lose $10-50K monthly in delay penalties for delays that weren't their fault. The dispute process is brutal:

- Airline sends penalty: "Flight TK1234 departed 18 min late. Your fault. $900 penalty."
- Handler must dig through logs, GPS data, timestamps, radio transcripts
- Write formal dispute response with evidence
- **Takes 3-6 hours per dispute**
- Often lose anyway due to poor documentation

## The Solution

**GroundCrew AI Dispute Agent** - Upload airline penalty notice → Get professional dispute response in 4 minutes.

The agent automatically:
1. ✅ Extracts flight details, claimed delay, penalty amount
2. ✅ Retrieves all relevant evidence (turnaround timeline, GPS, communications)
3. ✅ Analyzes root cause and determines actual responsibility
4. ✅ Generates professional dispute response letter
5. ✅ Attaches evidence package
6. ✅ User reviews, edits if needed, downloads/sends

**Time to resolve: 4 hours → 4 minutes**

## MVP Features

### Core Workflow
- 📤 **Upload penalty notice** (PDF, image, or manual entry)
- 🤖 **AI extracts details** (flight number, date, delay, amount) using Claude
- 📊 **Manual evidence entry** (turnaround activities, timestamps) via form/CSV/JSON
- 🔍 **AI analyzes root cause** and assigns responsibility percentages
- ✍️ **AI generates dispute letter** using IATA delay codes and evidence
- ✏️ **Review and edit** response before sending
- 📄 **Export as PDF/DOCX** with evidence package

### What You Get
- **Professional dispute letters** citing specific evidence
- **Responsibility breakdown** (handler vs airline vs vendors vs weather)
- **IATA delay code** analysis
- **Evidence timeline** visualization
- **Recommendation**: Full dispute, partial dispute, or accept

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy async
- **AI**: Anthropic Claude Sonnet 4 for document parsing, analysis, and generation
- **Data**: PostgreSQL (disputes, evidence, flights)
- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **Infrastructure**: Docker, Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Anthropic API key (get at https://console.anthropic.com)

### Installation

1. **Clone and setup**:
```bash
git clone <repository-url>
cd Groundside
cp .env.example .env
```

2. **Add your Anthropic API key** to `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

3. **Start the platform**:
```bash
docker-compose up -d
```

4. **Seed the database**:
```bash
docker-compose exec backend python scripts/seed_data.py
```

5. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

### Creating a Dispute

**Option 1: Upload Penalty Notice**
```bash
curl -X POST http://localhost:8000/api/v1/disputes/upload \
  -F "file=@penalty_notice.pdf"
```

**Option 2: Manual Entry**
```bash
curl -X POST http://localhost:8000/api/v1/disputes \
  -H "Content-Type: application/json" \
  -d '{
    "flight_number": "TK1234",
    "flight_date": "2025-01-14",
    "claimed_delay_minutes": 18,
    "penalty_amount": 900,
    "airline_claimed_reason": "Ground handler delay"
  }'
```

### Adding Evidence
```bash
curl -X POST http://localhost:8000/api/v1/disputes/{dispute_id}/evidence \
  -H "Content-Type: application/json" \
  -d '{
    "activities": [
      {
        "activity_type": "deboarding",
        "scheduled_start": "2025-01-14T09:58:00Z",
        "actual_start": "2025-01-14T09:58:00Z",
        "actual_end": "2025-01-14T10:11:00Z",
        "performed_by": "handler"
      },
      {
        "activity_type": "catering",
        "scheduled_start": "2025-01-14T10:11:00Z",
        "actual_start": "2025-01-14T10:22:00Z",
        "actual_end": "2025-01-14T10:38:00Z",
        "performed_by": "vendor",
        "notes": "Catering truck dispatched to wrong gate initially"
      }
    ]
  }'
```

### Process the Dispute
```bash
# Trigger AI analysis
curl -X POST http://localhost:8000/api/v1/disputes/{dispute_id}/analyze

# Check status
curl http://localhost:8000/api/v1/disputes/{dispute_id}/status

# Get generated response
curl http://localhost:8000/api/v1/disputes/{dispute_id}

# Export as PDF
curl http://localhost:8000/api/v1/disputes/{dispute_id}/export?format=pdf \
  --output dispute_response.pdf
```

## Project Structure

```
groundcrew-ai/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── disputes.py      # Dispute CRUD and workflow
│   │   │   ├── evidence.py      # Evidence management
│   │   │   └── customers.py     # Customer/auth management
│   │   ├── auth.py              # API key authentication
│   │   └── metering.py          # Usage tracking
│   │
│   ├── models/
│   │   ├── dispute.py           # Dispute and evidence models
│   │   ├── flight.py            # Flight data models
│   │   └── customer.py          # Multi-tenancy models
│   │
│   ├── agents/
│   │   ├── base_agent.py        # Base agent class
│   │   ├── dispute_agent/
│   │   │   ├── orchestrator.py  # Main dispute agent
│   │   │   ├── state_machine.py # State management
│   │   │   ├── penalty_extractor.py   # Parse penalty notices
│   │   │   ├── root_cause_analyzer.py # Determine responsibility
│   │   │   └── response_generator.py  # Generate dispute letter
│   │   └── shared/
│   │       ├── llm_client.py    # Claude API wrapper
│   │       ├── prompts.py       # LLM prompts
│   │       └── iata_codes.py    # IATA delay code reference
│   │
│   ├── services/
│   │   ├── file_storage.py      # File upload/download
│   │   ├── pdf_generator.py     # PDF export
│   │   └── document_parser.py   # Parse uploaded docs
│   │
│   └── scripts/
│       └── seed_data.py         # Seed test data
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.tsx         # Disputes list + stats
│       │   ├── NewDispute.tsx        # Upload penalty notice
│       │   └── DisputeDetail.tsx     # Review/edit response
│       └── components/
│           ├── FileUpload.tsx        # Drag-drop upload
│           ├── DisputeTimeline.tsx   # Visual timeline
│           ├── ResponseEditor.tsx    # Edit generated text
│           └── ExportOptions.tsx     # Download buttons
│
└── docs/
    ├── architecture.md
    ├── agent-design.md
    └── iata-delay-codes.md
```

## How It Works

### Agent Architecture

The Dispute Agent uses a multi-step pipeline:

```
1. PenaltyExtractor
   ├─ Parse uploaded document (PDF/image)
   ├─ Extract: flight number, date, delay, amount, reason
   └─ Uses Claude for document understanding

2. EvidenceGatherer
   ├─ User provides turnaround activity log
   ├─ Optionally: GPS data, weather, AODB records
   └─ Structures evidence for analysis

3. RootCauseAnalyzer
   ├─ Compares actual vs standard turnaround times
   ├─ Identifies delays by activity and responsible party
   ├─ Assigns responsibility percentages
   └─ Recommends: full dispute, partial, or accept

4. ResponseGenerator
   ├─ Writes professional dispute letter
   ├─ Cites specific evidence and timestamps
   ├─ Uses IATA delay codes where appropriate
   ├─ Maintains professional tone
   └─ Includes evidence package

5. User Review
   ├─ User edits response if needed
   ├─ Regenerate with different emphasis
   └─ Export as PDF/DOCX
```

### State Machine

```
UPLOADED → EXTRACTING → EXTRACTED → GATHERING → GATHERED
       → ANALYZING → ANALYZED → GENERATING → GENERATED
       → REVIEWING → APPROVED → EXPORTED
```

## Example Output

**Input**: Airline penalty notice claiming 18 min delay, $900 penalty

**Agent Output**:
```
Recommendation: FULL DISPUTE (94% confidence)

Responsibility Breakdown:
- Catering Vendor: 12 min (67%)
- Airline (late crew): 4 min (22%)
- Late inbound aircraft: 13 min (not handler's fault)
- Ground Handler: 0 min (0%)

Generated Response:
"Dear Turkish Airlines Operations Team,

Re: Delay Penalty Dispute - Flight TK1234 (14 January 2025)

We are writing to formally dispute the delay penalty of $900 assessed
for Flight TK1234 on 14 January 2025.

SUMMARY OF FINDINGS
Our analysis indicates that the 18-minute departure delay was caused by
factors outside our control:

1. Late Aircraft Arrival (IATA Code 93): The inbound aircraft arrived
   13 minutes behind schedule at 09:58, reducing available turnaround
   time from 60 to 47 minutes.

2. Catering Vendor Delay (IATA Code 32): The catering truck was
   initially dispatched to gate A24 instead of A23, resulting in a
   16-minute delay (log timestamp 10:18 shows redirection).

3. Flight Crew Late Check-in (IATA Code 11): Your crew reported 4
   minutes late for boarding preparation.

HANDLER PERFORMANCE
Our team completed all assigned activities on time:
- Deboarding: 13 min (within 8-15 min standard)
- Cleaning: 14 min (within 12-20 min standard)
- Boarding: 18 min (within 15-30 min standard)

We respectfully request full waiver of the $900 penalty as the delay
was not caused by ground handling operations.

Evidence package attached."
```

## API Authentication

GroundCrew AI supports both:
1. **API key authentication** (for programmatic access)
2. **No auth** (for MVP single-user deployment)

To enable API keys:
```bash
# Create customer
curl -X POST http://localhost:8000/api/v1/customers \
  -d '{"name": "My Ground Handler", "organization_type": "ground_handler"}'

# Generate API key
curl -X POST http://localhost:8000/api/v1/customers/me/api-keys \
  -d '{"name": "Production Key", "scopes": ["disputes:read", "disputes:write"]}'

# Use in requests
curl -H "X-API-Key: gs_live_..." http://localhost:8000/api/v1/disputes
```

## Configuration

Key `.env` variables:

```bash
# API
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/groundcrew

# AI
ANTHROPIC_API_KEY=sk-ant-api03-...
LLM_MODEL=claude-sonnet-4-20250514

# Storage
STORAGE_TYPE=local
STORAGE_PATH=./uploads

# Frontend
VITE_API_URL=http://localhost:8000
```

## Roadmap

### MVP (Week 1-2) ✅
- [x] Upload penalty notice
- [x] Extract details with LLM
- [x] Manual evidence entry
- [x] Root cause analysis
- [x] Generate dispute response
- [x] Export as PDF

### Phase 2 (Week 3-4)
- [ ] Better document parsing (various formats)
- [ ] Evidence strength scoring
- [ ] Weather API integration
- [ ] Airline-specific response templates
- [ ] Dispute history and analytics

### Phase 3 (Week 5-6)
- [ ] Connect to customer's operational data
- [ ] Automatic evidence gathering
- [ ] Batch processing
- [ ] Success rate tracking

### Future
- [ ] Multi-language support
- [ ] Email integration (auto-process penalties from inbox)
- [ ] Chat interface for dispute refinement
- [ ] Mobile app

## Business Model

- **Free**: 5 disputes/month
- **Starter**: $99/month, 25 disputes/month
- **Professional**: $299/month, 100 disputes/month
- **Enterprise**: Custom pricing, unlimited disputes, API access

## Support

For questions or issues:
- Email: support@groundcrew.ai
- Documentation: https://docs.groundcrew.ai

## License

Proprietary - All rights reserved

---

**Transform disputes from 4 hours to 4 minutes.**
