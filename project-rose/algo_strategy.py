from tkinter.messagebox import NO
from wsgiref.simple_server import demo_app
import gamelib
import random
import math
import warnings
from sys import maxsize
import json


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
        self.broken_wall_locations = []
        self.upgrades = []
        self.support_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write(
            "Performing turn {} of your custom algo strategy".format(
                game_state.turn_number
            )
        )
        game_state.suppress_warnings(
            True
        )  # Comment or remove this line to enable warnings.

        self.strategy(game_state)

        game_state.submit_turn()

    def setup_base(self, game_state):
        turrets = [
            [1, 12],
            [21, 11],
            [25, 12],
            [26, 12],
            [21, 9],
        ]
        walls = [
            [0, 13],
            [1, 13],
            [26, 13],
            [27, 13],
            [22, 12],
            [23, 12],
            [24, 12],
            [2, 11],
            [3, 10],
            [4, 9],
            [20, 9],
            [5, 8],
            [19, 8],
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
            [21, 12],
        ]
        # todo: upgrade walls if they take damage. not for highschool comp.
        self.upgrades = [
            [25, 12],
            [21, 11],
            [1, 12],
            [21, 12],
            [20, 8],
            [19, 7],
            [18, 8],
            [17, 8],
        ]
        self.removals = [
            [0, 13],
            [1, 13],
            [26, 13],
            [27, 13],
        ]
        self.support_locations = [
            [20, 8],
            [19, 7],
            [17, 6],
            [18, 6],
            [17, 5],
            [16, 4],
        ]
        game_state.attempt_spawn(TURRET, turrets)
        game_state.attempt_spawn(WALL, walls)
        game_state.attempt_spawn(SUPPORT, self.support_locations)
        game_state.attempt_upgrade(self.upgrades)
        game_state.attempt_remove(self.removals)
        # todo: remove everything that's not upgraded. especially walls

    def strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """

        # self.build_reactive_defense(game_state)
        # todo: get the walls that take damage and have them upgrade themselves. put all this reactive stuff in its own function
        # todo: upgrade more of the walls
        # game_state.attempt_spawn(TURRET, self.broken_wall_locations)
        self.upgrades += self.broken_wall_locations

        # Getting the defense setup initially. Copied from the #1 ranked dude as of 06/10/22
        self.setup_base(game_state)
        self.reactive_demo(game_state)
        # todo: check if after the cost of building the wall we will have enough sp, then upgrade turrets and other damaged walls

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base

        """ if game_state.turn_number % 3 == 1:
            # Now let's analyze the enemy base to see where their defenses are concentrated.
            # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            if (
                self.detect_enemy_unit(
                    game_state, unit_type=None, valid_x=None, valid_y=[14, 15]
                )
                > 10
            ):
                self.reactive_demo(game_state)
            else:
                # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

                # Only spawn Scouts every other turn
                # Sending more at once is better since attacks can only hit a single scout at a time

                # To simplify we will just check sending them from back left and right
                scout_spawn_location_options = [[13, 0], [14, 0]]
                best_location = self.least_damage_spawn_location(
                    game_state, scout_spawn_location_options
                )
                game_state.attempt_spawn(SCOUT, best_location, 1000)

                # Lastly, if we have spare SP, let's build some supports
                support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
                game_state.attempt_spawn(SUPPORT, support_locations) """

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

    def reactive_demo(self, game_state):
        # If they have their attack line at y = 14
        if (
            self.detect_enemy_unit(
                game_state, unit_type=None, valid_x=None, valid_y=[14]
            )
            > 10
        ):
            self.demolisher_line_strategy(game_state, 11)  # hardcoded vals
            # have to remove the walls at y = 12
            # todo: find best place to have funnel
        elif (
            self.detect_enemy_unit(
                game_state, unit_type=None, valid_x=None, valid_y=[15]
            )
            > 10
        ):
            self.demolisher_line_strategy(game_state, 12)
        # If they have their attack line at y = 16
        elif (
            self.detect_enemy_unit(
                game_state, unit_type=None, valid_x=None, valid_y=[16]
            )
            > 10
        ):
            self.demolisher_line_strategy(game_state, 13)
        # If they don't have a lot of units on the board
        elif (
            self.detect_enemy_unit(
                game_state, unit_type=None, valid_x=None, valid_y=None
            )
            < 15
        ):
            # spam scouts
            pass
        elif (
            self.detect_enemy_unit(
                game_state, unit_type=None, valid_x=list(range(0, 14)), valid_y=None
            )
            < 8
        ):
            # send demos to the left
            pass
        else:
            # send demos to the right
            pass

    def demolisher_line_strategy(self, game_state, y_val):
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

        # todo: check that we can afford this attack before we actually do it
        if (
            game_state.get_resource(MP)
            > gamelib.GameUnit(DEMOLISHER, game_state.config).cost[game_state.MP] * 3
            and game_state.get_resource(SP) > 22
        ):

            for x in range(27, 4, -1):
                game_state.attempt_spawn(cheapest_unit, [x, y_val])
                # game_state.attempt_remove([x, y_val])

            # Now spawn demolishers next to the line
            # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
            # todo: check that we can spawn 3+ at a time... they're somewhat ineffective if we cant
            game_state.attempt_spawn(DEMOLISHER, [15, 1], 1000)

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
        # damage_on_me = [l for l in events["death"] if (l[3] == 1) and l[1] < 3]
        broken_walls = [l for l in events["death"] if l[3] == 1 and l[1] == 0]
        [self.broken_wall_locations.append(l[0]) for l in broken_walls]
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


# todo: parse turnstring for next move
""" {
    "p2Units": [
        [
            [0, 14, 75.0, "40"],
            [3, 15, 35.0, "41"],
            [22, 16, 75.0, "42"],
            [21, 16, 75.0, "43"],
            [20, 16, 75.0, "44"],
            [19, 16, 75.0, "45"],
            [18, 16, 75.0, "46"],
            [17, 16, 75.0, "47"],
            [16, 16, 75.0, "48"],
            [15, 16, 75.0, "49"],
            [14, 16, 75.0, "50"],
            [13, 16, 75.0, "51"],
            [12, 16, 75.0, "52"],
            [11, 16, 75.0, "53"],
            [10, 16, 75.0, "54"],
            [9, 16, 75.0, "55"],
            [8, 16, 75.0, "56"],
            [7, 16, 75.0, "57"],
            [6, 16, 75.0, "58"],
            [5, 16, 35.0, "59"],
            [4, 16, 35.0, "60"],
            [27, 14, 150.0, "67"],
            [26, 14, 150.0, "76"],
            [25, 14, 150.0, "83"],
            [23, 14, 150.0, "84"],
            [2, 14, 150.0, "85"],
            [1, 14, 150.0, "92"],
        ],
        [],
        [
            [26, 15, 90.0, "61"],
            [23, 15, 90.0, "63"],
            [2, 15, 90.0, "64"],
            [25, 16, 90.0, "65"],
            [23, 16, 90.0, "66"],
            [3, 16, 90.0, "74"],
            [16, 17, 90.0, "75"],
            [11, 17, 90.0, "82"],
            [25, 15, 90.0, "91"],
        ],
        [],
        [],
        [],
        [],
        [
            [27, 14, 0.0, "67"],
            [26, 14, 0.0, "76"],
            [25, 14, 0.0, "83"],
            [23, 14, 0.0, "84"],
            [2, 14, 0.0, "85"],
            [25, 15, 0.0, "91"],
            [1, 14, 0.0, "92"],
        ],
    ],
    "turnInfo": [1, 3, 26, 343],
    "p1Stats": [40.0, 14.0, 0.0, 6],
    "p1Units": [
        [
            [0, 13, 75.0, "5"],
            [26, 13, 75.0, "8"],
            [27, 13, 75.0, "9"],
            [2, 11, 75.0, "10"],
            [3, 10, 75.0, "12"],
            [21, 10, 75.0, "13"],
            [4, 9, 75.0, "14"],
            [20, 9, 75.0, "15"],
            [5, 8, 75.0, "16"],
            [19, 8, 75.0, "17"],
            [6, 7, 75.0, "18"],
            [7, 7, 75.0, "19"],
            [8, 7, 75.0, "20"],
            [10, 7, 75.0, "21"],
            [11, 7, 75.0, "22"],
            [12, 7, 75.0, "23"],
            [13, 7, 75.0, "24"],
            [14, 7, 75.0, "25"],
            [15, 7, 75.0, "26"],
            [16, 7, 75.0, "27"],
            [17, 7, 75.0, "28"],
            [18, 7, 75.0, "29"],
            [9, 6, 75.0, "30"],
            [1, 13, 150.0, "31"],
            [21, 11, 150.0, "32"],
            [23, 13, 81.0, "33"],
        ],
        [],
        [[25, 13, 39.0, "2"], [1, 12, 90.0, "3"], [22, 11, 90.0, "4"]],
        [],
        [],
        [
            [18, 4, 40.0, "93"],
            [16, 3, 40.0, "94"],
            [14, 5, 40.0, "95"],
            [13, 6, 40.0, "96"],
            [16, 3, 40.0, "97"],
        ],
        [],
        [[1, 13, 0.0, "31"], [21, 11, 0.0, "32"], [23, 13, 0.0, "33"]],
    ],
    "p2Stats": [40.0, 0.0, 0.7, 6],
    "events": {
        "selfDestruct": [
            [[24, 14], [[24, 13], [25, 13], [23, 13]], 15.0, 3, "101", 2],
            [[24, 14], [[23, 13], [24, 13], [25, 13]], 15.0, 3, "102", 2],
            [[24, 14], [[25, 13], [23, 13], [24, 13]], 15.0, 3, "103", 2],
        ],
        "breach": [],
        "damage": [
            [[24, 13], 15.0, 2, "73", 1],
            [[25, 13], 15.0, 2, "2", 1],
            [[23, 13], 15.0, 0, "33", 1],
            [[23, 13], 15.0, 0, "33", 1],
            [[24, 13], 15.0, 2, "73", 1],
            [[25, 13], 15.0, 2, "2", 1],
            [[25, 13], 15.0, 2, "2", 1],
            [[23, 13], 15.0, 0, "33", 1],
            [[24, 13], 15.0, 2, "73", 1],
            [[25, 13], 2.0, 2, "2", 1],
            [[25, 13], 2.0, 2, "2", 1],
            [[25, 13], 2.0, 2, "2", 1],
        ],
        "shield": [],
        "move": [],
        "spawn": [],
        "death": [
            [[24, 14], 3, "101", 2, false],
            [[24, 13], 2, "73", 1, false],
            [[24, 14], 3, "102", 2, false],
            [[24, 14], 3, "103", 2, false],
        ],
        "attack": [
            [[24, 14], [25, 13], 2.0, 3, "101", "2", 2],
            [[24, 14], [25, 13], 2.0, 3, "102", "2", 2],
            [[24, 14], [25, 13], 2.0, 3, "103", "2", 2],
        ],
        "melee": [],
    },
} """
