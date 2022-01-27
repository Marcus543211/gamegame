import inspect

from collections import namedtuple

from pygame import Vector2

from id import Id
from player import Player
from scope import Scope


class Command:
    def __init__(self, function, only_most_recent):
        parameters = inspect.signature(function).parameters
        non_scope_parameters = list(parameters)[1:]
        self._namedtuple = namedtuple(function.__name__, non_scope_parameters)
        print(self._namedtuple)

    def bind(self, *args):
        pass


class BoundCommand:
    def __init__(self, args, kwargs):
        pass

    def __call__(self, scope: Scope):
        pass


def command(function=None, *, only_most_recent=False):
    def wrapper(function):
        return Command(function, only_most_recent)

    if function:
        return wrapper(function)

    return wrapper


@command(only_most_recent=True)
def set_radius(scope: Scope, radius: float):
    scope.circle_radius = radius


@command
def set_id(scope: Scope, id_: Id):
    scope.id_ = id_


@command
def set_name(scope: Scope, id_: Id, name: str):
    scope.players[id_].name = name


@command
def remove_player(scope: Scope, id_: Id):
    del scope.players[id_]


@command(only_most_recent=True)
def set_player_position(
        scope: Scope, id_: Id, position: Vector2,
        last_acceleration: Vector2, velocity: Vector2):
    player = scope.players.setdefault(id_, Player(id_))
    player.position = position
    player.last_acceleration = last_acceleration
    player.velocity = velocity
