import inspect

from pygame import Vector2

from id import Id
from player import Player
from scope import Scope


def command(function=None, *, only_most_recent=False):
    def wrapper(function):
        parameters = inspect.signature(function).parameters
        non_scope_parameters = list(parameters)[1:]
        print(non_scope_parameters)
        return function

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
