from argparse import ArgumentParser

from frontends import ConsoleBasic


if __name__ == '__main__':
    parser = ArgumentParser(description="Minesweeper, console edition")
    parser.add_argument('-r', "--rows", help="Number of rows (default: 10)", type=int, default="10")
    parser.add_argument('-c', "--cols", help="Number of columns (default: 10)", type=int, default="10")
    parser.add_argument('-m', "--mines", help="Number of mines (default: 10)", type=int, default="10")
    args = parser.parse_args()

    game = ConsoleBasic(args.rows, args.cols, args.mines)
    game.run()
