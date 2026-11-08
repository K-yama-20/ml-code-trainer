from typing import Literal
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SessionCreate(StrictModel):
    kind: Literal["daily", "concept", "review", "custom"] = "daily"
    concept_id: str | None = None
    modules: list[str] = []
    stages: list[Literal["guided", "partial", "independent"]] = []
    count: int = Field(default=20, ge=1, le=50)


class AdvanceRequest(StrictModel):
    from_item_id: str
    skip: bool = False


class CodeRequest(StrictModel):
    item_id: str
    code: str = Field(max_length=16384)
    client_request_id: str = Field(min_length=8, max_length=100)

    @field_validator("code")
    @classmethod
    def code_bytes(cls, value):
        if len(value.encode("utf-8")) > 16384:
            raise ValueError("Code must be at most 16 KiB in UTF-8")
        return value


class ExecutionRequest(CodeRequest):
    mode: Literal["run", "submit"] = "run"


class BrowserTestResult(StrictModel):
    name: str = Field(max_length=100)
    passed: bool
    error: str | None = Field(default=None, max_length=2000)
    actual: object = None
    actual_tuple_paths: list[list[int | str]] | None = None


class BrowserResult(StrictModel):
    verdict: Literal[
        "Accepted",
        "Wrong Answer",
        "Syntax Error",
        "Runtime Error",
        "Time Limit Exceeded",
        "Execution Failed",
        "System Error",
    ]
    passed_tests: int = Field(ge=0, le=100)
    total_tests: int = Field(ge=0, le=100)
    stdout: str = Field(default="", max_length=32768)
    stderr: str = Field(default="", max_length=32768)
    elapsed_ms: float = Field(default=0, ge=0, le=3600000)
    tests: list[BrowserTestResult] | None = Field(default=None, max_length=100)


class SubmissionRequest(CodeRequest):
    browser_result: BrowserResult | None = None
    execution_id: str | None = None
    run_count: int = Field(default=0, ge=0, le=10000)


class DraftPut(StrictModel):
    code: str = Field(max_length=16384)
    revision: int = Field(ge=0)


class SettingsPatch(StrictModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=60)
    theme: Literal["dark", "light", "system"] | None = None
    font_size: int | None = Field(default=None, ge=12, le=24)
    daily_goal: int | None = Field(default=None, ge=1, le=100)
    timezone: str | None = None

    @field_validator("timezone")
    @classmethod
    def valid_zone(cls, value):
        if value:
            try:
                ZoneInfo(value)
            except ZoneInfoNotFoundError:
                raise ValueError("Unknown timezone")
        return value


class ActivityAnswer(StrictModel):
    question_id: str
    answer: int = Field(ge=0, le=20)


class ExecutionView(BaseModel):
    id: str
    status: str
    code_hash: str
    result: dict | None


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class PublicTestView(BaseModel):
    setup: str
    args: str
    expected: object
    expected_tuple_paths: list[list[int | str]] | None = None
    comparison: Literal["exact", "json", "json_unicode"] = "exact"


class ProblemView(BaseModel):
    id: str
    family_id: str
    version_id: str
    content_version: int
    concept_id: str
    module_id: str
    stage: Literal["guided", "partial", "independent"]
    type: Literal["completion", "prediction", "implementation", "bugfix"]
    difficulty: int
    title: str
    description: str
    learning_goal: str
    input_conditions: str
    output_conditions: str
    starter_code: str
    example: str
    editable_regions: list[dict]
    explanation: str
    common_mistakes: list[str]
    public_tests: list[PublicTestView]
    required_ast: str
    check_dtype: bool
    protect_inputs: bool = False
    runtime: Literal["browser", "sandbox"]
    packages: list[str]
    prerequisites: list[str]
    estimated_minutes: int
    variant_seed: int
    variant_generator: str
    tolerance: float
    presentation: dict | None = None
    workspace: dict | None = None
    execution: dict | None = None


class SessionItemView(BaseModel):
    id: str
    user_id: str
    session_id: str
    problem_version_id: str
    variant_seed: int
    position: int
    hint_level: int
    solution_viewed: bool
    completed: bool


class ItemDetailView(SessionItemView):
    problem: ProblemView


class SessionView(BaseModel):
    id: str
    user_id: str
    kind: Literal["daily", "concept", "review", "custom"]
    status: Literal["active", "paused", "completed"]
    position: int
    created_at: datetime
    updated_at: datetime
    items: list[SessionItemView]
    goal_count: int = 20


class AdvanceView(BaseModel):
    session: SessionView
    next_item_id: str | None
    message: str = ""
    reason: str | None = None


class DraftView(BaseModel):
    code: str | None
    revision: int


class SettingsView(BaseModel):
    display_name: str
    theme: Literal["dark", "light", "system"]
    font_size: int
    daily_goal: int
    timezone: str


class SubmissionView(BaseModel):
    id: str
    user_id: str
    problem_version_id: str
    session_id: str
    item_id: str
    variant_seed: int
    submitted_code: str
    verdict: str
    verification_level: Literal["browser_provisional", "server_verified"]
    passed_tests: int
    total_tests: int
    run_count: int
    hint_level_used: int
    solution_viewed: bool
    submitted_at: datetime
    client_request_id: str
    code_hash: str
    result: dict


class HistoryView(BaseModel):
    total: int
    items: list[SubmissionView]
