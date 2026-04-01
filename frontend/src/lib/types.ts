export interface PromptConfig {
  name: string;
  system: string;
  model: string;
  temperature: number;
  max_tokens: number;
}

export interface ExperimentConfig {
  prompts: {
    a: PromptConfig;
    b: PromptConfig;
  };
  judge_model: string;
}

export interface Experiment {
  id: string;
  name: string;
  description: string;
  hypothesis: string;
  config: ExperimentConfig | null;
  created_at: string;
  updated_at: string;
}

export interface SummaryMetrics {
  winner: string;
  confidence: string;
  score_a: number;
  score_b: number;
  score_delta: number;
  recommendation: string;
}

export interface ExperimentListItem {
  id: string;
  name: string;
  description: string;
  hypothesis: string;
  run_count: number;
  last_run_at: string | null;
  last_run_metrics: SummaryMetrics | null;
}

export interface RunHistoryItem {
  id: string;
  experiment_id: string | null;
  experiment_name: string | null;
  status: string;
  prompt_names: Record<string, string>;
  prompt_models: Record<string, string>;
  total_cases: number;
  error_count: number;
  created_at: string;
  completed_at: string | null;
  summary_metrics: SummaryMetrics | null;
}

export interface RunHistoryResponse {
  items: RunHistoryItem[];
  total: number;
}

export interface ExperimentFormData {
  name: string;
  description: string;
  hypothesis: string;
  config: ExperimentConfig;
}

export interface TestCase {
  id: string;
  case_identifier: string;
  category: string;
  input: string;
  context?: string;
  reference?: string;
}

export interface TestSet {
  id: string;
  name: string;
  cases: TestCase[];
  created_at: string;
  updated_at: string;
}

export interface TestSetListItem {
  id: string;
  name: string;
  case_count: number;
}

export interface TestSetFormData {
  name: string;
  cases: Omit<TestCase, "id">[];
}

export interface RubricLevel {
  score: number;
  description: string;
}

export interface RubricDimension {
  id: string;
  name: string;
  description: string;
  weight: number;
  levels: RubricLevel[];
  sort_order: number;
}

export interface Rubric {
  id: string;
  name: string;
  dimensions: RubricDimension[];
}

export interface RubricListItem {
  id: string;
  name: string;
}

export interface RubricDimensionFormData {
  name: string;
  description: string;
  weight: number;
  levels: RubricLevel[];
}

export interface RubricFormData {
  name: string;
  dimensions: RubricDimensionFormData[];
}

export interface RunListItem {
  id: string;
  status: string;
  prompt_names: Record<string, string>;
  prompt_models: Record<string, string>;
  total_cases: number;
  error_count: number;
  created_at: string;
  completed_at: string | null;
}

export interface ConfidenceInterval {
  mean: number;
  lower: number;
  upper: number;
  ci_level: number;
}

export interface PromptDimensionStats {
  mean: number;
  std: number;
  n: number;
  ci_95: ConfidenceInterval;
}

export interface DimensionComparison {
  mean_diff: number;
  ttest: {
    t_statistic: number;
    p_value: number;
    significant_005: boolean;
    significant_010: boolean;
  };
  cohens_d: number;
  effect_interpretation: string;
  better: string;
}

export interface DimensionAnalysis {
  weight: number;
  comparison: DimensionComparison;
  [promptName: string]: PromptDimensionStats | number | DimensionComparison;
}

export interface PointwiseData {
  dimensions: Record<string, DimensionAnalysis>;
  overall_weighted: Record<string, number | string>;
}

export interface PairwiseData {
  total: number;
  [key: string]: number | string;
}

export interface CategoryBreakdownEntry {
  n_cases: number;
  better: string;
  [promptName: string]: number | string;
}

export interface NotableCase {
  test_case_id: string;
  category: string;
  input: string;
  mean_delta: number;
}

export interface Recommendation {
  winner: string;
  confidence: string;
  signals: {
    for_a: number;
    for_b: number;
    confidence: string;
  };
}

export interface PromptMetrics {
  name: string;
  model: string;
  n_responses: number;
  latency: { avg: number; p50: number; p95: number };
  tokens: { total_input: number; total_output: number; total: number; avg_per_response: number };
  cost_usd: number;
}

export interface OperationalMetrics {
  per_prompt: Record<string, PromptMetrics>;
  multi_variable_warning: boolean;
}

export interface AnalysisData {
  prompt_a: { key: string; name: string };
  prompt_b: { key: string; name: string };
  pointwise: PointwiseData;
  pairwise: PairwiseData;
  category_breakdown: Record<string, CategoryBreakdownEntry>;
  notable_cases: Record<string, NotableCase[]>;
  recommendation: Recommendation;
  operational_metrics?: OperationalMetrics;
}

export interface RunResultsData {
  run_id: string;
  run_data: Record<string, unknown> | null;
  eval_data: Record<string, unknown> | null;
  analysis: { analysis: AnalysisData } | null;
}

export interface DryRunResult {
  valid: boolean;
  experiment_name: string;
  test_case_count: number;
  prompt_names: string[];
  prompt_models: Record<string, string>;
  rubric_name: string;
}

export interface JobProgress {
  step: string;
  detail: string;
}

export interface JobStatus {
  job_id: string;
  status: "pending" | "running" | "done" | "failed";
  result: Record<string, string> | null;
  error: string | null;
  progress: JobProgress | null;
  created_at: string;
  updated_at: string;
}

export interface SettingItem {
  key: string;
  value: string;
  is_set: boolean;
}

export interface EvalDimensionScore {
  score: number | null;
  reasoning: string;
}

export interface EvalPairwiseRound {
  winner: string;
  reasoning: string;
}

export interface EvalPairwise {
  winner: string;
  consistent: boolean;
  round1?: EvalPairwiseRound;
  round2_swapped?: EvalPairwiseRound;
}

export interface EvalCase {
  test_case_id: string;
  category: string;
  input: string;
  pointwise?: Record<string, Record<string, EvalDimensionScore>>;
  pairwise?: EvalPairwise;
  skipped?: boolean;
}

export interface RunCaseResponse {
  response: string;
  input_tokens: number;
  output_tokens: number;
  latency_seconds: number;
  model: string;
  stop_reason: string;
}

export interface RunCase {
  test_case_id: string;
  category: string;
  input: string;
  context?: string | null;
  reference?: string | null;
  responses: Record<string, RunCaseResponse>;
}

export interface MergedCase {
  test_case_id: string;
  category: string;
  input: string;
  context?: string | null;
  reference?: string | null;
  responses: Record<string, RunCaseResponse>;
  pointwise?: Record<string, Record<string, EvalDimensionScore>>;
  pairwise?: EvalPairwise;
  skipped?: boolean;
}
