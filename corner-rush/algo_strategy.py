from xmlrpc.client import boolean
import gamelib
import random
import math
import warnings
from sys import maxsize
import json

# keywords: note, todo, test
# note: changes in unit.py: changed the upgrade function so that self.health is actually updated

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

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
        self.corner_bool = False

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        """ gamelib.debug_write(
            "Performing turn {} of your custom algo strategy".format(
                game_state.turn_number
            )
        ) """
        game_state.suppress_warnings(
            True
        )  # Comment or remove this line to enable warnings.

        self.strategy(game_state)

        game_state.submit_turn()

    def y_val_demo_check(self, game_state, y) -> bool:
        return False
        return self.detect_enemy_unit(
            game_state, unit_type=None, valid_x=None, valid_y=[y]
        ) in range(
            10, 17
        )  # test

    def attack(self, game_state):
        self.corner_scout_attack(game_state)

        if game_state.turn_number < 5:
            self.stall_with_interceptors(game_state)
        else:
            self.replace_damaged_walls(game_state)
            if game_state.turn_number % 4 != 1:
                pass
            else:
                if self.y_val_demo_check(game_state, 14):
                    self.demolisher_line_strategy(game_state, 11)
                elif self.y_val_demo_check(game_state, 15):
                    self.demolisher_line_strategy(game_state, 12)
                elif self.y_val_demo_check(game_state, 16):
                    self.demolisher_line_strategy(game_state, 13)
                else:
                    self.corner_bool = True
                    self.corner_attack_prep(game_state)
                if False:
                    # To simplify we will just check sending them from back left and right
                    scout_spawn_location_options = [[13, 0], [14, 0]]
                    best_location = self.least_damage_spawn_location(
                        game_state, scout_spawn_location_options
                    )
                    game_state.attempt_spawn(SCOUT, best_location, 1000)

    def strategy(self, game_state):
        self.attack(game_state)
        self.build_defences(game_state)

        # Lastly, if we have spare SP, let's build some supports
        # todo: these aren't really effective rn
        support_locations = [
            [10, 5],
            [11, 5],
            [12, 5],
            [13, 5],
            [14, 5],
            [15, 5],
            [16, 5],
            [17, 5],
            [11, 4],
            [12, 4],
            [13, 4],
            [14, 4],
            [15, 4],
            [16, 4],
            [12, 3],
            [13, 3],
            [14, 3],
            [15, 3],
            [13, 2],
            [14, 2],
            [13, 1],
            [14, 1],
        ]
        game_state.attempt_spawn(SUPPORT, support_locations)
        game_state.attempt_upgrade(support_locations)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [
            [1, 12],
            [19, 9],
            [20, 9],
            [7, 6],
            [17, 6],
            [18, 6],
        ]
        attack_turrets = [
            [25, 11],
            [26, 12],
        ]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)
        if not self.corner_bool:
            game_state.attempt_spawn(TURRET, attack_turrets)
        # Place walls in front of turrets to soak up damage for them
        first_walls = [
            [0, 13],
            [1, 13],
            [2, 12],
            [2, 11],
            [3, 10],
            [19, 10],
            [20, 10],
            [21, 10],
            [22, 10],
        ]
        wall_locations = [
            [4, 9],
            [5, 8],
            [6, 7],
            [7, 7],
            [8, 7],
            [9, 7],
            [10, 7],
            [11, 7],
            [12, 7],
            [13, 7],
            [14, 7],
            [15, 7],
            [16, 7],
            [17, 7],
            [18, 7],
            [19, 7],
        ]
        attack_walls = [
            [23, 10],
            [24, 11],
            [25, 12],
            [26, 13],
            [27, 13],
        ]
        upgrades = [
            [0, 13],
            [1, 13],
            [26, 13],
            [27, 13],
            [1, 12],
            [25, 11],
            [19, 9],
            [20, 9],
            [7, 6],
            [17, 6],
            [18, 6],
            [25, 12],
            [19, 10],
            [20, 10],
            [7, 7],
            [17, 7],
            [18, 7],
        ]

        # todo: it'd be great if scouts could be slowed down a little more
        game_state.attempt_spawn(WALL, first_walls)
        if not self.corner_bool:
            game_state.attempt_spawn(WALL, attack_walls)
        game_state.attempt_spawn(WALL, wall_locations)
        # todo: should dot some turrets in the middle of the U
        # upgrade walls so they soak more damage
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

    # todo: need those supports much quicker. they're very powerful. stall with interceptors if SP is not accumulating fast enough. the interceptors are better defendors than the turrets. sending 14 supports out w/o shields is a waste
    # todo: don't really need to spawn 4+ once initial defences are set up
    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(
            game_state.game_map.BOTTOM_LEFT
        ) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        locations = [
            [12, 1],
            [13, 0],
            [14, 0],
            [17, 3],
        ]

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        game_state.attempt_spawn(INTERCEPTOR, locations, 1)

        # While we have remaining MP to spend lets send out interceptors randomly.
        while (
            game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP]
            and len(deploy_locations) > 0
        ):
            # Choose a random deploy location.
            """deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]"""

            # todo: this is slower than the random one for some reason? my guess is because i'm passing a 2d array vs singular tuples
            # losing some randomly placed units if they're blocked in. just cause a unit can be placed on the edge doesn't mean they can get out
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def corner_attack_prep(self, game_state):
        removals = [
            [23, 10],
            [24, 11],
            [25, 11],
            [25, 12],
            [26, 12],
            [26, 13],
            [27, 13],
        ]
        game_state.attempt_remove(removals)

    def corner_scout_attack(self, game_state):
        if self.corner_bool:
            wall_additions = [
                [19, 8],
                [23, 12],
                [24, 12],
                [25, 13],
                [9, 6],
            ]
            turret_additions = [23, 11]
            all_upgrades = [
                [23, 11],
                [23, 12],
            ]
            game_state.attempt_spawn(WALL, wall_additions)
            game_state.attempt_spawn(TURRET, turret_additions)
            game_state.attempt_upgrade(all_upgrades)
            self.corner_bool = False
            game_state.attempt_spawn(
                SCOUT, [9, 4], round(game_state.get_resource(MP) / 3)
            )
            game_state.attempt_spawn(SCOUT, [8, 5], 1000)
            game_state.attempt_remove(wall_additions)
            game_state.attempt_remove(turret_additions)

    def demolisher_line_strategy(self, game_state, yval):
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
        # todo: change y level based on their defenses

        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, yval])
            game_state.attempt_remove([x, yval])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        # todo: spawn them in larger groups, 1 or 2 at a time are not super effective
        # todo: they don't get support shields even if there are support towers
        game_state.attempt_spawn(DEMOLISHER, [12, 1], 1000)

    # todo: a better attack might be spamming scouts down the edges
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

    def replace_damaged_walls(self, game_state):
        # todo: consider upgrading first since that doesn't have a 1 turn delay
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if (
                        unit.player_index == 0 and unit.health < unit.max_health * 0.8
                    ):  # they have bugs in their
                        game_state.attempt_remove(location)
                    """ if location == [7, 6]:
                        gamelib.debug_write(f"{unit.health}, {unit.max_health}") """

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
        with open("outgamestate.txt", "w") as f:
            f.write(str(state))
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                # gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                """ gamelib.debug_write(
                    "All locations: {}".format(self.scored_on_locations)
                ) """


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
