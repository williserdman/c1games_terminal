""" so this pygad solution has the slight issue of essentually only being one layer deep """

import pygad
import numpy

function_inputs = [4, -2, 3.5, 5, -11, -4.7]
desired_output = [10, 22]


def fitness_func(solution, solution_idx):
    print("\n\n\n\n")
    print(solution_idx)
    print("\n\n\n\n")
    output = numpy.sum(solution * function_inputs)
    fitness = 1.0 / numpy.sum(numpy.abs(output - desired_output))
    return fitness


params = dict(
    fitness_func=fitness_func,
    num_generations=50,
    num_parents_mating=4,
    sol_per_pop=100,
    num_genes=len(function_inputs),
    init_range_low=-2,
    init_range_high=5,
    parent_selection_type="sss",
    crossover_type="uniform",
    mutation_type="random",
    mutation_percent_genes=10,
)

ga_instance = pygad.GA(**params)
ga_instance.run()

solution, solution_fitness, solution_idx = ga_instance.best_solution()
print("Parameters of the best solution : {solution}".format(solution=solution))
print(
    "Fitness value of the best solution = {solution_fitness}".format(
        solution_fitness=solution_fitness
    )
)

prediction = numpy.sum(numpy.array(function_inputs) * solution)
print(
    "Predicted output based on the best solution : {prediction}".format(
        prediction=prediction
    )
)
