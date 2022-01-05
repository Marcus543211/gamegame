from dataclasses import dataclass, field
from typing import Optional

from id import Id
from player import Player


@dataclass
class Scope:
    id_: Optional[Id] = None
    circle_radius: float = 20
    players: dict[Id, Player] = field(default_factory=dict)
