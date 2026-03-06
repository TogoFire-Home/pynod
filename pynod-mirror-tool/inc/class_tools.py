# This file is part of the PyNOD-Mirror-Tool project,
# the latest version of which can be downloaded at:
# https://github.com/Scorpikor/pynod-mirror-tool

class TColor:
    # Use: print(TColor.RED + "TEXT" + TColor.ENDC)
    GRAY = str("\033[1;30m")
    RED = str("\033[1;31m")
    GREEN = str("\033[1;32m")
    YELLOW = str("\033[1;33m")
    BLUE = str("\033[1;34m")
    MAGENTA = str("\033[1;35m")
    CYAN = str("\033[1;36m")
    WHITE = str("\033[1;37m")
    CRIMSON = str("\033[1;38m")
    ENDC = str("\033[0m")
    BOLD = str("\033[1m")
    LINE = str("=" * 70)
    UNDERLINE = str("\033[4m")
