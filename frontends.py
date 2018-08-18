import string

from os import system
from typing import Optional

from board import Board, Coord


class GameInterface():

    class GameStatus():
        WIN, LOSE, QUIT = range(3)

    def __init__(self, num_rows: int=20, num_cols: int=20, num_mines: int=10):
        self._board = Board(num_rows, num_cols, num_mines)
        self._running = False

    def _win(self) -> int:
        self.render(show_mines=True, msg='A winner is you!')
        return GameInterface.GameStatus.WIN

    def _game_over(self) -> int:
        self.render(show_mines=True, msg='There was a mine!')
        return GameInterface.GameStatus.LOSE

    def run(self) -> int:
        raise NotImplementedError()

    def render(self, msg: Optional[str] = None, show_mines: bool = False) -> None:
        raise NotImplementedError()


class ConsoleBasic(GameInterface):

    AXIS_COORDS = string.digits + string.ascii_letters + string.punctuation
    COVERED = '▒'
    MARKED = '■'
    MINE = '¤'

    def __init__(self, num_rows: int=20, num_cols: int=20, num_mines: int=10):
        super().__init__(num_rows, num_cols, num_mines)
        self._axis_x = ' '.join(x for x in self.AXIS_COORDS[:num_cols])
        self._axis_y = self.AXIS_COORDS[:num_rows]

    def __convert_str_to_coord(self, loc: str) -> Coord:
        x, y = loc[1:]
        x, y = self.AXIS_COORDS.find(x), self.AXIS_COORDS.find(y)
        return Coord(x, y)

    def run(self) -> int:
        self._running = True

        while self._running:
            self.render()
            response = input("(U)ncover [Uxy], (M)ark [Mxy], (Q)uit: ").strip()
            cmd_id = response[0].lower()

            if cmd_id == 'q':
                self._running = False
            elif len(response) < 3:
                continue
            elif cmd_id == 'u':
                status = self._board.uncover(self.__convert_str_to_coord(response))

                if status == Board.UncoverStatus.BOMB:
                    return self._game_over()
                elif status == Board.UncoverStatus.WIN:
                    return self._win()
            elif cmd_id == 'm':
                self._board.mark(self.__convert_str_to_coord(response))

        return ConsoleBasic.GameStatus.QUIT

    def __render_line(self, y: int, show_mines: bool=False) -> str:
        line = []

        for cell in self._board[y]:
            if cell.is_discovered:
                line.append(' ' if cell.is_empty else str(cell.value))
            elif show_mines and cell.has_bomb:
                line.append(self.MINE)
            elif cell.is_marked:
                line.append(self.MARKED)
            else:
                line.append(self.COVERED)

        return ' '.join(line)

    def render(self, msg: Optional[str]=None, show_mines: bool=False) -> None:
        _ = system('clear')
        x_padding = ' '
        y_padding = 1

        if msg is not None:
            print(msg)

        for i in range(y_padding):
            print('')

        print(f"{x_padding}{self._board.num_mines_remaining}/{self._board.num_mines} Remaining\n")
        print(f"{x_padding}   {self._axis_x}\n{x_padding}  ╔" + '═' * len(self._axis_x) + '╗')

        for y, label in enumerate(self._axis_y):
            print(f"{x_padding}{label} ║" + self.__render_line(y, show_mines) + f"║{label}")

        print(f"{x_padding}  ╚" + '═' * len(self._axis_x) + f"╝\n{x_padding}   {self._axis_x}\n")
