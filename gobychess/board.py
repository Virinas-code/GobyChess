#!/usr/bin/env python3

## TODO/FIXME/NOTE/DEPRECATED/HACK/REVIEW

import itertools

from gmpy2 import bit_scan1, xmpz

from . import movegen as mvg
from .utils import bitboard_of_square, print_bitboard, bitboard_of_index
import numpy as np
import copy


class Board():

    def __init__(self):
        self.pieces = [[], []]
        self.pieces[0] = [xmpz(0b0000000011111111000000000000000000000000000000000000000000000000),
                          xmpz(0b0100001000000000000000000000000000000000000000000000000000000000),
                          xmpz(0b0010010000000000000000000000000000000000000000000000000000000000),
                          xmpz(0b1000000100000000000000000000000000000000000000000000000000000000),
                          xmpz(0b0001000000000000000000000000000000000000000000000000000000000000),
                          xmpz(0b0000100000000000000000000000000000000000000000000000000000000000)]
        self.pieces[1] = [xmpz(0b0000000000000000000000000000000000000000000000001111111100000000),
                          xmpz(0b0000000000000000000000000000000000000000000000000000000001000010),
                          xmpz(0b0000000000000000000000000000000000000000000000000000000000100100),
                          xmpz(0b0000000000000000000000000000000000000000000000000000000010000001),
                          xmpz(0b0000000000000000000000000000000000000000000000000000000000010000),
                          xmpz(0b0000000000000000000000000000000000000000000000000000000000001000)]
        self.to_move = 1
        self.white_kingside = 1
        self.white_queenside = 1
        self.black_kingside = 1
        self.black_queenside = 1
        self.en_passant = xmpz(0b0000000000000000000000000000000000000000000000000000000000000000)
        self.halfmove_clock = 0
        self.fullmove_counter = 1

        self.all_pieces_color = [xmpz(0b0000000000000000000000000000000000000000000000000000000000000000),
                                 xmpz(0b0000000000000000000000000000000000000000000000000000000000000000)]
        # self.all_pieces_black = xmpz(0b0000000000000000000000000000000000000000000000000000000000000000)
        # self.all_pieces_white = xmpz(0b0000000000000000000000000000000000000000000000000000000000000000)
        self.all_pieces = xmpz(0b0000000000000000000000000000000000000000000000000000000000000000)

        self.update_all_pieces()

    def from_fen(self, fen):
        '''
        Set board to fen position

        Args:
            String containing the fen position
        '''
        words = fen.split()

        if words[1] == 'w':
            self.to_move = 1
        else:
            self.to_move = 0

        if words[2] == '-':
            self.white_kingside = 0
            self.white_queenside = 0
            self.black_kingside = 0
            self.black_queenside = 0
        if 'K' in words[2]:
            self.white_kingside = 1
        else:
            self.white_kingside = 0
        if 'Q' in words[2]:
            self.white_queenside = 1
        else:
            self.white_queenside = 0
        if 'k' in words[2]:
            self.black_kingside = 1
        else:
            self.black_kingside = 0
        if 'q' in words[2]:
            self.black_queenside = 1
        else:
            self.black_queenside = 0

        if words[3] == '-':
            self.en_passant = xmpz(0b0000000000000000000000000000000000000000000000000000000000000000)
        else:
            self.en_passant = bitboard_of_square(words[3])

        self.halfmove_clock = int(words[4])
        self.fullmove_counter = int(words[5])

        rows = words[0].split("/")
        index = 0
        piece_strings = {'p': 0, 'n': 1, 'b': 2, 'r': 3, 'q': 4, 'k': 5}
        for row in rows[::-1]:
            for char in row:
                if char.isdigit():
                    for _ in range(int(char)):
                        for piecetype in range(6):
                            self.pieces[0][piecetype][index] = 0
                            self.pieces[1][piecetype][index] = 0
                        index += 1
                else:
                    color = 0
                    if char.isupper():
                        color = 1
                        char = char.lower()
                    for piecetype in range(6):
                        if piecetype == piece_strings[char]:
                            self.pieces[color][piecetype][index] = 1
                        else:
                            self.pieces[0][piecetype][index] = 0
                            self.pieces[1][piecetype][index] = 0
                    index += 1

        self.update_all_pieces()

    def __str__(self):
        '''
        Print current position
        '''
        board_str = "." * 64
        board_str = list(board_str)

        piece_strings = {0: 'p', 1: 'n', 2: 'b', 3: 'r', 4: 'q', 5: 'k'}

        for i in [0, 1]:
            piece = ""
            for j in range(6):
                piece = piece_strings[j]
                if i == 1:
                    piece = piece.upper()

                for square in range(64):
                    if self.pieces[i][j][square]:
                        board_str[square] = piece

        board_str = "".join(board_str)[::-1]
        board_str = list(board_str)
        for i in range(8):
            x = board_str[i * 8:(i + 1) * 8]
            board_str[i * 8:(i + 1) * 8] = x[::-1]
            board_str[(i + 1) * 8 - 1] += '\n'
        board_str = "".join(board_str)

        return "To move: {}\n{}\nEn passent square: \
                {}\nmoves played: {}".format(self.to_move, board_str,
                                             self.en_passant,
                                             self.fullmove_counter)

    def make_move(self, move):
        '''
        Apply move to board

        Args:
            move (Tuple): Tuple containing (square from, square to, pomotion)
        '''
        # check if indices in bound
        square_from, square_to, promotion = move
        if not 0 <= square_from <= 63 or not 0 <= square_to <= 63:
            raise IndexError("Square outside the Board")
        # check if a piece (and which) is on square from
        if not self.all_pieces[square_from]:
            raise ValueError("There is no piece on the square")
        # on what square is it not 0
        color, piece_to_move = self.piece_on(square_from)
        # check if piece can go to square to
        if not mvg.check_piece_move(piece_to_move, square_from, square_to, self):
            print(self)
            raise ValueError("Move {} is not possible".format(move))
        # check if color to move afterwards in check
        if self.in_check_after_move(move):
            raise ValueError("You are in Check!")

        capture = False

        if piece_to_move == 0:
            self.halfmove_clock = 0
        elif self.all_pieces_color[1 - self.to_move][square_to]:
            self.halfmove_clock = 0
            capture = True
        else:
            self.halfmove_clock += 1

        if capture:
            for i in range(4):
                self.pieces[1 - self.to_move][i][square_to] = 0

        if not self.to_move:
            self.fullmove_counter += 1

        self.pieces[self.to_move][piece_to_move][square_from] = 0
        self.pieces[self.to_move][piece_to_move][square_to] = 1
        self.update_all_pieces()

        if piece_to_move == 0 and abs(square_from - square_to) == 16:
            if self.to_move:
                self.en_passant = square_to - 8
            else:
                self.en_passant = square_to + 8

        self.to_move = 1 - self.to_move
        # if pawn
            # if check if on 7th rank
                # check if promotion given
                # apply
            # if pawn did double move
                # update en passant square
            # else set en passant square to empty
        # else:
        # apply
        # change color to move
        # update all pieces
        # update halfmove and fullmove counter
        # update castling rights
        return self

    def gen_legal_moves(self):
        return itertools.filterfalse(lambda moves: self.in_check_after_move(moves),
                                     mvg.generate_moves(self))

    def update_all_pieces(self):
        '''
        Update the bitboards containing positions of all pieces
        '''
        self.all_pieces = xmpz(0b0000000000000000000000000000000000000000000000000000000000000000)
        self.all_pieces_color[0] = xmpz(0b0000000000000000000000000000000000000000000000000000000000000000)
        self.all_pieces_color[1] = xmpz(0b0000000000000000000000000000000000000000000000000000000000000000)



        for i, j in itertools.product(range(2), range(6)):
            self.all_pieces |= self.pieces[i][j]
        for i in range(6):
            self.all_pieces_color[1] |= self.pieces[1][i]

        for i in range(6):
            self.all_pieces_color[0] |= self.pieces[0][i]

    def piece_on(self, square):
        for color, piecetype in itertools.product(range(2), range(6)):
            if self.pieces[color][piecetype][square]:
                return color, piecetype
        return None, None

    def board_copy(self):
        new_board = Board()
        new_board.pieces = copy.deepcopy(self.pieces)
        new_board.to_move = self.to_move
        new_board.update_all_pieces()
        return new_board

    def in_check(self):
        return mvg.color_in_check(self.to_move, self)

    def in_check_after_move(self, move):
        square_from, square_to, promotion = move
        color, piece_to_move = self.piece_on(square_from)
        tmp_board = self.board_copy()
        # REVIEW better alternatives ?
        tmp_board.pieces[tmp_board.to_move][piece_to_move][square_from] = 0
        tmp_board.pieces[tmp_board.to_move][piece_to_move][square_to] = 1
        #print(self.all_pieces, type(self.all_pieces))
        #tmp_board.all_pieces = copy.deepcopy(self.all_pieces)
        #print(tmp_board.all_pieces, type(tmp_board.all_pieces))
        #print_bitboard(tmp_board.all_pieces)
        tmp_board.update_all_pieces()
        #tmp_board.all_pieces[square_from] = 0
        #tmp_board.all_pieces[square_to] = 1
        # REVIEW not needed ?
        for i in range(4):
            tmp_board.pieces[1 - tmp_board.to_move][i][square_to] = 0
        return tmp_board.in_check()
