"""
LLM prompts for dispute resolution agent.
"""

PENALTY_EXTRACTION_PROMPT = """You are analyzing an airline penalty notice for a ground handling company.

Extract the following information from the document:

1. Flight number (e.g., TK1234, LH456)
2. Flight date (YYYY-MM-DD format)
3. Origin and destination airports (IATA codes if available)
4. Claimed delay in minutes
5. Penalty amount and currency
6. Reason given by airline for the delay
7. Any specific claims about ground handler responsibility

Document content:
{document_text}

Respond in JSON format:
{{
    "flight_number": "...",
    "flight_date": "YYYY-MM-DD",
    "origin": "...",
    "destination": "...",
    "claimed_delay_minutes": ...,
    "penalty_amount": ...,
    "penalty_currency": "...",
    "airline_claimed_reason": "...",
    "airline_specific_claims": ["...", "..."],
    "confidence": 0.95
}}

If any information is not found in the document, use null for that field.
"""


ROOT_CAUSE_ANALYSIS_PROMPT = """You are an aviation operations expert analyzing a delay incident to determine the actual root cause and assign responsibility.

## Penalty Claim
- Flight: {flight_number}
- Date: {flight_date}
- Airline claims: {claimed_delay_minutes} minutes delay
- Airline's stated reason: {airline_claimed_reason}

## Flight Timing
- Scheduled Arrival: {scheduled_arrival}
- Actual Arrival: {actual_arrival}
- Scheduled Departure: {scheduled_departure}
- Actual Departure: {actual_departure}

## Turnaround Activity Log
{turnaround_activities}

## Additional Evidence
{evidence_summary}

## Standard Turnaround Times (for reference)

**Narrow-body aircraft (A320, B737):**
- Deboarding: 8-15 min
- Cleaning: 12-20 min
- Catering: 10-20 min
- Fueling: 15-30 min
- Boarding: 15-30 min
- Pushback: 3-5 min

**Wide-body aircraft (A330, B777, A350):**
- Deboarding: 15-25 min
- Cleaning: 20-35 min
- Catering: 15-30 min
- Fueling: 20-40 min
- Boarding: 25-40 min
- Pushback: 5-8 min

## IATA Delay Codes (for reference)
- 11: Late crew or cabin crew (airline responsibility)
- 13: Late captain (airline responsibility)
- 16: De-icing (airport/weather)
- 31: Flight deck technical defects (airline responsibility)
- 32: Catering (vendor responsibility)
- 33: Cleaning (handler/vendor responsibility)
- 34: Fueling (vendor responsibility)
- 43: Flight documentation late (airline responsibility)
- 61: Runway closed (airport/ATC)
- 69: Airport services (airport responsibility)
- 71-77: Weather delays
- 81: Load connection (airline/handler responsibility)
- 82: Baggage late (handler responsibility)
- 87: Loading/off-loading delayed (handler responsibility)
- 91: Late aircraft arrival (airline responsibility)
- 93: Late inbound connection (airline responsibility)

## Your Task

Analyze the incident and provide:

1. **Actual delay calculation**: Compare scheduled vs actual departure
2. **Activity analysis**: Identify which activities ran over standard times
3. **Root cause determination**: What actually caused the delay?
4. **Responsibility assignment**: Assign percentage responsibility to each party
5. **IATA delay codes**: Which codes apply to this incident?
6. **Recommendation**: Should this be a full dispute, partial dispute, or accept?

Consider:
- Late inbound aircraft reduces available turnaround time (NOT handler's fault)
- Airline crew issues (late check-in, late from hotel) are airline responsibility
- Vendor delays (catering truck late, fuel delay) are vendor responsibility
- Handler is only responsible for activities they directly control
- Airport/ATC delays are not handler's fault
- Weather delays are not handler's fault

Respond in JSON format:
{{
    "actual_delay_minutes": ...,
    "root_causes": [
        {{
            "cause": "...",
            "responsible_party": "handler|airline|airport_atc|weather|vendor_catering|vendor_fuel|vendor_other|passengers|other",
            "delay_minutes": ...,
            "iata_code": "...",
            "explanation": "..."
        }}
    ],
    "responsibility_breakdown": {{
        "handler": ...,
        "airline": ...,
        "airport_atc": ...,
        "weather": ...,
        "vendor_catering": ...,
        "vendor_fuel": ...,
        "vendor_other": ...,
        "passengers": ...,
        "other": ...
    }},
    "handler_responsible_minutes": ...,
    "iata_delay_codes": ["...", "..."],
    "analysis_summary": "Brief explanation of what happened and why",
    "recommendation": "full_dispute|partial_dispute|accept",
    "confidence": 0.0-1.0,
    "key_evidence": [
        "Specific evidence point that supports our case",
        "Another evidence point"
    ]
}}

Be objective and fair. If the handler WAS responsible, say so. But defend them when the evidence shows they were not at fault.
"""


DISPUTE_RESPONSE_GENERATION_PROMPT = """You are a professional writer drafting a dispute response letter on behalf of a ground handling company.

## Context
- Ground handler: {handler_name}
- Airline: {airline_name}
- Flight: {flight_number} on {flight_date}
- Route: {origin} → {destination}
- Penalty claimed: {penalty_amount} {penalty_currency}
- Airline's claim: {airline_claimed_reason}

## Our Analysis
{root_cause_analysis}

## Evidence Summary
{evidence_summary}

## Responsibility Breakdown
- Handler responsible: {handler_minutes} minutes ({handler_percent}%)
- Airline responsible: {airline_minutes} minutes ({airline_percent}%)
- Vendor responsible: {vendor_minutes} minutes ({vendor_percent}%)
- Other factors: {other_minutes} minutes ({other_percent}%)

## IATA Delay Codes
{iata_codes}

## Recommendation
{recommendation}

## Instructions

Write a professional, factual dispute letter that:

1. **Opening**: Acknowledge receipt of penalty notice and state purpose (dispute)
2. **Summary**: One paragraph overview of our position
3. **Detailed Analysis**: Break down what actually happened:
   - Late inbound aircraft (if applicable)
   - Each activity and who performed it
   - Where delays actually occurred
   - Who was responsible for each delay
4. **Evidence**: Reference specific:
   - Timestamps from activity logs
   - AODB records showing late arrival
   - GPS/system logs (if available)
   - Industry standard turnaround times
5. **Handler Performance**: Show that handler activities were completed on time and within standards
6. **IATA Delay Codes**: Use proper codes to categorize delays
7. **Conclusion**: Clear statement of what you're requesting:
   - Full waiver (if handler 0% responsible)
   - Adjusted penalty (if handler partially responsible)
   - Acknowledgment that delay was unavoidable

## Tone and Style
- Professional and respectful (you want to maintain good airline relationship)
- Fact-based and objective (cite specific times, data, standards)
- Confident but not aggressive
- Concise (2-3 pages maximum)
- Use aviation industry terminology appropriately

## Structure
Use this structure:
```
[Date]

[Airline Operations Contact]
[Airline Name]

Re: Delay Penalty Dispute - Flight [Number] ([Date])

Dear [Airline] Operations Team,

[Your letter here]

Sincerely,
[Handler Name] Operations Team
```

Generate the complete letter now. Use specific times and data points from the analysis. Make it compelling but fair.
"""


EVIDENCE_SUMMARIZATION_PROMPT = """Summarize the following evidence items in a clear, concise format for inclusion in a dispute letter.

Evidence items:
{evidence_items}

For each piece of evidence, provide:
1. What it shows
2. Why it's relevant to the dispute
3. How it supports the handler's position

Format as a bulleted list suitable for inclusion in a formal letter.
"""


IATA_CODE_EXPLANATION_PROMPT = """Explain the following IATA delay codes in the context of this dispute:

Codes: {iata_codes}

Provide a brief (1-2 sentence) explanation of each code and why it applies to this situation.
"""


RESPONSE_REGENERATION_PROMPT = """The user has requested changes to the generated dispute response.

Original response:
{original_response}

User feedback:
{user_feedback}

Please regenerate the dispute response incorporating the user's feedback while maintaining:
- Professional tone
- Factual accuracy
- All key evidence points
- Proper structure

Generate the updated response now.
"""


TEMPLATE_CUSTOMIZATION_PROMPT = """Adapt the following dispute response to match the airline's preferred format and tone.

Base response:
{base_response}

Airline-specific requirements:
- Airline: {airline_name}
- Preferred tone: {tone}
- Include IATA codes: {include_iata}
- Include timeline: {include_timeline}
- Additional instructions: {custom_instructions}

Generate the customized response now.
"""
