import re
from collections import deque
import time
from copy import deepcopy

def process_blueprint(lines: list) -> list:
    """
    Processes a list of blueprint lines and extracts relevant information.

    Args:
        lines (list): A list of blueprint lines.

    Returns:
        list: A list of tuples containing the blueprint ID and its associated cost dictionary.
              Each tuple has the format (bid, cost), where:
              - bid (int): The blueprint ID.
              - cost (dict): The cost dictionary representing 
                the resources required for the blueprint.
                
                The cost dictionary has the following structure:
                {
                    'ore': {'ore': ore_ore, 'clay': 0, 'obsidian': 0, 'geode': 0},
                    'clay': {'ore': clay_ore, 'clay': 0, 'obsidian': 0, 'geode': 0},
                    'obsidian': {'ore': obsidian_ore, 'clay': obsidian_clay, 'obsidian': 0, 'geode': 0},
                    'geode': {'ore': geode_ore, 'clay': 0, 'obsidian': geode_obsidian, 'geode': 0}
                }
                
                where:
                - ore_ore (int): The cost of each ore robot in ore units.
                - clay_ore (int): The cost of each clay robot in ore units.
                - obsidian_ore (int): The cost of each obsidian robot in ore units.
                - obsidian_clay (int): The cost of each obsidian robot in clay units.
                - geode_ore (int): The cost of each geode robot in ore units.
                - geode_obsidian (int): The cost of each geode robot in obsidian units.
    """
    processed = []
    for line in lines:
        bid = int(re.search('Blueprint (\\d+?):', line).group(1))
        ore_ore = int(re.search('Each ore robot costs (\\d+?) ore.', line).group(1))
        clay_ore = int(re.search('Each clay robot costs (\\d+?) ore.', line).group(1))
        obsidian_ore = int(re.search('Each obsidian robot costs (\\d+?) ore', line).group(1))
        obsidian_clay = int(
            re.search('Each obsidian robot costs \\d+ ore and (\\d+?) clay.', line).group(1))
        geode_ore = int(
            re.search('Each geode robot costs (\\d+?) ore', line).group(1))
        geode_obsidian = int(
            re.search('Each geode robot costs \\d+ ore and (\\d+?) obsidian.', line).group(1))
        cost = {
            'ore': {'ore': ore_ore, 'clay': 0, 'obsidian': 0, 'geode': 0},
            'clay': {'ore': clay_ore, 'clay': 0, 'obsidian': 0, 'geode': 0},
            'obsidian': {'ore': obsidian_ore, 'clay': obsidian_clay, 'obsidian': 0, 'geode': 0},
            'geode': {'ore': geode_ore, 'clay': 0, 'obsidian': geode_obsidian, 'geode': 0}
        }
        processed.append((bid, cost))
    return processed

def read_file_to_list(path: str) -> list:
    """
    Reads a file and returns its content as a list of lines.

    Args:
        path (str): The path to the file.

    Returns:
        list: A list containing the lines of the file.

    Raises:
        FileNotFoundError: If the specified file path does not exist.
        IOError: If there is an error while reading the file.

    Note:
        This function assumes that the file is encoded in UTF-8 format.
        If the file has a different encoding, specify the appropriate encoding
        using the `encoding` parameter when calling the `open` function.
    """
    with open(path, 'r', encoding='utf-8') as fileinput:
        return fileinput.readlines()

class State:
    """
    Represents the state of the tree node.

    Args:
        inventory (dict): A dict of items in the inventory.
        bots (dict): A dict of bots in the system.
        elapsed (float): The elapsed time since the system started.

    Attributes:
        inventory (dict): A dict of items in the inventory.
        bots (dict): A dict of bots in the system.
        elapsed (float): The elapsed time since the system started.

    """
    def __init__(self, inventory, bots, elapsed):
        self.inventory = inventory
        self.bots = bots
        self.elapsed = elapsed

def prediction_stop(state, max_time, blueprint, max_geodes, costs, blueprint_item):
    """
    Determines whether the node should be pruned based on the current state and conditions.

    Args:
        state (State): The current state of the tree node.
        max_time (float): The maximum time allowed for the prediction.
        blueprint (dict): The blueprint containing crafting recipes.
        max_geodes (int): The maximum number of geodes at the given time.
        costs (dict): The costs associated with crafting items.
        blueprint_item (str): The item being crafted in the blueprint.

    Returns:
        bool: True if the node should be pruned, False otherwise.

    """
    elapsed = state.elapsed
    inventory = deepcopy(state.inventory)
    bots = deepcopy(state.bots)
    
    # Prune if the remaining time is not enough to complete the blueprint item 'ore'
    if blueprint_item == 'ore' and max_time <= elapsed + costs['ore']:
        return True
    
    # Prune if the elapsed time has reached 23 and the blueprint item is not 'geode'
    if elapsed >= 23 and blueprint_item != 'geode':
        return True
    
    # Prune if the elapsed time has reached 22 and the blueprint item is either 'clay' or 'ore'
    if elapsed >= 22 and (blueprint_item == 'clay' or blueprint_item == 'ore'):
        return True

    remaining_time = max_time - elapsed
    
    # Check conditions after 21 elapsed time
    # Check if the remaining time is enough to craft the blueprint item 'geode'
    # After checking if the 'geode' robot can be crafted, make a prediction on the number of geodes that can be collected in the remaining time
    # If the number of geodes collected is less than the maximum number of geodes, prune the node
    # Since it is impossible to collect the maximum number of geodes
    if elapsed >= 21:
        geode_cost = blueprint['geode']
        wait_time = maximum_wait_time(State(
            inventory=inventory,
            bots=bots,
            elapsed=elapsed,
        ), max_time, geode_cost)
        if wait_time < remaining_time:
            inventory['geode'] += (remaining_time - wait_time - 1)
                
        potential_geodes = inventory['geode'] + bots['geode'] * remaining_time
        if potential_geodes <= max_geodes:
            return True
    

def maximum_wait_time(state, max_time, costs):
    """
    Calculates the maximum wait time to craft the robots defined by costs based on the current state, maximum time.

    Args:
        state (State): The current state of the system.
        max_time (float): The maximum time allowed for the prediction.
        costs (dict): The costs associated with crafting items.

    Returns:
        int: The maximum wait time.

    """
    return max(
        0 if (state.inventory[key] >= cost)  # If inventory has enough items, wait time is 0
        else max_time + 1 if (state.bots[key] == 0)  # If no bots available, wait time is max_time + 1
        else (cost - state.inventory[key] + state.bots[key] - 1) // state.bots[key]  # Calculate wait time based on the difference between inventory and bots
        for key, cost in costs.items()  # Iterate over each key and cost in the costs dictionary
    )

def max_geodes(blueprint):
    """
    Calculates the maximum number of geodes obtainable based on the provided blueprint.

    Args:
        blueprint (dict): The blueprint containing crafting recipes.

    Returns:
        int: The maximum number of geodes obtainable.

    """
    max_time = 24  # Maximum time allowed for the prediction
    max_geodes = 0  # Maximum number of geodes obtained

    q = deque()  # Initialize a queue for breadth-first search
    q.append(State(
        inventory={'ore': 0, 'clay': 0, 'obsidian': 0, 'geode': 0},
        bots={'ore': 1, 'clay': 0, 'obsidian': 0, 'geode': 0},
        elapsed=0,
    ))

    while q:
        state = q.popleft()  # Take the next state from the queue
        inventory = state.inventory
        bots = state.bots
        elapsed = state.elapsed

        # Check if the elapsed time has reached the maximum time
        if elapsed == max_time:
            # Update the maximum number of geodes if the current count is higher
            max_geodes = max(inventory['geode'] + bots['geode'], max_geodes)
            print("max_geodes: ", max_geodes, "\nElapsed: ", elapsed)
            continue

        for blueprint_item in blueprint:
            costs = blueprint[blueprint_item]

            # Check if the node should be pruned based on prediction_stop conditions
            if prediction_stop(state, max_time, blueprint, max_geodes, costs, blueprint_item):
                continue
            # Check if the remaining time is enough to craft the blueprint item
            # If not, prune the node
            wait_time = maximum_wait_time(state, max_time, costs)

            # Calculate the new elapsed time after crafting the item and waiting for the bots to finish
            # Exemple : If the elapsed time is 10 and the wait time is 3, the new elapsed time is 14
            # The new elapsed time is 14 because the item is crafted at time 10 and the bots finish at time 13
            new_elapsed = elapsed + wait_time + 1
            if new_elapsed >= max_time:
                continue

            # Calculate the new inventory after crafting the item
            # Exemple : If the inventory has 2 'ore' and the bots have 3 'ore', the new inventory will have 5 'ore'
            new_inventory = {
                key: inventory[key] + bots[key] * (wait_time + 1) - costs.get(key, 0)
                for key in inventory
            }

            new_bots = bots.copy()
            new_bots[blueprint_item] += 1  # Increment the count of bots for the crafted item

            # Add the new state to the queue for further exploration
            # The new state is the state after crafting the item and waiting for the bots to finish
            q.append(State(
                inventory=new_inventory,
                bots=new_bots,
                elapsed=new_elapsed,
            ))
            
        # Calculate the number of geodes collected at the end of the simulation
        geodes = inventory['geode'] + bots['geode']

        # Update the maximum number of geodes if the current count is higher
        max_geodes = max(geodes, max_geodes)

    return max_geodes

if __name__ == '__main__':
    file_input = read_file_to_list(path='input_ore.txt')
    blueprints = process_blueprint(file_input)
    final = 0
    final_time = 0
    for bid,blueprint in blueprints:
        start_time = time.time()
        max_geode = max_geodes(blueprint)
        final += bid * max_geode
        print("max_geodes: ", max_geode)
        end_time = time.time()
        final_time += end_time - start_time
        print("Time: ", end_time - start_time)
    print("Final score: ", final)
    print("Final time: ", final_time)