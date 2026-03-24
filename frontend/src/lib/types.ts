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

export interface ExperimentListItem {
  id: string;
  name: string;
  description: string;
  hypothesis: string;
  run_count: number;
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
