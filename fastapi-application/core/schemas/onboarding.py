from pydantic import BaseModel


class OnboardingStepRead(BaseModel):
    code: str
    title: str
    description: str
    required: bool
    completed: bool
    status: str


class OnboardingRead(BaseModel):
    user_id: int
    kyc_status: str
    progress_percent: int
    next_step: str | None = None
    steps: list[OnboardingStepRead]
