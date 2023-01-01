import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write("Random seed: {}".format(seed))

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write("Configuring your custom algo strategy...")
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write(
            "Performing turn {} of your custom algo strategy".format(
                game_state.turn_number
            )
        )
        game_state.suppress_warnings(
            True
        )  # Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()

    def starter_strategy(self, game_state):

        self.build_defences(game_state)
        if (
            self.detect_enemy_unit(
                game_state, unit_type=None, valid_x=None, valid_y=[14, 15]
            )
            > 10
        ):
            # self.demolisher_line_strategy(game_state)
            pass
        else:
            if game_state.turn_number % 2 == 1:
                # To simplify we will just check sending them from back left and right
                scout_spawn_location_options = [[13, 0], [14, 0]]
                best_location = self.least_damage_spawn_location(
                    game_state, scout_spawn_location_options
                )
                game_state.attempt_spawn(SCOUT, best_location, 1000)

            # Lastly, if we have spare SP, let's build some supports
            support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
            game_state.attempt_spawn(SUPPORT, support_locations)

    def build_defences(self, game_state):
        self.step0d(game_state)
        self.step1d(game_state)
        self.step2d(game_state)
        if game_state.turn_number > 4:
            self.fix_damaged_defenses(game_state)
        self.step3d(game_state)
        self.step4d(game_state)
        self.step5d(game_state)

    def fix_damaged_defenses(self, game_state):
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 0 and unit.health < unit.max_health * 0.8:
                        game_state.attempt_remove(location)

    def step5d(self, game_state):
        turrets = [
            [23, 9],
            [22, 8],
        ]
        walls = [
            [23, 10],
            [22, 9],
        ]

        game_state.attempt_spawn(WALL, walls)
        game_state.attempt_spawn(TURRET, turrets)

    def step4d(self, game_state):
        upgrades = [
            [3, 13],
            [25, 13],
            [6, 13],
            [21, 12],
        ]
        walls = [
            [5, 10],
            [24, 11],
        ]
        turrets = [
            [24, 10],
        ]
        game_state.attempt_upgrade(upgrades)
        game_state.attempt_spawn(WALL, walls)
        game_state.attempt_spawn(TURRET, turrets)

    def step3d(self, game_state):
        upgrades = [
            [0, 13],
            [1, 13],
            [26, 13],
            [27, 13],
        ]
        walls = [
            [3, 10],
            [4, 13],
            [5, 13],
            [4, 10],
            [8, 9],
            [7, 13],
            [7, 12],
            [7, 11],
            [7, 10],
            [17, 8],
            [16, 8],
            [15, 8],
            [14, 8],
            [13, 8],
            [12, 8],
            [11, 8],
            [10, 8],
            [9, 8],
            [20, 11],
            [19, 10],
        ]

        game_state.attempt_upgrade(upgrades)
        game_state.attempt_spawn(WALL, walls)

    def step2d(self, game_state):
        walls = [
            [0, 13],
            [1, 13],
            [2, 13],
            [25, 13],
            [26, 13],
            [27, 13],
        ]

        game_state.attempt_spawn(WALL, walls)

    def step1d(self, game_state):
        walls = [
            [18, 9],
        ]
        upgrades = [
            [18, 8],
        ]

        game_state.attempt_spawn(WALL, walls)
        game_state.attempt_upgrade(upgrades)

    def step0d(self, game_state):
        turrets = [
            [3, 12],
            [6, 12],
            [21, 11],
            [25, 12],
            [18, 8],
        ]
        walls = [
            [3, 13],
            [6, 13],
            [21, 12],
            [25, 13],
        ]
        upgrades = [
            [3, 12],
            [6, 12],
            [21, 11],
            [25, 12],
        ]

        game_state.attempt_spawn(TURRET, turrets)
        game_state.attempt_spawn(WALL, walls)
        game_state.attempt_upgrade(upgrades)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1] + 1]
            game_state.attempt_spawn(TURRET, build_location)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(
            game_state.game_map.BOTTOM_LEFT
        ) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)

        # While we have remaining MP to spend lets send out interceptors randomly.
        while (
            game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP]
            and len(deploy_locations) > 0
        ):
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]

            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if (
                unit_class.cost[game_state.MP]
                < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]
            ):
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += (
                    len(game_state.get_attackers(path_location, 0))
                    * gamelib.GameUnit(TURRET, game_state.config).damage_i
                )
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if (
                        unit.player_index == 1
                        and (unit_type is None or unit.unit_type == unit_type)
                        and (valid_x is None or location[0] in valid_x)
                        and (valid_y is None or location[1] in valid_y)
                    ):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                self.scored_on_locations.append(location)


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
