#!/usr/bin/env python3

"""
Basic uci implementation
"""

from .board import Board
from .utils import move_from_san, san_from_move
from .search import Searcher
from .evaluation import Evaluator
import time

def main():

    board = Board()

    evaluator = Evaluator()
    searcher = Searcher(evaluator, aim_depth=4, manage_time=True)


    while True:
        command = input()

        if command == 'quit':
            break

        elif command == 'uci':
            print("id name GobyChess")
            print("id author Tom Magorsch")
            print("option name evalpath type string")
            print("uciok")

        elif command == 'isready':
            print("readyok")

        elif command == 'ucinewgame':
            board.reset_board()

        elif command.startswith('position'):
            words = command.split(' ')

            moves_position = command.find('moves')

            if words[1] == 'fen':
                if moves_position >= 0:
                    fen_string = command[:moves_position]
                else:
                    fen_string = command

                fen = fen_string.split(' ', 2)[2]

                board.from_fen(fen)


            if words[1] == 'startpos':
                board.reset_board()

            if moves_position >= 0:
                moves = command[moves_position:].split()[1:]
            else:
                moves = []

            for move in moves:
                board.make_generated_move(move_from_san(move))

        elif command.startswith('go'):

            _, *params = command.split()

            parameters = params[::2]
            values = params[1::2]

            for parameter, value in zip(parameters, values):
                if parameter == 'wtime':
                    searcher.wtime = int(value)
                elif parameter == 'btime':
                    searcher.btime = int(value)
                elif parameter == 'winc':
                    searcher.winc = int(value)
                elif parameter == 'binc':
                    searcher.binc = int(value)
                elif parameter == 'depth':
                    searcher.aim_depth = int(value)
                    searcher.manage_time = False
                elif parameter == 'movetime':
                    pass

            searcher.update_depth(board.to_move, board.fullmove_counter)

            evaluation = searcher.search_negascout(board)
            #evaluation = searcher.search_alpha_beta(board)
            print(f'bestmove {san_from_move(searcher.best_move)}')

        elif command.startswith('setoption'):
            _, *params = command.split()
            if params[1] == 'evalpath':
                evaluator.load_tables(params[3] + "_square.csv", params[3] + "_piece.csv")

        else:
            pass


if __name__ == "__main__":
    main()
