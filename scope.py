from dataclasses import dataclass, field

from player import Player


@dataclass
class Scope:
    players: dict[tuple[str, int], Player] = field(default_factory=dict)
