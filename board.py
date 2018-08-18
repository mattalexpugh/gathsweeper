from collections import namedtuple
from random import choice
from typing import Generator, List, Set, Union


Coord = namedtuple("Coord", ['x', 'y'])


class Board():

    class CellStatus():
        UNDISCOVERED, MARKED, DISCOVERED = range(3)

    class UncoverStatus():
        CONTINUE, BOMB, WIN = range(3)

    class Cell():

        def __init__(self, cell_value: int, cell_status: int):
            self.__cell_value = cell_value
            self.__cell_status = cell_status

        @property
        def has_bomb(self) -> bool:
            return self.__cell_value == Board.MINE

        @property
        def value(self) -> int:
            return self.__cell_value

        @property
        def is_marked(self) -> bool:
            return self.__cell_status == Board.CellStatus.MARKED

        @property
        def is_discovered(self) -> bool:
            return self.__cell_status == Board.CellStatus.DISCOVERED

        @property
        def is_empty(self) -> bool:
            return self.__cell_value == 0

    MINE = -1

    def __init__(self, num_rows: int=10, num_cols: int=10, num_bombs: int=10):
        self.__board = [[0] * num_cols for r in range(num_rows)]
        self.__status = [[Board.CellStatus.UNDISCOVERED] * num_cols for i in range(num_rows)]
        self.__mine_locations = set()

        self.__num_rows = num_rows
        self.__num_cols = num_cols
        self.__num_mines = num_bombs
        self.__num_mines_remaining = num_bombs
        self.__num_undiscovered = num_rows * num_cols - num_bombs

        self.__populate()

    def __getitem__(self, y: int) -> List['Board.Cell']:
        return [Board.Cell(v, s) for v, s in zip(self.__board[y], self.__status[y])]

    def __get_neighbours_of(self, coord: Coord) -> Generator[Coord, None, None]:
        x_min, x_max = max(0, coord.x - 1), min(self.num_cols - 1, coord.x + 1) + 1
        y_min, y_max = max(0, coord.y - 1), min(self.num_rows - 1, coord.y + 1) + 1

        for x in range(x_min, x_max):
            for y in range(y_min, y_max):
                neighbour = self.get_coord(x, y)

                if neighbour != coord:
                    yield neighbour

    def __place_bomb(self, coord: Coord) -> None:
        self.__board[coord.y][coord.x] = self.MINE

        for loc in self.__get_neighbours_of(coord):
            if self.__board[loc.y][loc.x] != self.MINE:
                self.__board[loc.y][loc.x] += 1

    def __populate(self) -> None:
        if self.num_cols * self.num_rows <= self.num_mines:
            raise RuntimeError("Must have at least one mine-free cell.")

        f_rand_row = lambda: choice(range(self.num_rows))
        f_rand_col = lambda: choice(range(self.num_cols))

        while len(self.__mine_locations) < self.num_mines:
            coord = self.get_coord(f_rand_col(), f_rand_row())

            if coord not in self.__mine_locations:
                self.__mine_locations.add(coord)
                self.__place_bomb(coord)

    def __get_empty_region(self, coord: Coord) -> Generator[Coord, None, None]:
        if self.__status[coord.y][coord.x] == Board.CellStatus.UNDISCOVERED and self.__board[coord.y][coord.x] == 0:
            stack = [coord]
            seen = set(stack)
            border = set()

            while len(stack):
                current = stack.pop(0)

                for neighbour in self.__get_neighbours_of(current):
                    if neighbour not in seen and self.__status[neighbour.y][neighbour.x] == Board.CellStatus.UNDISCOVERED:
                        if self.__board[neighbour.y][neighbour.x] == 0:
                            stack.append(neighbour)
                        else:
                            border.add(neighbour)

                        seen.add(neighbour)

                yield current

            for loc in border:
                yield loc
        else:
            yield coord

    def __bomb_at(self, coord: Coord) -> bool:
        return self.__board[coord.y][coord.x] == self.MINE

    def uncover(self, coord: Coord) -> int:
        if self.__status[coord.y][coord.x] != Board.CellStatus.UNDISCOVERED:
            return Board.UncoverStatus.CONTINUE
        elif self.__bomb_at(coord):
            return Board.UncoverStatus.BOMB

        for loc in self.__get_empty_region(coord):
            self.__status[loc.y][loc.x] = Board.CellStatus.DISCOVERED
            self.__num_undiscovered -= 1

        return Board.UncoverStatus.WIN if self.__num_undiscovered == 0 else Board.UncoverStatus.CONTINUE

    def mark(self, loc: Coord) -> None:
        if self.__status[loc.y][loc.x] == Board.CellStatus.UNDISCOVERED:
            self.__status[loc.y][loc.x] = Board.CellStatus.MARKED
            self.__num_mines_remaining -= 1
        elif self.__status[loc.y][loc.x] == Board.CellStatus.MARKED:
            self.__status[loc.y][loc.x] = Board.CellStatus.UNDISCOVERED
            self.__num_mines_remaining += 1

    @property
    def num_cols(self) -> int:
        return self.__num_cols

    @property
    def num_rows(self) -> int:
        return self.__num_rows

    @property
    def num_mines(self) -> int:
        return self.__num_mines

    @property
    def num_mines_remaining(self) -> int:
        return self.__num_mines_remaining

    @staticmethod
    def get_coord(x: int, y: int) -> Coord:
        return Coord(x, y)
