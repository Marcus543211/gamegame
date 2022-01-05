from dataclasses import dataclass, field
from typing import Optional

from player import Player


class Id(int):
    pass


@dataclass
class Scope:
    id_: Optional[Id] = None
    circle_radius: float = 20
    players: dict[Id, Player] = field(default_factory=dict)
