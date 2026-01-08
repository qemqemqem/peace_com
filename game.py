"""
Core game logic for PEACE_COM.
"""

import json

from config import QUIT_COMMANDS
from prompts import (
    SYSTEM_PROMPT,
    SITUATION_PROMPT,
    WORLD_ENTITIES_PROMPT,
    ENTITY_STATE_PROMPT,
    PLAYER_CHARACTER_PROMPT,
    OPENING_MESSAGE_PROMPT,
    FEASIBILITY_PROMPT,
    TIME_ESTIMATE_PROMPT,
    CHARACTER_SIMULATION_PROMPT,
    PLACE_SIMULATION_PROMPT,
    NARRATIVE_ARCS_PROMPT,
    ARC_RESOLUTION_PROMPT,
)
from llm import get_response, get_structured_response
from models import Character, Place, PlayerCharacter, GameWorld, NarrativeArc
from schemas import (
    WorldEntitiesResponse,
    PlayerCharacterResponse,
    FeasibilityResponse,
    NarrativeArcsResponse,
    ArcResolutionResponse,
)
from ui import (
    print_title,
    print_separator,
    print_response,
    print_goodbye,
    get_input,
)


def print_dev(label: str, content: str):
    """Print development/debug information."""
    print(f"\n[DEV] {label}")
    print("-" * 40)
    print(content)
    print("-" * 40)


def initialize_world() -> GameWorld:
    """Initialize the game world through the 5-step LLM flow."""

    # Step 1: Generate the situation
    print("\n[Generating situation...]")
    situation_messages = [{"role": "user", "content": SITUATION_PROMPT}]
    situation = get_response(situation_messages)
    print_dev("SITUATION", situation)

    # Step 2: Generate characters and places
    print("\n[Generating characters and places...]")
    entities_prompt = WORLD_ENTITIES_PROMPT.format(situation=situation)
    entities_messages = [{"role": "user", "content": entities_prompt}]
    entities_data = get_structured_response(entities_messages, WorldEntitiesResponse)

    places = [
        Place(name=p.name, type=p.type, inventory=list(p.inventory))
        for p in entities_data.places
    ]
    characters = [
        Character(
            name=c.name,
            role=c.role,
            location=c.location,
            inventory=list(c.inventory),
        )
        for c in entities_data.characters
    ]

    print_dev(
        "PLACES",
        "\n".join(
            f"- {p.name} ({p.type}) [items: {', '.join(p.inventory) or 'none'}]"
            for p in places
        ),
    )
    print_dev(
        "CHARACTERS",
        "\n".join(
            f"- {c.name} ({c.role}) @ {c.location} [items: {', '.join(c.inventory) or 'none'}]"
            for c in characters
        ),
    )

    # Step 3: Get initial states for each entity
    print("\n[Generating initial states...]")
    for character in characters:
        state_prompt = ENTITY_STATE_PROMPT.format(
            situation=situation,
            entity_type="CHARACTER",
            name=character.name,
            role_or_type=character.role,
        )
        state_messages = [{"role": "user", "content": state_prompt}]
        character.initial_state = get_response(state_messages)
        print_dev(f"STATE: {character.name}", character.initial_state)

    for place in places:
        state_prompt = ENTITY_STATE_PROMPT.format(
            situation=situation,
            entity_type="PLACE",
            name=place.name,
            role_or_type=place.type,
        )
        state_messages = [{"role": "user", "content": state_prompt}]
        place.initial_state = get_response(state_messages)
        print_dev(f"STATE: {place.name}", place.initial_state)

    # Step 4: Generate player character
    print("\n[Generating player character...]")
    places_list = "\n".join(f"- {p.name}" for p in places)
    pc_prompt = PLAYER_CHARACTER_PROMPT.format(
        situation=situation,
        places_list=places_list,
    )
    pc_messages = [{"role": "user", "content": pc_prompt}]
    pc_data = get_structured_response(pc_messages, PlayerCharacterResponse)

    player = PlayerCharacter(
        name=pc_data.name,
        skill=pc_data.skill,
        fatal_flaw=pc_data.fatal_flaw,
        location=pc_data.location,
        inventory=list(pc_data.inventory),
    )
    print_dev(
        "PLAYER CHARACTER",
        f"Name: {player.name}\n"
        f"Skill: {player.skill}\n"
        f"Fatal Flaw: {player.fatal_flaw}\n"
        f"Location: {player.location}\n"
        f"Inventory: {', '.join(player.inventory) or 'none'}",
    )

    # Step 5: Generate narrative arcs
    print("\n[Generating narrative arcs...]")
    arcs_prompt = NARRATIVE_ARCS_PROMPT.format(
        situation=situation,
        player_name=player.name,
        player_skill=player.skill,
        player_flaw=player.fatal_flaw,
    )
    arcs_messages = [{"role": "user", "content": arcs_prompt}]
    arcs_data = get_structured_response(arcs_messages, NarrativeArcsResponse)

    narrative_arcs = [
        NarrativeArc(
            name=arc.name,
            problem=arc.problem,
            stakes=arc.stakes,
            resolution_criteria=arc.resolution_criteria,
            possible_resolutions=list(arc.possible_resolutions),
        )
        for arc in arcs_data.arcs
    ]

    for arc in narrative_arcs:
        print_dev(
            f"NARRATIVE ARC: {arc.name}",
            f"Problem: {arc.problem}\n"
            f"Stakes: {arc.stakes}\n"
            f"Resolution: {arc.resolution_criteria}\n"
            f"Ideas: {', '.join(arc.possible_resolutions)}",
        )

    # Create the world object
    world = GameWorld(
        situation=situation,
        characters=characters,
        places=places,
        narrative_arcs=narrative_arcs,
        player=player,
    )

    return world


def check_feasibility(world: GameWorld, player_action: str) -> FeasibilityResponse:
    """Check if the player's action is feasible and get initial outcome."""
    world_context = build_world_context(world)
    prompt = FEASIBILITY_PROMPT.format(
        world_context=world_context,
        player_action=player_action,
        fatal_flaw=world.player.fatal_flaw,
    )
    messages = [{"role": "user", "content": prompt}]
    return get_structured_response(messages, FeasibilityResponse)


def estimate_time(player_action: str) -> str:
    """Ask the LLM how long the player's action will take."""
    prompt = TIME_ESTIMATE_PROMPT.format(player_action=player_action)
    messages = [{"role": "user", "content": prompt}]
    return get_response(messages).strip()


def simulate_time_passage(world: GameWorld, time_elapsed: str) -> None:
    """Simulate what each character and place does during the time period."""
    print_dev("TIME ELAPSED", time_elapsed)

    # Simulate each character
    for character in world.characters:
        current_state = character.initial_state
        if character.updates:
            current_state = character.updates[-1]

        prompt = CHARACTER_SIMULATION_PROMPT.format(
            situation=world.situation,
            name=character.name,
            role=character.role,
            location=character.location,
            current_state=current_state,
            time_elapsed=time_elapsed,
        )
        messages = [{"role": "user", "content": prompt}]
        update = get_response(messages).strip()
        character.updates.append(f"[{time_elapsed}] {update}")
        print_dev(f"CHARACTER UPDATE: {character.name}", update)

    # Simulate each place
    for place in world.places:
        current_state = place.initial_state
        if place.updates:
            current_state = place.updates[-1]

        prompt = PLACE_SIMULATION_PROMPT.format(
            situation=world.situation,
            name=place.name,
            type=place.type,
            current_state=current_state,
            time_elapsed=time_elapsed,
        )
        messages = [{"role": "user", "content": prompt}]
        update = get_response(messages).strip()
        place.updates.append(f"[{time_elapsed}] {update}")
        print_dev(f"PLACE UPDATE: {place.name}", update)


def build_arcs_summary(world: GameWorld) -> str:
    """Build a summary of active (unresolved) narrative arcs."""
    active_arcs = [arc for arc in world.narrative_arcs if not arc.resolved]
    if not active_arcs:
        return "No active narrative arcs."
    
    lines = []
    for arc in active_arcs:
        lines.append(
            f"- {arc.name}\n"
            f"  Problem: {arc.problem}\n"
            f"  Stakes: {arc.stakes}\n"
            f"  Resolution criteria: {arc.resolution_criteria}"
        )
    return "\n".join(lines)


def check_arc_resolution(
    world: GameWorld, player_action: str, outcome: str
) -> list[NarrativeArc]:
    """Check if any narrative arcs have been resolved by the player's action."""
    active_arcs = [arc for arc in world.narrative_arcs if not arc.resolved]
    if not active_arcs:
        return []

    world_context = build_world_context(world)
    arcs_summary = build_arcs_summary(world)

    prompt = ARC_RESOLUTION_PROMPT.format(
        world_context=world_context,
        player_action=player_action,
        outcome=outcome,
        arcs_summary=arcs_summary,
    )
    messages = [{"role": "user", "content": prompt}]
    resolution_data = get_structured_response(messages, ArcResolutionResponse)

    resolved_arcs = []
    for resolution in resolution_data.resolutions:
        if resolution.resolved:
            # Find and update the matching arc
            for arc in world.narrative_arcs:
                if arc.name == resolution.arc_name and not arc.resolved:
                    arc.resolved = True
                    arc.resolution_outcome = resolution.resolution_outcome or ""
                    resolved_arcs.append(arc)
                    print_dev(
                        f"ARC RESOLVED: {arc.name}",
                        arc.resolution_outcome,
                    )
                    break

    return resolved_arcs


def build_character_summary(character: Character) -> str:
    """Build a summary string for a character including updates."""
    base = f"- {character.name} ({character.role}) @ {character.location} [has: {', '.join(character.inventory) or 'nothing'}]: {character.initial_state}"
    if character.updates:
        updates_str = "\n    ".join(character.updates)
        base += f"\n    RECENT: {updates_str}"
    return base


def build_place_summary(place: Place) -> str:
    """Build a summary string for a place including updates."""
    base = f"- {place.name} ({place.type}) [contains: {', '.join(place.inventory) or 'nothing'}]: {place.initial_state}"
    if place.updates:
        updates_str = "\n    ".join(place.updates)
        base += f"\n    RECENT: {updates_str}"
    return base


def build_world_context(world: GameWorld) -> str:
    """Build a context string from the world state for the system prompt."""
    characters_summary = "\n".join(
        build_character_summary(c) for c in world.characters
    )
    places_summary = "\n".join(
        build_place_summary(p) for p in world.places
    )

    return f"""
CURRENT SITUATION:
{world.situation}

PLAYER CHARACTER:
Name: {world.player.name}
Skill: {world.player.skill}
Fatal Flaw: {world.player.fatal_flaw}
Location: {world.player.location}
Inventory: {', '.join(world.player.inventory) or 'nothing'}

KEY CHARACTERS:
{characters_summary}

NOTABLE LOCATIONS:
{places_summary}
"""


def create_session(world: GameWorld) -> list[dict]:
    """Create a new game session with message history."""
    world_context = build_world_context(world)
    full_system_prompt = SYSTEM_PROMPT + "\n\n" + world_context
    return [{"role": "system", "content": full_system_prompt}]


def refresh_session(messages: list[dict], world: GameWorld) -> None:
    """Refresh the system message with updated world state."""
    world_context = build_world_context(world)
    full_system_prompt = SYSTEM_PROMPT + "\n\n" + world_context
    messages[0] = {"role": "system", "content": full_system_prompt}


def generate_opening(world: GameWorld) -> str:
    """Generate the opening message for the player."""
    characters_summary = "\n".join(
        f"- {c.name} ({c.role}) @ {c.location} [has: {', '.join(c.inventory) or 'nothing'}]: {c.initial_state}"
        for c in world.characters
    )
    places_summary = "\n".join(
        f"- {p.name} ({p.type}) [contains: {', '.join(p.inventory) or 'nothing'}]: {p.initial_state}"
        for p in world.places
    )

    opening_prompt = OPENING_MESSAGE_PROMPT.format(
        situation=world.situation,
        player_name=world.player.name,
        player_skill=world.player.skill,
        player_flaw=world.player.fatal_flaw,
        player_location=world.player.location,
        player_inventory=", ".join(world.player.inventory) or "nothing",
        characters_summary=characters_summary,
        places_summary=places_summary,
    )

    messages = [{"role": "user", "content": opening_prompt}]
    return get_response(messages)


def run_game():
    """Run the main game loop."""
    print_title()

    # Initialize the world
    world = initialize_world()

    # Create session with world context
    messages = create_session(world)

    # Step 5: Generate and show opening message
    print("\n[Generating opening scene...]")
    print_separator()
    opening = generate_opening(world)
    messages.append({"role": "assistant", "content": opening})
    print_response(opening)

    # Main game loop
    while True:
        print_separator()

        user_input = get_input()

        if not user_input:
            continue

        if user_input.lower() in QUIT_COMMANDS:
            print_goodbye()
            break

        messages.append({"role": "user", "content": user_input})

        # Step 1: Check feasibility and get initial outcome
        print("\n[Checking feasibility...]")
        feasibility = check_feasibility(world, user_input)
        print_dev("FEASIBILITY CHECK", 
            f"Feasible: {feasibility.feasible}\n"
            f"Interruption: {feasibility.immediate_interruption}\n"
            f"Flaw triggered: {feasibility.flaw_triggered} ({feasibility.flaw_effect})\n"
            f"Dice: {feasibility.dice_roll}\n"
            f"Initial outcome: {feasibility.initial_outcome}"
        )

        # Show initial outcome to player immediately
        print_response(feasibility.initial_outcome)

        # Step 2: Estimate how long this action takes
        print("\n[Estimating time...]")
        time_elapsed = estimate_time(user_input)

        # Step 3: Simulate world during that time
        print("\n[Simulating world...]")
        simulate_time_passage(world, time_elapsed)

        # Step 4: Check if any narrative arcs are resolved
        print("\n[Checking arc resolution...]")
        resolved_arcs = check_arc_resolution(
            world, user_input, feasibility.initial_outcome
        )

        # Step 5: Refresh session with updated world state
        refresh_session(messages, world)

        # Build context for final response including feasibility results
        feasibility_context = f"""
WHAT JUST HAPPENED:
- Player attempted: {user_input}
- Initial outcome: {feasibility.initial_outcome}
- Time elapsed: {time_elapsed}
- Feasible: {feasibility.feasible}
"""
        if feasibility.immediate_interruption:
            feasibility_context += f"- Interruption: {feasibility.immediate_interruption}\n"
        if feasibility.flaw_triggered:
            feasibility_context += f"- Flaw triggered ({world.player.fatal_flaw}): {feasibility.flaw_effect}\n"
        if feasibility.dice_roll.needed:
            feasibility_context += f"- Dice roll: {feasibility.dice_roll.result} ({'success' if feasibility.dice_roll.success else 'failure'})\n"
        if resolved_arcs:
            for arc in resolved_arcs:
                feasibility_context += f"- ARC RESOLVED [{arc.name}]: {arc.resolution_outcome}\n"

        # Add feasibility context as a system message for the final response
        messages.append({"role": "system", "content": feasibility_context})

        # For dev
        with open("messages_dump.json", "w") as f:
            json.dump(messages, f, indent=2)
        print("[DEV] Messages dumped to messages_dump.json")

        print("==========\nMESSAGES\n==========")
        for message in messages:
            print(f"{message['role']}: {message['content'][:100]}...")
        print("==========\n")

        # Step 6: Generate final response with all context
        response = get_response(messages)
        messages.append({"role": "assistant", "content": response})

        print_response(response)
