import json
import random
import os
from datetime import datetime, timezone

GARDEN_WIDTH = 40
GARDEN_HEIGHT = 16

# Plant types and their growth stages (each stage = one run)
PLANTS = {
    "flower": {
        "stages": [".", ",", "|", "φ", "✿"],
        "weight": 35,
    },
    "tree": {
        "stages": [".", ",", "↑", "↟", "♣", "♣"],
        "weight": 20,
    },
    "grass": {
        "stages": [".", "'", '"', "⌇"],
        "weight": 25,
    },
    "mushroom": {
        "stages": [".", "○", "♨"],
        "weight": 10,
    },
    "vine": {
        "stages": [".", "~", "≈", "❋"],
        "weight": 10,
    },
}

CRITTERS = ["ᘛ", "⌘", "Ƹ", "ȣ", "✦", "∞"]

WEATHER = [
    ("☀️  Clear skies", 0.3),
    ("🌤  Partly cloudy", 0.2),
    ("☁️  Overcast", 0.15),
    ("🌧  Light rain", 0.15),
    ("⛈  Thunderstorm", 0.05),
    ("🌈  Rainbow!", 0.05),
    ("🌙  Moonlit night", 0.1),
]

STATE_FILE = "garden_state.json"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "day": 0,
        "plants": [],
        "critters": [],
        "history": [],
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def pick_plant_type():
    types = list(PLANTS.keys())
    weights = [PLANTS[t]["weight"] for t in types]
    return random.choices(types, weights=weights, k=1)[0]


def get_empty_cells(state):
    occupied = {(p["x"], p["y"]) for p in state["plants"]}
    empty = []
    for y in range(GARDEN_HEIGHT):
        for x in range(GARDEN_WIDTH):
            if (x, y) not in occupied:
                empty.append((x, y))
    return empty


def grow_garden(state):
    state["day"] += 1
    events = []

    # Grow existing plants
    grown = 0
    for plant in state["plants"]:
        stages = PLANTS[plant["type"]]["stages"]
        if plant["stage"] < len(stages) - 1:
            # Not all plants grow every cycle -- adds natural variation
            if random.random() < 0.7:
                plant["stage"] += 1
                grown += 1

    if grown > 0:
        events.append(f"{grown} plant(s) grew")

    # Plant new seeds (1-4 per run, fewer as garden fills)
    empty = get_empty_cells(state)
    fill_ratio = 1 - (len(empty) / (GARDEN_WIDTH * GARDEN_HEIGHT))
    max_new = max(1, int(4 * (1 - fill_ratio)))
    num_new = random.randint(1, max_new)

    if empty:
        num_new = min(num_new, len(empty))
        new_cells = random.sample(empty, num_new)
        for x, y in new_cells:
            plant_type = pick_plant_type()
            state["plants"].append({
                "type": plant_type,
                "x": x,
                "y": y,
                "stage": 0,
            })
        events.append(f"{num_new} seed(s) planted")

    # Random critter placement (temporary, just for this render)
    state["critters"] = []
    if random.random() < 0.4:
        critter_cells = get_empty_cells(state)
        if critter_cells:
            cx, cy = random.choice(critter_cells)
            state["critters"].append({
                "type": random.choice(CRITTERS),
                "x": cx,
                "y": cy,
            })
            events.append("a critter visited!")

    # Pick weather
    weather_options, weather_weights = zip(*WEATHER)
    weather = random.choices(weather_options, weights=weather_weights, k=1)[0]

    return events, weather


def render_garden(state, weather):
    grid = [[" " for _ in range(GARDEN_WIDTH)] for _ in range(GARDEN_HEIGHT)]

    # Place plants
    for plant in state["plants"]:
        stages = PLANTS[plant["type"]]["stages"]
        char = stages[plant["stage"]]
        grid[plant["y"]][plant["x"]] = char

    # Place critters
    for critter in state["critters"]:
        grid[critter["y"]][critter["x"]] = critter["type"]

    # Count stats
    total_plants = len(state["plants"])
    mature = sum(
        1 for p in state["plants"]
        if p["stage"] == len(PLANTS[p["type"]]["stages"]) - 1
    )
    type_counts = {}
    for p in state["plants"]:
        type_counts[p["type"]] = type_counts.get(p["type"], 0) + 1

    # Build the output
    border_top = "┌" + "─" * (GARDEN_WIDTH + 2) + "┐"
    border_bot = "└" + "─" * (GARDEN_WIDTH + 2) + "┘"

    lines = []
    lines.append(border_top)
    for row in grid:
        lines.append("│ " + "".join(row) + " │")
    lines.append(border_bot)

    garden_art = "\n".join(lines)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    readme = f"""# 🌱 ASCII Garden

A self-growing garden, tended by a bot. Every 8 hours, new seeds are planted and existing plants grow.

**Day {state['day']}** · {weather} · {total_plants} plants · {mature} fully grown

```
{garden_art}
```

## Census
| Type | Count | Stages |
|------|-------|--------|
| 🌸 Flower | {type_counts.get('flower', 0)} | `. , | φ ✿` |
| 🌳 Tree | {type_counts.get('tree', 0)} | `. , ↑ ↟ ♣` |
| 🌿 Grass | {type_counts.get('grass', 0)} | `. ' " ⌇` |
| 🍄 Mushroom | {type_counts.get('mushroom', 0)} | `. ○ ♨` |
| 🌿 Vine | {type_counts.get('vine', 0)} | `. ~ ≈ ❋` |

*Last tended: {now}*
*This garden grows automatically via GitHub Actions.*
"""
    return readme


def main():
    state = load_state()
    events, weather = grow_garden(state)
    readme = render_garden(state, weather)

    with open("README.md", "w") as f:
        f.write(readme)

    save_state(state)

    print(f"Day {state['day']}: {', '.join(events)}")
    print(f"Weather: {weather}")
    print(f"Total plants: {len(state['plants'])}")


if __name__ == "__main__":
    main()
