"""
Data models for PEACE_COM game world.
"""

from dataclasses import dataclass, field


@dataclass
class Character:
    """An NPC in the game world."""

    name: str
    role: str  # e.g., "merchant", "enforcer", "hacker"
    location: str = ""  # name of the Place they're in
    inventory: list[str] = field(default_factory=list)  # items they carry
    initial_state: str = ""  # filled during initialization
    updates: list[str] = field(default_factory=list)


@dataclass
class Place:
    """A location in the game world."""

    name: str
    type: str  # e.g., "tavern", "market", "tunnel"
    adjacent: list[str] = field(default_factory=list)  # names of connected places
    inventory: list[str] = field(default_factory=list)  # items found here
    initial_state: str = ""  # filled during initialization
    updates: list[str] = field(default_factory=list)


@dataclass
class NarrativeArc:
    """A narrative arc representing an ongoing problem or situation in the world."""

    name: str  # brief name for the arc
    problem: str  # the core problem and situation
    stakes: str  # what the PC stands to gain or lose
    resolution_criteria: str  # how this arc can be resolved
    possible_resolutions: list[str] = field(default_factory=list)  # ideas for resolution
    resolved: bool = False
    resolution_outcome: str = ""  # how it was resolved, if resolved


@dataclass
class PlayerCharacter:
    """The player's character."""

    name: str
    skill: str
    fatal_flaw: str
    location: str = ""  # name of the Place they're in
    inventory: list[str] = field(default_factory=list)  # items they carry


@dataclass
class GameWorld:
    """The complete game world state."""

    situation: str
    characters: list[Character] = field(default_factory=list)
    places: list[Place] = field(default_factory=list)
    narrative_arcs: list[NarrativeArc] = field(default_factory=list)
    player: PlayerCharacter = None
