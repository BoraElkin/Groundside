export enum DisputeState {
  PENALTY_UPLOADED = 'penalty_uploaded',
  EXTRACTING_DETAILS = 'extracting_details',
  DETAILS_EXTRACTED = 'details_extracted',
  GATHERING_EVIDENCE = 'gathering_evidence',
  EVIDENCE_GATHERED = 'evidence_gathered',
  ANALYZING = 'analyzing',
  ANALYSIS_COMPLETE = 'analysis_complete',
  GENERATING_RESPONSE = 'generating_response',
  RESPONSE_GENERATED = 'response_generated',
  UNDER_REVIEW = 'under_review',
  APPROVED = 'approved',
  EXPORTED = 'exported',
  FAILED = 'failed',
}

export enum DisputeRecommendation {
  FULL_DISPUTE = 'full_dispute',
  PARTIAL_DISPUTE = 'partial_dispute',
  ACCEPT_PENALTY = 'accept_penalty',
  UNKNOWN = 'unknown',
}

export enum EvidenceType {
  TIMESTAMP_LOG = 'timestamp_log',
  PHOTO = 'photo',
  VIDEO = 'video',
  DOCUMENT = 'document',
  SYSTEM_LOG = 'system_log',
  WITNESS_STATEMENT = 'witness_statement',
  COMMUNICATION = 'communication',
}

export enum ResponsibleParty {
  HANDLER = 'handler',
  AIRLINE = 'airline',
  AIRPORT = 'airport',
  VENDOR_FUEL = 'vendor_fuel',
  VENDOR_CATERING = 'vendor_catering',
  VENDOR_CLEANING = 'vendor_cleaning',
  ATC = 'atc',
  WEATHER = 'weather',
  OTHER = 'other',
}

export interface Dispute {
  id: string
  customer_id?: string
  state: DisputeState
  flight_number?: string
  flight_date?: string
  airline_code?: string
  origin?: string
  destination?: string
  aircraft_type?: string
  claimed_delay_minutes?: number
  penalty_amount?: number
  penalty_currency?: string
  airline_claimed_reason?: string
  airline_specific_claims?: string[]
  actual_delay_minutes?: number
  handler_responsible_minutes?: number
  root_cause_analysis?: string
  responsibility_breakdown?: Record<string, number>
  iata_delay_codes?: string[]
  recommendation?: DisputeRecommendation
  confidence_score?: number
  dispute_response_text?: string
  outcome?: string
  savings_amount?: number
  error_message?: string
  created_at: string
  updated_at: string
}

export interface DisputeActivity {
  id?: string
  dispute_id?: string
  activity_type: string
  performed_by: ResponsibleParty
  scheduled_start?: string
  actual_start?: string
  scheduled_end?: string
  actual_end?: string
  scheduled_duration_minutes?: number
  actual_duration_minutes?: number
  notes?: string
}

export interface Evidence {
  id: string
  dispute_id: string
  evidence_type: EvidenceType
  summary: string
  timestamp?: string
  file_id?: string
  metadata?: Record<string, any>
}

export interface DisputeDetail extends Dispute {
  activities: DisputeActivity[]
  evidence: Evidence[]
}

export interface DisputeStatus {
  id: string
  state: DisputeState
  progress_percentage: number
  current_step: string
  error_message?: string
  estimated_completion_seconds?: number
}

export interface DisputeStats {
  total_disputes: number
  disputes_this_month: number
  total_penalties_claimed: number
  total_savings: number
  win_rate_percentage: number
  avg_time_to_resolve_minutes: number
  disputes_by_state: Record<DisputeState, number>
  disputes_by_recommendation: Record<DisputeRecommendation, number>
}

export interface DisputeCreateData {
  flight_number: string
  flight_date: string
  airline_code?: string
  claimed_delay_minutes: number
  penalty_amount: number
  penalty_currency?: string
  airline_claimed_reason?: string
  scheduled_arrival?: string
  actual_arrival?: string
  scheduled_departure?: string
  actual_departure?: string
}
