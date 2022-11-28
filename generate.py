import sys
import random

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # Loop over each entry in self.domains
        for entry in self.domains.items():
            var, domain = entry
            # Remove values that are inconsistent with unary contraints
            for value in domain.copy():
                if len(value) != var.length:
                    domain.remove(value)


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # Check if two variables overlap
        if self.crossword.overlaps[x, y]:
            i, j = self.crossword.overlaps[x, y]
            change = False
            # Check if there is possible value for y
            for value1 in self.domains[x].copy():
                counter = 0
                for value2 in self.domains[y]:
                    if value1[i] == value2[j]:
                        break
                    counter += 1
                # If there is no possible value for y
                if counter == len(self.domains[y]):
                    self.domains[x].remove(value1)
                    change= True
            return change
        else:
            return False

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs == None:
            arcs = []
            # Get queue of all arcs in the problem
            for var1 in self.crossword.variables:
                for var2 in self.crossword.variables:
                    if var1 == var2:
                        continue
                    if self.crossword.overlaps[var1, var2]:
                        if (var2, var1) not in arcs:
                            arcs.append((var1, var2))
        
        # Revise each arc in the queue
        while arcs:
            for arc in arcs:
                # Remove arc from queue
                arcs.remove(arc)
                if self.revise(arc[0], arc[1]):
                    # If no value in domain
                    if len(self.domains[arc[0]]) == 0:
                        return False
                # Add additional arc to queue if need be
                for value in self.crossword.variables:
                    if value != arc[0] and self.crossword.overlaps[value, arc[0]] and value != arc[1]:
                        arcs.append((value, arc[0]))

        return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        # Check if assignment contain all avriable
        if len(self.crossword.variables) == len(assignment.keys()):
            for value in self.crossword.variables:
                # Check if variable is assigned a value
                if assignment[value] is None:
                    return False
            return True
        return False

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # Loop over all pair in assignment
        for key1, value1 in assignment.items():
            for key2, value2 in assignment.items():
                if key1 == key2:
                    continue
                # Check if values are distinct
                if value1 == value2:
                    return False
                # Check if values are of correct length
                if len(value1) != key1.length or len(value2) != key2.length:
                    return False
                # Check for conflict between variables
                if self.crossword.overlaps[key1, key2]:
                    i, j = self.crossword.overlaps[key1, key2]
                    if value1[i] != value2[j]:
                        return False
        # If all tests passed, return True
        return True
            

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # Get a list of all var's neighbors
        neighbors = self.crossword.neighbors(var)
        domain_values = []

        # If there are neightbors
        if neighbors:
            for value in self.domains[var]:
                n = 0
                for neighbor in neighbors:
                    # If neighbor is not alreaady assigned
                    if neighbor not in list(assignment.keys()):
                        i, j = self.crossword.overlaps[var, neighbor]
                        for value_neighbor in self.domains[neighbor]:
                            if value[i] != value_neighbor[j]:
                                n += 1
                domain_values.append((value, n))
        else:
            for value in self.domains[var]:
                domain_values.append((value, 0))

        # Sort the list by n
        domain_values.sort(key=lambda var: var[1])

        domain = []
        # Get a list of values only
        for value in domain_values.copy():
            domain.append(value[0])

        return domain

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # Initialize empty list
        unassigned = []
        # Loop over all variable
        for var in self.crossword.variables:
            # Add variable to list if variable not already in assignment
            if var not in list(assignment.keys()):
                if self.crossword.neighbors(var):
                    degree = len(self.crossword.neighbors(var))
                    unassigned.append(((var), (len(self.domains[var])), degree))
                else:
                    unassigned.append(((var), (len(self.domains[var])), 0))

        # Sort variable by degree
        unassigned.sort(key=lambda var: var[2], reverse=True)
        # Sort variable by number of values in domain
        unassigned.sort(key=lambda var: var[1])

        return unassigned[0][0]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # Check if assignment is complete
        if self.assignment_complete(assignment):
            return assignment
        # If not complete
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            # Add value to assignment
            assignment[var] = value
            # If new assignment is consistent
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result != None:
                    return result
            # If new assignment is not consistent
            assignment.pop(var)

        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
