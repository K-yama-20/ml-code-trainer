export interface Module {
  id: string;
  title: string;
  subtitle: string;
  color: string;
  icon: string;
}
export interface Concept {
  id: string;
  module_id: string;
  title: string;
  description: string;
  example: string;
  prerequisites: string[];
  order: number;
  problem_count?: number;
  ordered_practice?: boolean;
  problems?: Problem[];
}
export type TuplePaths = (string | number)[][];
export interface TestCase {
  setup: string;
  args: string;
  expected: unknown;
  expected_tuple_paths?: TuplePaths | null;
  comparison?: "exact" | "json" | "json_unicode" | "relative";
}
export type Stage = "guided" | "partial" | "independent";
export interface Problem {
  id: string;
  version_id: string;
  family_id: string;
  concept_id: string;
  module_id: string;
  title: string;
  description: string;
  learning_goal: string;
  input_conditions: string;
  output_conditions: string;
  stage: Stage;
  type: string;
  starter_code: string;
  editable_regions?: { start: number; end: number }[];
  example: string;
  explanation: string;
  common_mistakes: string[];
  public_tests: TestCase[];
  runtime: "browser" | "sandbox";
  packages: string[];
  required_ast: string;
  check_dtype: boolean;
  protect_inputs?: boolean;
  estimated_minutes: number;
  variant_seed: number;
  content_version: number;
  workspace?: {
    mode: "script" | "function" | "prediction";
    provided_code: string;
    task: string;
    invocation?: string;
    structure: string;
    authored: boolean;
    hint_count?: number;
  } | null;
  execution?: {
    mode: string;
    inputs?: string[];
    globals?: string[];
    entrypoint?: string;
    constant_goal?: boolean;
    allow_input_mutation?: boolean;
  } | null;
  presentation?: {
    edit_instruction: string;
    worked_example: string;
    feedback: { wrong: string; runtime: string };
    answer?: { mode: "fixed"; wrap_array: boolean };
  } | null;
}
export interface Item {
  id: string;
  session_id: string;
  problem_version_id: string;
  variant_seed: number;
  position: number;
  hint_level: number;
  solution_viewed: boolean;
  completed: boolean;
  problem?: Problem;
}
export interface StudySession {
  id: string;
  kind: string;
  status: string;
  position: number;
  items: Item[];
  goal_count?: number;
}
export interface Progress {
  concept_id: string;
  mastery_level: number;
  mastery_score: number;
  current_stage: Stage;
  stage_families: Record<string, string[]>;
  last_practiced_at: string;
  last_verified_at: string | null;
}
export interface Review {
  concept_id: string;
  due_at: string;
  interval_days: number;
  success_streak: number;
}
export interface UserSettings {
  display_name: string;
  theme: "dark" | "light" | "system";
  font_size: number;
  daily_goal: number;
  timezone: string;
}
export interface ActivityProgress {
  activity_id: string;
  question_id: string;
  accepted: boolean;
  answer: number;
}
export interface Dashboard {
  user: { id: string; display_name: string };
  settings: UserSettings;
  total_attempts: number;
  accepted: number;
  today_count: number;
  streak: number;
  study_days: number;
  weekly: { date: string; count: number }[];
  concepts: Progress[];
  reviews: Review[];
  abilities: Record<string, { attempts: number; accepted: number }>;
  activities: ActivityProgress[];
  due_count: number;
  mastered: number;
  current_session: StudySession | null;
  sandbox_available: boolean;
  auth_mode: string;
}
export interface Result {
  verdict: string;
  passed_tests: number;
  total_tests: number;
  stdout?: string;
  stderr?: string;
  elapsed_ms?: number;
  error_line?: number;
  tests?: {
    name: string;
    passed: boolean;
    error?: string;
    actual?: unknown;
    expected?: unknown;
    actual_tuple_paths?: TuplePaths | null;
    expected_tuple_paths?: TuplePaths | null;
  }[];
  code_hash?: string;
  verification_level?: string;
}
export interface Attempt {
  id: string;
  problem_version_id: string;
  item_id: string;
  session_id: string;
  submitted_code: string;
  verdict: string;
  verification_level: string;
  hint_level_used: number;
  submitted_at: string;
  result: Result;
}
export interface Question {
  id: string;
  prompt: string;
  choices: string[];
  file?: string;
  symbol?: string;
  type?: string;
}
export interface Activity {
  id: string;
  title: string;
  description: string;
  concept_id?: string;
  code?: string;
  flow?: string[];
  questions: Question[];
  library?: string;
  minutes?: number;
  entry?: string;
  files?: {
    name: string;
    code: string;
    symbols: { name: string; line: number }[];
  }[];
  line_count?: number;
}
export interface Job {
  id: string;
  status: string;
  code_hash: string;
  result: Result | null;
}
