from typing import Optional
from pydantic import BaseModel, Field

class CharacterProfile(BaseModel):
    name: str = Field(description="The name of the character")
    age: Optional[int] = Field(default=None, description="The age of the character. Use None if not specified in the book.")
    gender: Optional[str] = Field(default=None, description="The gender of the character. Use None if not specified in the book.")
    sex: Optional[str] = Field(default=None, description="The sex of the character. Use None if not specified in the book.")
    race: Optional[str] = Field(default=None, description="The race of the character. Use None if not specified in the book.")
    occupation: Optional[str] = Field(default=None, description="The occupation of the character. Use None if not specified in the book.")
    personality: str = Field(default="", description="The personality of the character")
    appearance: str = Field(default="", description="The appearance of the character")
    backstory: str = Field(default="", description="The backstory of the character")
    relationships: list[str] = Field(default_factory=list, description="The relationships of the character")
    goals: list[str] = Field(default_factory=list, description="The goals of the character")
    motivations: list[str] = Field(default_factory=list, description="The motivations of the character")

class CharacterList(BaseModel):
    """A list of characters identified from the book, categorized as main or side."""
    main_characters: list[str] = Field(..., description="A list of names of the main characters.")
    side_characters: list[str] = Field(..., description="A list of names of the side characters.")