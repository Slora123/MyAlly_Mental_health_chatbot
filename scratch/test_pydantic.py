from pydantic import BaseModel
from typing import Optional

class OnboardingRequest(BaseModel):
    nickname: Optional[str] = None
    gender: Optional[str] = None

    class Config:
        extra = "allow"

req = OnboardingRequest(**{"nickname": "Slora", "phone": "12345", "birthday": "2000-01-01"})
print("Normal dump:", req.model_dump())
print("Exclude unset:", req.model_dump(exclude_unset=True))
