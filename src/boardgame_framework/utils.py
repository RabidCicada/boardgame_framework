"""
This module provide miscellaneous support for the boardgame_framework
"""
import logging
import pathlib
from . import cell
from enum import Enum, IntEnum
from dataclasses import dataclass
from numpy import ndarray

logger = logging.getLogger(__name__)

def checkallequal(iteratable):
    iterator = iter(iteratable)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == rest for rest in iterator)

def a_star_search(cells, start, goal, hasJump=False, hasFlying=False):
    # assert our locations exist
    assert graph.getTileByMapCoordinates(start)
    assert graph.getTileByMapCoordinates(goal)

    frontier = PriorityQueue()

    start_tile = graph.getTileByMapCoordinates(start)
    goal_tile = graph.getTileByMapCoordinates(goal)
    frontier.put(start_tile, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0

    while not frontier.empty():
        current_tile = frontier.get()

        if current_tile == goal_tile:
            break

        current = current_tile.getMapLocation()
        for next in current_tile.getMapNeighbors():
            next_tile = graph.getTileByMapCoordinates(next)
            if next_tile and next_tile.isPassable():
                new_cost = cost_so_far[current] + next_tile.costToEnter(graph.difficulty, hasJump, hasFlying)
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + heuristic(goal, next)
                    frontier.put(next_tile, priority)
                    came_from[next] = current

    #return came_from
    current = goal
    path = []
    while current != start:
       path.append(current)
       current = came_from[current]
    path.append(start) # optional
    path.reverse() # optional
    return path, cost_so_far[goal]
