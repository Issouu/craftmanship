import re
from collections import deque
import time
from copy import deepcopy

MAX_TIME = 24
MAX_TIME_THRESHOLD_FOR_CREATION = 23
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
                'obsidian': 0,
                'geode': 0
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


def prediction_useful_node(node: Node, blueprint: list, max_geodes: int, robot_type: str) -> bool:
    elapsed = node.elapsed
    inventory = deepcopy(node.inventory)
    bots = deepcopy(node.bots)
    costs = blueprint[robot_type]

    if robot_type == 'ore' and MAX_TIME <= elapsed + costs['ore']:
        return True

    if elapsed >= MAX_TIME_THRESHOLD_FOR_CREATION and robot_type != 'geode':
        return True

    if elapsed >= CLAY_ORE_THRESHOLD and (robot_type == 'clay' or robot_type == 'ore'):
        return True

    remaining_time = MAX_TIME - elapsed

    if elapsed >= GEODE_THRESHOLD:
        geode_cost = blueprint['geode']
        wait_time = maximum_wait_time(
            Node(
                inventory=inventory,
                bots=bots,
                elapsed=elapsed,
            ),
            MAX_TIME,
            geode_cost
        )
        if wait_time < remaining_time:
            inventory['geode'] += (remaining_time - wait_time - 1)

        potential_geodes = inventory['geode'] + bots['geode'] * remaining_time
        if potential_geodes <= max_geodes:
            return True


def maximum_wait_time(node: Node, costs: dict) -> int:
    return max(
        0 if node.inventory[key] >= cost
        else MAX_TIME + 1 
        if node.bots[key] == 0
        else (cost - node.inventory[key] + node.bots[key] - 1) // node.bots[key]
        for key, cost in costs.items()
    )


def max_geodes(blueprint: list) -> int:
    max_geodes = 0

    queue = deque()
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
        node = queue.popleft()
        inventory = node.inventory
        bots = node.bots
        elapsed = node.elapsed

        if elapsed == MAX_TIME:
            max_geodes = max(inventory['geode'] + bots['geode'], max_geodes)
            print("max_geodes: ", max_geodes, "\nElapsed: ", elapsed)
            continue

        for robot_type in blueprint:
            costs = blueprint[robot_type]

            if prediction_useful_node(node, blueprint, max_geodes, robot_type):
                continue

            wait_time = maximum_wait_time(node, costs)

            new_elapsed = elapsed + wait_time + 1
            if new_elapsed >= MAX_TIME:
                continue

            new_inventory = {
                key: inventory[key] + bots[key] * (wait_time + 1) - costs.get(key, 0)
                for key in inventory
            }

            new_bots = bots.copy()
            new_bots[robot_type] += 1

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
