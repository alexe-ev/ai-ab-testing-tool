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
