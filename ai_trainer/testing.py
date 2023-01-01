import numpy
import pygad
import pickle

### TOURNAMENT RUNNER ###

### GAME PLAYER ###
def play_game(model1, model2):
    with open("../model_1s_folder/modelpickle.pkl", "wb") as f:
        pickle.dump(model1, f)
    with open("../model_2s_folder/modelpickle.pkl", "wb") as f:
        pickle.dump(model2, f)
    # play the game and record the winner


#######################
"""recap: so this might work, it's going to be a massive model though. what next needs to be done is implement the usage of the model into terminals thing. so the way I was considering going about that was dumping the models to be used in a folder, then when called algo_stratehy.py will load that pickle file, having imported pygad, and the model can predict there. those predictions don't really matter to us here. once predictions have been made the move will be done, and all we have to do is do that for both, then record the winner. using the winner info, we can run the tournament, and create a reference list, so that fitness will be assigned based on that list: so we run this tournament once, then when assigning the fitness we just look it up in the chart... where the winners of the competition have the highest fitness and the biggest losers have the lowest fitness"""
########################


### FITNESS FUNCTION ###
def fitness_func(solution, sol_idx):
    global GANN_instance, data_inputs, data_outputs

    predictions = pygad.nn.predict(
        last_layer=GANN_instance.population_networks[sol_idx], data_inputs=data_inputs
    )
    correct_predictions = numpy.where(predictions == data_outputs)[0].size
    solution_fitness = (correct_predictions / data_outputs.size) * 100

    return solution_fitness


### GENERATION STEP ###
def callback_generation(ga_instance):
    global GANN_instance, last_fitness

    population_matrices = pygad.gann.population_as_matrices(
        population_networks=GANN_instance.population_networks,
        population_vectors=ga_instance.population,
    )

    GANN_instance.update_population_trained_weights(
        population_trained_weights=population_matrices
    )

    print(
        "Generation = {generation}".format(generation=ga_instance.generations_completed)
    )
    print("Fitness = {fitness}".format(fitness=ga_instance.best_solution()[1]))
    print(
        "Change = {change}".format(change=ga_instance.best_solution()[1] - last_fitness)
    )

    last_fitness = ga_instance.best_solution()[1].copy()


# Holds the fitness value of the previous generation.
last_fitness = 0

# Optional step of filtering the input data using the standard deviation.
features_STDs = numpy.std(a=data_inputs, axis=0)
data_inputs = data_inputs[:, features_STDs > 50]

# The length of the input vector for each sample (i.e. number of neurons in the input layer).
num_inputs = data_inputs.shape[1]
# The number of neurons in the output layer (i.e. number of classes).
num_classes = 4

# Creating an initial population of neural networks. The return of the initial_population() function holds references to the networks, not their weights. Using such references, the weights of all networks can be fetched.
num_solutions = 8  # A solution or a network can be used interchangeably.

GANN_instance = pygad.gann.GANN(
    num_solutions=512,
    num_neurons_input=4374,
    num_neurons_output=1092,
    num_neurons_hidden_layers=[4800, 3800, 3000, 2200, 1300],
    output_activation="None",
    hidden_activations="relu",
)


""" GANN_instance = pygad.gann.GANN(
    num_solutions=num_solutions,
    num_neurons_input=num_inputs,
    num_neurons_hidden_layers=[150, 50],
    num_neurons_output=num_classes,
    hidden_activations=["relu", "relu"],
    output_activation="softmax",
) """

# population does not hold the numerical weights of the network instead it holds a list of references to each last layer of each network (i.e. solution) in the population. A solution or a network can be used interchangeably.
# If there is a population with 3 solutions (i.e. networks), then the population is a list with 3 elements. Each element is a reference to the last layer of each network. Using such a reference, all details of the network can be accessed.
population_vectors = pygad.gann.population_as_vectors(
    population_networks=GANN_instance.population_networks
)

# To prepare the initial population, there are 2 ways:
# 1) Prepare it yourself and pass it to the initial_population parameter. This way is useful when the user wants to start the genetic algorithm with a custom initial population.
# 2) Assign valid integer values to the sol_per_pop and num_genes parameters. If the initial_population parameter exists, then the sol_per_pop and num_genes parameters are useless.
initial_population = population_vectors.copy()

num_parents_mating = (
    4  # Number of solutions to be selected as parents in the mating pool.
)

num_generations = 500  # Number of generations.

mutation_percent_genes = 10  # Percentage of genes to mutate. This parameter has no action if the parameter mutation_num_genes exists.

parent_selection_type = "sss"  # Type of parent selection.

crossover_type = "single_point"  # Type of the crossover operator.

mutation_type = "random"  # Type of the mutation operator.

keep_parents = (
    -1
)  # Number of parents to keep in the next population. -1 means keep all parents and 0 means keep nothing.

""" ga_instance = pygad.GA(
    num_generations=num_generations,
    num_parents_mating=num_parents_mating,
    initial_population=initial_population,
    fitness_func=fitness_func,
    mutation_percent_genes=mutation_percent_genes,
    parent_selection_type=parent_selection_type,
    crossover_type=crossover_type,
    mutation_type=mutation_type,
    keep_parents=keep_parents,
    on_generation=callback_generation,
) """

params = dict(
    fitness_func=fitness_func,
    num_generations=500,
    num_parents_mating=8,
    parent_selection_type="sss",
    crossover_type="uniform",
    mutation_type="random",
    mutation_percent_genes=10,
    on_generation=generation_step,
)

ga_instance = pygad.GA(**params)
ga_instance.run()

# After the generations complete, some plots are showed that summarize how the outputs/fitness values evolve over generations.
ga_instance.plot_fitness()
solution, solution_fitness, solution_idx = ga_instance.best_solution()

with open("datafile.txt", "wb") as fh:
    pickle.dump(GANN_instance.population_networks[solution_idx], fh)
