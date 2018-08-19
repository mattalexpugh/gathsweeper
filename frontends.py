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

    def run(self) -> int:
        raise NotImplementedError()


class ConsoleBase(GameInterface):

    COVERED = '■'
    MARKED = '@'
    MINE = '×'

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
        x, y = self.AXIS_COORDS.find(loc[1]), self.AXIS_COORDS.find(loc[2])
        return Coord(x, y)

    def _win(self) -> int:
        self.render(show_mines=True, msg=self.WINNER_TEXT)
        return GameInterface.GameStatus.WIN

    def _game_over(self) -> int:
        self.render(show_mines=True, msg=self.LOSER_TEXT)
        return GameInterface.GameStatus.LOSE

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

        # Need to get some colours for the numbers!
        if curses.has_colors():
            curses.start_color()

        for i, forecolor in enumerate([ curses.COLOR_WHITE, curses.COLOR_CYAN,
                                        curses.COLOR_BLUE, curses.COLOR_MAGENTA,
                                        curses.COLOR_GREEN, curses.COLOR_YELLOW, 
                                        curses.COLOR_RED, curses.COLOR_RED], start=1):
            curses.init_pair(i, forecolor, curses.COLOR_BLACK)

        stdscr.box()

        # Work out some geometry things
        height, width = stdscr.getmaxyx()
        l_row = self._board.num_rows * 2 - 1
        l_col = self._board.num_cols + 5  # Padding etc
        idx_grid_offset_y = int((height // 2) - (l_col // 2) - l_col % 2)
        idx_grid_offset_x = int((width // 2) - (l_row // 2) - l_row % 2)
        start_y = int((height // 2) - 2)
        y_title_offset = 3

        # State keeping
        key_event = 0
        mark_mode = False

        def render_outcome(msg: str) -> None:
            # At the end of the game, so show all the mines
            render_board(show_mines=True)
            l_msg = len(msg)
            start_x = int((width // 2) - (l_msg // 2) - l_msg % 2)
            inner = "═" * (l_msg + 2)

            for i, segment in enumerate([f"╔{inner}╗",  f"║ {msg} ║", f"╚{inner}╝"], start=-1):
                stdscr.addstr(start_y + i, start_x, segment)

            # Wait for any input before exiting
            _ = stdscr.getch()
            curses.echo()
            curses.endwin()

        def render_board(show_mines: bool=False) -> None:
            # Render the current state of the board, dealing with borders, colors etc.
            inner = "═" * (l_row + 2)
            remaining = "[{}] {}".format(self._board.num_mines_remaining, "[M]" if mark_mode else "")
            padding = " " * (l_row - len(remaining))

            for offset, header in enumerate([f"╔{inner}╗", f"║ {remaining}{padding} ║", f"╠{inner}╣"]):
                stdscr.addstr(idx_grid_offset_y + offset, idx_grid_offset_x, header)

            for y in range(self._board.num_rows):
                line = "║ " + self._render_line(y, show_mines=show_mines) + " ║"

                # Check for numeric values in this line, and render colors accordingly
                for i, ch in enumerate(line):
                    if ch.isdigit():
                        stdscr.attron(curses.color_pair(int(ch)))
    
                    stdscr.addstr(y + idx_grid_offset_y + y_title_offset, idx_grid_offset_x + i, ch)

                    if ch.isdigit():
                        stdscr.attroff(curses.color_pair(int(ch)))


            stdscr.addstr(self._board.num_rows + idx_grid_offset_y + y_title_offset, idx_grid_offset_x, f"╚{inner}╝")

        while self._running:
            stdscr.clear()
            statusbar = " GathSweeper | (q)uit | toggle (m)ark mode"

            # Render status bar
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(height - 1, 0, statusbar)
            stdscr.addstr(height - 1, len(statusbar), " " * (width - len(statusbar) - 1))
            stdscr.attroff(curses.color_pair(1))

            render_board()

            if key_event == ord("q"):
                break
            if key_event == ord("m"):
                mark_mode = not mark_mode
                key_event = 0
                continue
            if key_event == curses.KEY_MOUSE:
                _, mx, my, _, _ = curses.getmouse()
                key_event = 0

                # TODO: Fix this to be dynamic given sizes
                if mx % 1 != 0:
                    continue

                coord = Coord((mx - idx_grid_offset_x - 2) // 2, my - idx_grid_offset_y - y_title_offset)

                if coord.x >= self._board.num_cols or coord.y >= self._board.num_rows:
                    continue

                if not mark_mode:
                    status = self._board.uncover(coord)

                    if status == Board.UncoverStatus.BOMB:
                        render_outcome(self.LOSER_TEXT)
                        return self._game_over()
                    elif status == Board.UncoverStatus.WIN:
                        render_outcome(self.WINNER_TEXT)
                        return self._win()
                else:
                    self._board.mark(coord)

                continue

            key_event = stdscr.getch()

        curses.echo()
        curses.endwin()
        return Board.UncoverStatus.CONTINUE
