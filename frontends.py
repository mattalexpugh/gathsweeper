import curses
import string

from os import system
from typing import Optional

from board import Board, Coord


class GameInterface():

    class GameStatus():
        WIN, LOSE, QUIT = range(3)

    WINNER_TEXT = 'A winner is you!'
    LOSER_TEXT = 'There was a mine!'

    def __init__(self, num_rows: int=20, num_cols: int=20, num_mines: int=10):
        self._board = Board(num_rows, num_cols, num_mines)
        self._running = False

    def _win(self) -> int:
        self.render(show_mines=True, msg=self.WINNER_TEXT)
        return GameInterface.GameStatus.WIN

    def _game_over(self) -> int:
        self.render(show_mines=True, msg=self.LOSER_TEXT)
        return GameInterface.GameStatus.LOSE

    def run(self) -> int:
        raise NotImplementedError()

    def render(self, msg: Optional[str] = None, show_mines: bool = False) -> None:
        raise NotImplementedError()


class ConsoleBase(GameInterface):

    COVERED = '▒'
    MARKED = '■'
    MINE = '¤'

    def _render_line(self, y: int, show_mines: bool=False) -> str:
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


class ConsoleBasic(ConsoleBase):

    AXIS_COORDS = string.digits + string.ascii_letters + string.punctuation

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
            print(f"{x_padding}{label} ║" + self._render_line(y, show_mines) + f"║{label}")

        print(f"{x_padding}  ╚" + '═' * len(self._axis_x) + f"╝\n{x_padding}   {self._axis_x}\n")


class ConsoleCurses(ConsoleBase):

    def __init__(self, num_rows: int=20, num_cols: int=20, num_mines: int=10):
        super().__init__(num_rows, num_cols, num_mines)

    def run(self) -> int:
        self._running = True

        stdscr = curses.initscr()
        curses.noecho()
        curses.curs_set(0)
        stdscr.keypad(1)
        curses.mousemask(1)

        if curses.has_colors():
            curses.start_color()

        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

        stdscr.box()

        # DO some rendering
        idx_grid_offset_y = 2
        idx_grid_offset_x = 2

        # State keeping
        key_event = 0
        mark_mode = False

        while self._running:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            start_y = int((height // 2) - 2)
            statusbar = " GathSweeper | (q)uit | toggle (m)ark mode | "
            statusbar += f"Remaining [{self._board.num_mines_remaining}/{self._board.num_mines}]"

            if mark_mode:
                statusbar += " | [MARKING]"

            # Render status bar
            stdscr.attron(curses.color_pair(3))
            stdscr.addstr(height - 1, 0, statusbar)
            stdscr.addstr(height - 1, len(statusbar), " " * (width - len(statusbar) - 1))
            stdscr.attroff(curses.color_pair(3))

            for y in range(self._board.num_rows):
                stdscr.addstr(y + idx_grid_offset_y, idx_grid_offset_x, self._render_line(y))

            if key_event == ord("q"):
                break
            if key_event == ord("m"):
                mark_mode = not mark_mode
                key_event = 0
                continue
            if key_event == curses.KEY_MOUSE:
                _, mx, my, _, _ = curses.getmouse()
                key_event = 0

                if mx % 2 != 0:
                    continue

                coord = Coord((mx - idx_grid_offset_x) // 2, my - idx_grid_offset_y)

                if not mark_mode:
                    status = self._board.uncover(coord)

                    if status == Board.UncoverStatus.BOMB:
                        start_x_title = int((width // 2) - (len(self.LOSER_TEXT) // 2) - len(self.LOSER_TEXT) % 2)
                        stdscr.addstr(start_y, start_x_title, self.LOSER_TEXT)
                        key_event = stdscr.getch()
                        curses.echo()
                        curses.endwin()
                        return self._game_over()
                    elif status == Board.UncoverStatus.WIN:
                        start_x_title = int((width // 2) - (len(self.WINNER_TEXT) // 2) - len(self.WINNER_TEXT) % 2)
                        stdscr.addstr(start_y, start_x_title, self.WINNER_TEXT)
                        key_event = stdscr.getch()
                        curses.echo()
                        curses.endwin()
                        return self._win()
                else:
                    self._board.mark(coord)

                continue

            key_event = stdscr.getch()

        curses.echo()
        curses.endwin()

    def render(self, msg: Optional[str] = None, show_mines: bool = False) -> None:
        pass
