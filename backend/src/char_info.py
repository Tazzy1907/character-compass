from pydantic import BaseModel, Field

class CharacterProfile(BaseModel):
    name: str = Field(description="The name of the character")
    age: int = Field(description="The age of the character")
    gender: str = Field(description="The gender of the character")
    sex: str = Field(description="The sex of the character")
    race: str = Field(description="The race of the character")
    occupation: str = Field(description="The occupation of the character")
    personality: str = Field(description="The personality of the character")
    appearance: str = Field(description="The appearance of the character")
    backstory: str = Field(description="The backstory of the character")
    relationships: list[str] = Field(description="The relationships of the character")
    goals: list[str] = Field(description="The goals of the character")
    motivations: list[str] = Field(description="The motivations of the character")