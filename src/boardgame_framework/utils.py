"""
This module provide miscellaneous support for the boardgame_framework
"""
import logging
import pathlib
from . import cell
from enum import Enum, IntEnum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

def checkallequal(iteratable):
    iterator = iter(iteratable)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == rest for rest in iterator)


# Incomplete
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

def flood_fill(coord, dirs, check_validity, color, fill_callback=None):
    print(f"Flood Filling starting at ({coord})")
    #here check_validity is a function that given coordinates of the point tells you whether
    #the point should be colored or not
    q = list()
    seen = list()
    q.append(coord)
    seen.append(coord)
    while (q):
        coord = q.pop()
        #print(f"ff->({coord})")
        color(coord)

        if fill_callback:
            fill_callback(coord)

        for d in dirs:
            newcoord = coord+d
            if (check_validity(newcoord)):
                if newcoord not in seen:
                    q.append(newcoord)
                    seen.append(newcoord)

# Input: img
# Output: resultImg
# 1 padImg ← pad img with background color;
# 2 seed ← (0,0);
# 3 padImg ← floodfill(padImg, seed) with label color;
# 4 for x in range(padImg.height) do
# ; // Main Filling Process
# 5 for y in range(padImg.width) do
# 6 if padImg[x][y] == background color then
# 7 seed ← (x,y), i ← 1;
# 8 while padImg[x][y-i] == boundary color
# do
# 9 i ← i + 1;
# 10 if padImg[x][y-i] == boundary color then
# 11 floodfill(padImg, seed) with filling
# color;
# 12 if resultImg[x][y] == exterior label color then
# 13 resultImg[x][y] ← background color;
# 14 else
# 15 floodfill(padImg, seed) with label color;
# 16 croppedImg ← crop padImg to original size, delete
# padding;
# ; // Crop-and-‘Inverse’ process
# 17 resultImg ← croppedImg;
# 18 for x in range(resultImg.height) do
# 19 for y in range(resultImg.width) do
# 20 if resultImg[x][y] == exterior label color then
# 21 resultImg[x][y] ← background color;
# 22 if resultImg[x][y] == interior label color then
# 23 resultImg[x][y] ← mask color;


# def scaff(CellMgr):
#
#
#     #Skip padding image because we rely on retrieval giving us "empty/exterior" values for padding cells
#
#     curr_coord = (0,0)
#
#     flood_fill(,curr_coord)
