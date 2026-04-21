import time
import os

NUMBER_PADDING = 10


def TERMINAL_WIDTH():
    return os.get_terminal_size().columns


def _clear():
    print("\r", end="", flush=False)
    print(" " * TERMINAL_WIDTH(), end="", flush=False)
    print("\r", end="", flush=False)
    print("", end="", flush=True)


def _get_percentage(number: float, padding: int) -> str:
    rounded = round(number, 1)
    string = f"{rounded}%"
    return string.rjust(padding, " ")


class LoadingBar:
    def __init__(self, total: int = 0):
        self._t = total
        self._init_t = total

    def __iter__(self):
        return self

    def __next__(self):
        percentage = ((self._init_t - self._t) / self._init_t) * 100
        line_width = int(
            min(
                TERMINAL_WIDTH() - 2 - NUMBER_PADDING,
                ((TERMINAL_WIDTH() - 2 - NUMBER_PADDING) / self._init_t)
                * (self._init_t - self._t),
            )
        )
        remaining_space = TERMINAL_WIDTH() - 2 - NUMBER_PADDING - line_width
        _clear()
        print("[", end="", flush=False)
        print(f"{line_width * '-'}{remaining_space * ' '}", end="", flush=False)
        print("]", end="", flush=False)
        print(_get_percentage(percentage, NUMBER_PADDING), end="", flush=False)
        print("", end="", flush=True)
        if self._t == 0:
            print("", flush=True)
            raise StopIteration()
        self._t -= 1
        return self._t


for i in LoadingBar(535):
    time.sleep(0.01)
