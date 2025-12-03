import time
from dataclasses import dataclass, field
from typing import List, Dict

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st


# =============================
# 1. Core Configuration
# =============================

RACE_DISTANCE: float = 200.0   # meters
DT: float = 0.1                # simulation time step
MAX_RACE_TIME: float = 40.0    # safety cap in seconds


# =============================
# 2. Data Model (same as backend)
# =============================

@dataclass
class BodySystemRunner:

    name: str
    system: str
    lane: int

    acceleration: float
    top_speed: float
    stamina_max: float
    stamina_regen: float
    burst_multiplier: float
    fatigue_factor: float

    personality: str
    ability: str

    # Dynamic race state
    position: float = 0.0
    speed: float = 0.0
    stamina: float = field(default=None)
    finished: bool = False
    finish_time: float | None = None

    def __post_init__(self) -> None:
        if self.stamina is None:
            self.stamina = self.stamina_max

    def update(self, dt: float, global_time: float, race_progress: float) -> None:
        if self.finished:
            return

        # -------------------------
        # 1. Personality-based target speed
        # -------------------------
        base_target = 0.8 * self.top_speed

        if self.personality == "aggressive":
            target_speed = min(self.top_speed, base_target + 0.15 * self.top_speed)
        elif self.personality == "calm":
            target_speed = base_target
        elif self.personality == "tactical":
            if race_progress < 0.4:
                target_speed = 0.7 * self.top_speed
            elif race_progress < 0.8:
                target_speed = 0.9 * self.top_speed
            else:
                target_speed = self.top_speed
        elif self.personality == "steady":
            target_speed = 0.85 * self.top_speed
        else:
            target_speed = base_target

        # -------------------------
        # 2. Abilities
        # -------------------------

        # Cardio
        if self.ability == "heart_engine":
            if self.speed < self.top_speed:
                self.stamina += self.stamina_regen * 1.2 * dt

        # Lungster
        if self.ability == "deep_inhale":
            if int(self.position) % 20 == 0 and self.position > 0:
                self.stamina += self.stamina_regen * 3.0 * dt

        # Flexor
        if self.ability == "power_burst":
            if race_progress < 0.25:
                target_speed = min(self.top_speed * 1.1, target_speed * 1.15)

        # Neuron
        if self.ability == "reflex_start":
            if global_time < 1.5:
                target_speed = min(self.top_speed, target_speed * 1.2)

        # Hormona
        if self.ability == "adrenaline_surge":
            if race_progress > 0.6:
                target_speed = min(self.top_speed * self.burst_multiplier,
                                   target_speed * self.burst_multiplier)

        # Gastro
        if self.ability == "energy_conversion":
            if self.stamina < 0.3 * self.stamina_max:
                target_speed = min(self.top_speed * 1.05, target_speed * 1.1)

        # Defenda & Bonestride partially handled in fatigue section

        # -------------------------
        # 3. Stamina mechanics
        # -------------------------

        speed_fraction = self.speed / self.top_speed if self.top_speed > 0 else 0.0
        drain_rate = 0.5 + 1.5 * speed_fraction

        self.stamina -= drain_rate * dt

        if speed_fraction < 0.7:
            self.stamina += self.stamina_regen * dt

        self.stamina = max(0.0, min(self.stamina, self.stamina_max))

        # -------------------------
        # 4. Fatigue
        # -------------------------

        stamina_fraction = self.stamina / self.stamina_max if self.stamina_max > 0 else 0.0
        fatigue_penalty = (1.0 - stamina_fraction) * self.fatigue_factor

        if self.ability == "fatigue_shield":
            fatigue_penalty *= 0.4

        effective_target_speed = max(0.0, target_speed * (1.0 - fatigue_penalty))

        if self.ability == "structural_stability":
            min_speed = 0.9 * 0.85 * self.top_speed
            effective_target_speed = max(min_speed, effective_target_speed)

        # -------------------------
        # 5. Move toward target speed
        # -------------------------
        if self.speed < effective_target_speed:
            self.speed += self.acceleration * dt
            if self.speed > effective_target_speed:
                self.speed = effective_target_speed
        else:
            self.speed -= self.acceleration * 1.3 * dt
            if self.speed < effective_target_speed:
                self.speed = effective_target_speed

        self.speed = max(0.0, self.speed)

        # -------------------------
        # 6. Update position
        # -------------------------

        self.position += self.speed * dt

        if self.position >= RACE_DISTANCE:
            self.position = RACE_DISTANCE
            self.finished = True
            self.finish_time = global_time


# =============================
# 3. Runner Roster
# =============================

def create_runners() -> List[BodySystemRunner]:
    return [
        BodySystemRunner(
            name="Cardio",
            system="Cardiovascular",
            lane=1,
            acceleration=3.0,
            top_speed=9.5,
            stamina_max=120.0,
            stamina_regen=12.0,
            burst_multiplier=1.1,
            fatigue_factor=0.5,
            personality="calm",
            ability="heart_engine",
        ),
        BodySystemRunner(
            name="Lungster",
            system="Respiratory",
            lane=2,
            acceleration=4.5,
            top_speed=9.4,
            stamina_max=80.0,
            stamina_regen=7.0,
            burst_multiplier=1.2,
            fatigue_factor=0.9,
            personality="aggressive",
            ability="deep_inhale",
        ),
        BodySystemRunner(
            name="Flexor",
            system="Muscular",
            lane=3,
            acceleration=4.2,
            top_speed=9.6,
            stamina_max=75.0,
            stamina_regen=6.0,
            burst_multiplier=1.3,
            fatigue_factor=1.0,
            personality="aggressive",
            ability="power_burst",
        ),
        BodySystemRunner(
            name="Neuron",
            system="Nervous",
            lane=4,
            acceleration=3.8,
            top_speed=9.2,
            stamina_max=90.0,
            stamina_regen=8.0,
            burst_multiplier=1.15,
            fatigue_factor=0.7,
            personality="tactical",
            ability="reflex_start",
        ),
        BodySystemRunner(
            name="Hormona",
            system="Endocrine",
            lane=5,
            acceleration=3.5,
            top_speed=9.7,
            stamina_max=85.0,
            stamina_regen=7.0,
            burst_multiplier=1.3,
            fatigue_factor=0.8,
            personality="tactical",
            ability="adrenaline_surge",
        ),
        BodySystemRunner(
            name="Defenda",
            system="Immune",
            lane=6,
            acceleration=2.8,
            top_speed=9.0,
            stamina_max=130.0,
            stamina_regen=11.0,
            burst_multiplier=1.05,
            fatigue_factor=0.3,
            personality="steady",
            ability="fatigue_shield",
        ),
        BodySystemRunner(
            name="Gastro",
            system="Digestive",
            lane=7,
            acceleration=3.6,
            top_speed=9.3,
            stamina_max=95.0,
            stamina_regen=8.5,
            burst_multiplier=1.2,
            fatigue_factor=0.8,
            personality="tactical",
            ability="energy_conversion",
        ),
        BodySystemRunner(
            name="Bonestride",
            system="Skeletal",
            lane=8,
            acceleration=2.4,
            top_speed=9.1,
            stamina_max=110.0,
            stamina_regen=10.0,
            burst_multiplier=1.1,
            fatigue_factor=0.6,
            personality="steady",
            ability="structural_stability",
        ),
    ]


# =============================
# 4. Simulation Engine
# =============================

def simulate_race() -> Dict[str, object]:
    runners = create_runners()
    t: float = 0.0
    frames: List[Dict[str, object]] = []

    while t < MAX_RACE_TIME and not all(r.finished for r in runners):
        avg_position = sum(r.position for r in runners) / len(runners)
        race_progress = avg_position / RACE_DISTANCE if RACE_DISTANCE > 0 else 0.0

        for r in runners:
            r.update(dt=DT, global_time=t, race_progress=race_progress)

        frame = {
            "time": t,
            "positions": [r.position for r in runners],
            "stamina": [r.stamina for r in runners],
            "speeds": [r.speed for r in runners],
        }
        frames.append(frame)

        t += DT

    return {"frames": frames, "runners": runners}


# =============================
# 5. Visualization Helpers
# =============================

def draw_frame(runners: List[BodySystemRunner], frame: Dict, player_choice: str | None = None):
    """
    Draw a single race frame in a straight 200m track with 8 lanes.
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    lane_gap = 1.2
    min_x, max_x = 0, RACE_DISTANCE

    # Draw lanes
    for r in runners:
        y = r.lane * lane_gap
        ax.hlines(y, min_x, max_x, colors="#DDDDDD", linewidth=1, linestyles="--")

    # Finish line
    ax.vlines(RACE_DISTANCE, lane_gap * 0.5, lane_gap * 8.5,
              colors="black", linewidth=2, linestyles="-")

    # Plot runners
    for idx, r in enumerate(runners):
        pos = frame["positions"][idx]
        y = r.lane * lane_gap

        size = 80
        edgecolor = "black"
        linewidth = 1.5

        if player_choice and r.name == player_choice:
            size = 120
            edgecolor = "gold"
            linewidth = 3.0

        ax.scatter(pos, y, s=size, c=r.system_color, edgecolors=edgecolor, linewidths=linewidth)

        ax.text(pos + 1.0, y + 0.1, r.name, fontsize=8, va="bottom")

    ax.set_xlim(min_x - 5, max_x + 10)
    ax.set_ylim(lane_gap * 0.5, lane_gap * 8.8)
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Lanes (1–8)")
    ax.set_title(f"Body Systems Race — t = {frame['time']:.1f} s")
    ax.set_yticks([])
    ax.grid(False)
    plt.tight_layout()
    st.pyplot(fig)


# We patch a color attribute onto runners here for visuals only
SYSTEM_COLORS = {
    "Cardiovascular": "#E53935",
    "Respiratory": "#1E88E5",
    "Muscular": "#FFB300",
    "Nervous": "#8E24AA",
    "Endocrine": "#F4511E",
    "Immune": "#43A047",
    "Digestive": "#FB8C00",
    "Skeletal": "#546E7A",
}


def attach_colors(runners: List[BodySystemRunner]) -> None:
    for r in runners:
        # attach system_color dynamically
        r.system_color = SYSTEM_COLORS.get(r.system, "#000000")


# =============================
# 6. Streamlit UI
# =============================

def main():
    st.set_page_config(page_title="Body Systems Race", layout="wide")

    st.title("🏃‍♂️ Body Systems Race — 200m Medical Sprint Simulation")
    st.write(
        "Each runner represents a body system with unique physiology and race personality. "
        "Watch how their abilities influence the 200m sprint."
    )

    # For highlighting only; the simulation itself recreates runners
    sample_runners = create_runners()
    system_names = [r.name for r in sample_runners]

    player_choice = st.selectbox(
        "Choose your body system runner:",
        options=system_names,
        index=0,
        help="This runner will be highlighted during the race.",
    )

    if st.button("Start Race"):
        st.write("Simulating race...")

        sim_result = simulate_race()
        frames = sim_result["frames"]
        final_runners = sim_result["runners"]
        attach_colors(final_runners)

        placeholder = st.empty()

        # Animate
        for frame in frames:
            with placeholder.container():
                draw_frame(final_runners, frame, player_choice=player_choice)
            time.sleep(0.05)

        # Results
        st.subheader("🏁 Final Results")

        runners = sim_result["runners"]

        def sort_key(r: BodySystemRunner) -> float:
            return r.finish_time if r.finish_time is not None else 1e9

        ordered = sorted(runners, key=sort_key)

        table_data = []
        for idx, r in enumerate(ordered, start=1):
            time_str = f"{r.finish_time:.2f} s" if r.finish_time is not None else "DNF"
            table_data.append({
                "Place": idx,
                "Runner": r.name,
                "System": r.system,
                "Finish Time": time_str,
                "Personality": r.personality,
                "Ability": r.ability,
            })

        st.table(table_data)
    else:
        st.markdown("Press **Start Race** to run a full 200m simulation.")


if __name__ == "__main__":
    main()