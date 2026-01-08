"""
Pydantic schemas for structured LLM responses.
"""

from pydantic import BaseModel


class CharacterSchema(BaseModel):
    """Schema for a character in the world entities response."""

    name: str
    role: str
    location: str  # name of place they're in
    inventory: list[str]  # items they carry


class PlaceSchema(BaseModel):
    """Schema for a place in the world entities response."""

    name: str
    type: str
    inventory: list[str]  # items found here


class WorldEntitiesResponse(BaseModel):
    """Response schema for world entities generation."""

    characters: list[CharacterSchema]
    places: list[PlaceSchema]


class PlayerCharacterResponse(BaseModel):
    """Response schema for player character generation."""

    name: str
    skill: str
    fatal_flaw: str
    location: str  # name of place they start in
    inventory: list[str]  # starting items


class DiceRollSchema(BaseModel):
    """Schema for a dice roll result."""

    needed: bool
    result: int | None = None  # 1-20 if rolled
    success: bool | None = None


class FeasibilityResponse(BaseModel):
    """Response schema for feasibility check."""

    feasible: bool
    immediate_interruption: str | None = None
    flaw_triggered: bool
    flaw_effect: str | None = None
    dice_roll: DiceRollSchema
    initial_outcome: str  # what happens immediately


class NarrativeArcSchema(BaseModel):
    """Schema for a narrative arc."""

    name: str
    problem: str  # the core problem and situation
    stakes: str  # what the PC stands to gain or lose
    resolution_criteria: str  # how this arc can be resolved
    possible_resolutions: list[str]  # ideas for ways it could be resolved


class NarrativeArcsResponse(BaseModel):
    """Response schema for narrative arcs generation."""

    arcs: list[NarrativeArcSchema]


class ArcResolutionSchema(BaseModel):
    """Schema for a single arc's resolution status."""

    arc_name: str
    resolved: bool
    resolution_outcome: str | None = None  # how it was resolved, if resolved


class ArcResolutionResponse(BaseModel):
    """Response schema for arc resolution check."""

    resolutions: list[ArcResolutionSchema]
