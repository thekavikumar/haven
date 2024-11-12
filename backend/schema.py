from typing import Optional

from pydantic import BaseModel


class PostInfo(BaseModel):
    name: str
    phone: str
    location: str
    duration_of_abuse: str
    frequency_of_incidents: str
    preferred_contact_method: str
    current_situation: str
    culprit_description: str
    custom_text: Optional[str] = None
