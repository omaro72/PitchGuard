export type ClaimStatus =
  | "SUPPORTED"
  | "UNSUPPORTED"
  | "CONTRADICTED"
  | "UNCLEAR";

export type ClaimType =
  | "STATISTIC"
  | "COMPARISON"
  | "MARKET_LEADERSHIP"
  | "PERFORMANCE"
  | "FACTUAL"
  | "OTHER";

export type ClaimImportance = "LOW" | "MEDIUM" | "HIGH";

export type RiskSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type RiskCategory =
  | "EXCESSIVE_PROMOTION"
  | "UNSUPPORTED_SUPERLATIVE"
  | "MISLEADING_CERTAINTY"
  | "SPAM_LIKE_LANGUAGE"
  | "UNCLEAR_CALL_TO_ACTION"
  | "CONFIDENTIALITY"
  | "REPUTATIONAL"
  | "OTHER";

export type ReviewDecision = "PASS" | "REVISE" | "BLOCK";
export type AnalysisStatus = "COMPLETE" | "ERROR";
export type ReviewerName = "EVIDENCE" | "RELEVANCE" | "RISK";

export interface CampaignBrief {
  company_name: string;
  announcement: string;
  target_audience: string;
}

export interface EvidenceItem {
  id: string;
  source: string;
  content: string;
  confidential: boolean;
}

export interface CoverageItem {
  id: string;
  title: string;
  summary: string;
  publication_date: string | null;
  url: string | null;
}

export interface JournalistProfile {
  name: string;
  publication: string;
  beat: string;
  recent_coverage: CoverageItem[];
}

export interface ReviewRequest {
  campaign: CampaignBrief;
  evidence: EvidenceItem[];
  journalist: JournalistProfile;
  pitch: string;
}

export interface ClaimFinding {
  claim_text: string;
  claim_type: ClaimType;
  importance: ClaimImportance;
  status: ClaimStatus;
  explanation: string;
  evidence_ids: string[];
}

export interface EvidenceReview {
  claims: ClaimFinding[];
  summary: string;
  missing_context: string[];
}

export interface RelevanceReview {
  relevance_score: number;
  personalization_score: number;
  summary: string;
  matched_topics: string[];
  mismatches: string[];
  missing_context: string[];
}

export interface RiskFinding {
  category: RiskCategory;
  severity: RiskSeverity;
  pitch_excerpt: string | null;
  explanation: string;
  recommendation: string;
}

export interface RiskReview {
  findings: RiskFinding[];
  summary: string;
  missing_context: string[];
}

export interface ReviewerError {
  reviewer: ReviewerName;
  code: string;
  message: string;
  retryable: boolean;
}

export interface ReviewResponse {
  analysis_status: AnalysisStatus;
  decision: ReviewDecision | null;
  decision_reasons: string[];
  evidence_review: EvidenceReview | null;
  relevance_review: RelevanceReview | null;
  risk_review: RiskReview | null;
  errors: ReviewerError[];
}
