/**
 * ResearchPilot Phase 1 - TypeScript Data Contracts.
 * Auto-aligned with backend Pydantic v2 schemas.
 */

export interface Project {
  id: string;
  name: string;
  topic: string;
  constraints?: string | null;
  year_range?: string | null;
  created_at: string;
  status: string;
}

export interface ProjectCreate {
  name: string;
  topic: string;
  constraints?: string | null;
  year_range?: string | null;
}

export interface PaperRecord {
  paper_id: string;
  title: string;
  authors: string[];
  year: number;
  doi?: string | null;
  source?: string | null;
  abstract: string;
  open_access_url?: string | null;
  embedding_model?: string;
  embedding_version?: string;
}

export interface BooleanQueries {
  openalex: string;
  arxiv: string;
  github: string;
}

export interface ScopeAnalysisResult {
  original_topic: string;
  problem: string;
  method: string;
  comparison: string;
  outcomes: string;
  research_questions: [string, string, string]; // Exactly 3 RQs
  boolean_queries: BooleanQueries;
  feasibility_score: number; // 0 to 100
  verdict: string;
  warnings: string[];
  is_mock?: boolean;
}

export interface ScoredPaper extends PaperRecord {
  similarity_score: number; // 0.0 to 1.0
}

export interface VectorSearchResponse {
  query: string;
  total_matches: number;
  papers: ScoredPaper[];
  model_id: string;
  dimension: number;
}

export interface CorpusSeedResponse {
  status: string;
  seeded_count: number;
  skipped_count: number;
  total_corpus_count: number;
  papers: PaperRecord[];
}

export interface ImportedRecord {
  paper_id: string;
  title: string;
  authors: string[];
  year: number;
  doi?: string | null;
  source?: string | null;
  abstract: string;
  status: 'imported' | 'duplicate' | 'rejected';
  merge_reason?: string | null;
}

export interface BibTeXImportResponse {
  total_processed: number;
  imported_count: number;
  duplicate_count: number;
  rejected_count: number;
  records: ImportedRecord[];
}

export interface ProviderDiagnosticItem {
  service_name: string;
  configured: boolean;
  status: 'online' | 'degraded' | 'offline' | 'mock';
  measured_latency_ms?: number | null;
  fallback_tier: string;
  model_id?: string | null;
  notes?: string | null;
}

export interface SystemDiagnosticsReport {
  timestamp: string;
  providers: ProviderDiagnosticItem[];
  active_fallback_order: string[];
  cache_hit_ratio: number;
}

export interface TaskEnvelope {
  run_id: string;
  correlation_id: string;
  task_id: string;
  stage: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  timestamp: string;
  payload: Record<string, any>;
  error?: Record<string, any> | null;
  simulation_mode: boolean;
}

// Future Work Contracts
export interface EvidenceSpan {
  span_id: string;
  paper_id: string;
  quote: string;
  section?: string | null;
  page?: number | null;
  confidence: number;
}

export interface PaperProfile {
  paper_id: string;
  primary_methods: string[];
  datasets_used: string[];
  findings: string[];
  limitations: string[];
}

export interface ResourceRecord {
  id: string;
  name: string;
  type: 'code' | 'dataset' | 'benchmark' | 'model';
  url?: string | null;
  description?: string | null;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  weight?: number | null;
}

export interface CandidateGap {
  id: string;
  title: string;
  description: string;
  reason: string;
  priority: 'high' | 'medium' | 'low';
}

export interface ExperimentPlan {
  id: string;
  title: string;
  hypothesis: string;
  methodology: string;
  evaluation_metrics: string[];
}

export interface VerificationAudit {
  audit_id: string;
  status: 'passed' | 'warning' | 'failed';
  checks: Array<Record<string, any>>;
  notes?: string | null;
  timestamp: string;
}
