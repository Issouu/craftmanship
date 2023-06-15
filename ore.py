import re
from collections import deque
import time
from copy import deepcopy

MAX_TIME_THRESHOLD = 23
CLAY_ORE_THRESHOLD = 22
GEODE_THRESHOLD = 21


def parse_blueprint(lines: list) -> list:
    processed = []
    for line in lines:
        blueprint_number = int(re.search('Blueprint (\\d+?):', line).group(1))
        ore_robot_ore_cost = int(re.search('Each ore robot costs (\\d+?) ore.', line).group(1))
        clay_robot_ore_cost = int(re.search('Each clay robot costs (\\d+?) ore.', line).group(1))
        obsidian_robot_ore_cost = int(re.search('Each obsidian robot costs (\\d+?) ore', line).group(1))
        obsidian_robot_clay_cost = int(
            re.search('Each obsidian robot costs \\d+ ore and (\\d+?) clay.', line).group(1))
        geode_robot_ore_cost = int(
            re.search('Each geode robot costs (\\d+?) ore', line).group(1))
        geode_robot_obsidian_cost = int(
            re.search('Each geode robot costs \\d+ ore and (\\d+?) obsidian.', line).group(1))
        cost = {
            'ore': {
                'ore': ore_robot_ore_cost, 
                'clay': 0, 
                'obsidian': 0, 
                'geode': 0
            },
            'clay': {
                'ore': clay_robot_ore_cost,
                'clay': 0, 
                'obsidian': 0, 
                'geode': 0
            },
            'obsidian': {
                'ore': obsidian_robot_ore_cost, 
                'clay': obsidian_robot_clay_cost, 
                'obsidian': 0, 'geode': 0
            },
            'geode': {
                'ore': geode_robot_ore_cost, 
                'clay': 0, 
                'obsidian': geode_robot_obsidian_cost, 
                'geode': 0
            }
        }
        processed.append((blueprint_number, cost))
    return processed


def read_file_to_list(path: str) -> list:
    with open(path, 'r', encoding='utf-8') as fileinput:
        return fileinput.readlines()


class Node:

    def __init__(self, inventory, bots, elapsed):
        self.inventory = inventory
        self.bots = bots
        self.elapsed = elapsed


def prediction_stop(state, max_time, blueprint, max_geodes, costs, blueprint_item):
    elapsed = state.elapsed
    inventory = deepcopy(state.inventory)
    bots = deepcopy(state.bots)

    if blueprint_item == 'ore' and max_time <= elapsed + costs['ore']:
        return True

    if elapsed >= MAX_TIME_THRESHOLD and blueprint_item != 'geode':
        return True

    if elapsed >= CLAY_ORE_THRESHOLD and (blueprint_item == 'clay' or blueprint_item == 'ore'):
        return True

    remaining_time = max_time - elapsed

    if elapsed >= GEODE_THRESHOLD:
        geode_cost = blueprint['geode']
        wait_time = maximum_wait_time(
            Node(
                inventory=inventory,
                bots=bots,
                elapsed=elapsed,
            ),
            max_time,
            geode_cost
        )
        if wait_time < remaining_time:
            inventory['geode'] += (remaining_time - wait_time - 1)

        potential_geodes = inventory['geode'] + bots['geode'] * remaining_time
        if potential_geodes <= max_geodes:
            return True


def maximum_wait_time(state, max_time, costs):
    return max(
        0 if state.inventory[key] >= cost
        else max_time + 1 if state.bots[key] == 0
        else (cost - state.inventory[key] + state.bots[key] - 1) // state.bots[key]
        for key, cost in costs.items()
    )


def max_geodes(blueprint):
    max_time = 24
    max_geodes = 0

    queue = deque()  # Initialize a queue for breadth-first search
    queue.append(
        Node(
            inventory = {
                'ore': 0,
                'clay': 0,
                'obsidian': 0,
                'geode': 0
            },
            bots = {
                'ore': 1,
                'clay': 0,
                'obsidian': 0,
                'geode': 0
            },
            elapsed=0,
    ))

    while queue:
        state = queue.popleft()  # Take the next state from the queue
        inventory = state.inventory
        bots = state.bots
        elapsed = state.elapsed

        if elapsed == max_time:
            # Update the maximum number of geodes if the current count is higher
            max_geodes = max(inventory['geode'] + bots['geode'], max_geodes)
            print("max_geodes: ", max_geodes, "\nElapsed: ", elapsed)
            continue

        for blueprint_item in blueprint:
            costs = blueprint[blueprint_item]

            if prediction_stop(state, max_time, blueprint, max_geodes, costs, blueprint_item):
                continue

            wait_time = maximum_wait_time(state, max_time, costs)

            new_elapsed = elapsed + wait_time + 1
            if new_elapsed >= max_time:
                continue

            new_inventory = {
                key: inventory[key] + bots[key] * (wait_time + 1) - costs.get(key, 0)
                for key in inventory
            }

            new_bots = bots.copy()
            new_bots[blueprint_item] += 1

            queue.append(Node(
                inventory=new_inventory,
                bots=new_bots,
                elapsed=new_elapsed,
            ))

        geodes = inventory['geode'] + bots['geode']
        max_geodes = max(geodes, max_geodes)

    return max_geodes


if __name__ == '__main__':
    file_input = read_file_to_list(path='input_ore.txt')
    blueprints = parse_blueprint(file_input)
    sum_found_geodes = 0
    sum_time = 0
    for blueprint_number, blueprint in blueprints:
        start_time = time.time()
        max_geode = max_geodes(blueprint)
        sum_found_geodes += blueprint_number * max_geode
        print("max_geodes: ", max_geode)
        end_time = time.time()
        sum_time += end_time - start_time
        print("Time: ", end_time - start_time)
    print("Final score: ", sum_found_geodes)
    print("Final time: ", sum_time)
