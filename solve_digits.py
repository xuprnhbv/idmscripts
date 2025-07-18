#! python
import itertools
import argparse
from tqdm import tqdm
import math


OPERATORS = ['+', '-', '*', '/']

def digits(result, board, expression_minimal_length=2, to_print=False, quiet=False):
    """
    Finds expressions that equal the given result.
    Goes over all permutations of the numbers on the board, and combinations of operators possible, and evaluating them one by one until an answer is found.
    In board permutations, we start from expressions with only two numbers (because one number will not be the answer), and go up in length until we use all numbers on the board.
    We use product with operators because we can use operators more then once, so its practically itertools.permutations but with repetition.
    """
    if not quiet:
        print(f"Looking for result {result} out of digits {board}:")
    if not to_print and not quiet:
        max_iterations =  sum((math.factorial(len(board)) / math.factorial(len(board) - r_i)) * (len(OPERATORS)**(r_i - 1)) for r_i in range(expression_minimal_length, len(board) + 1))
        bar = tqdm(total=max_iterations)
    for r in range(expression_minimal_length, len(board) +1):
        for p in itertools.permutations(board, r=r):
            for ops in itertools.product(OPERATORS, repeat=r-1):
                exp = ''
                for i in range(r-1):
                    exp += str(p[i]) + ops[i]
                exp += str(p[-1])
                try:
                    if to_print:
                        print(exp)
                    elif not quiet:
                        bar.update()
                    if eval(exp) == result:
                        return exp
                except ZeroDivisionError:
                    pass
    return None


def parse_args():
    parser = argparse.ArgumentParser(description="Solve digits challenge.")
    parser.add_argument("result", type=int, help="The required answer.")
    parser.add_argument("numbers", type=int, nargs='+', metavar="n", help="The challenge's given numbers.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print expressions as they are generated.")
    parser.add_argument("-m", "--minimal-length", required=False, default=2, type=int, help="The smallest number of numbers in an expression. Defaults to 2.")
    parser.add_argument("-q", "--quiet", action="store_true", help="Do not show bar or messages except final result.")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    print("Solution is {}".format(digits(args.result, args.numbers, args.minimal_length, args.verbose, args.quiet)))