import logging
import sys

# Normal colors
BLACK   = "\033[30m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
GRAY    = "\033[90m"
WHITE  = "\033[37m"

# Bright colors
BBLACK   = "\033[90m"
BRED     = "\033[91m"
BGREEN   = "\033[92m"
BYELLOW  = "\033[93m"
BBLUE    = "\033[94m"
BMAGENTA = "\033[95m"
BCYAN    = "\033[96m"
BGRAY    = "\033[97m"
BWHITE = "\033[97m"

RESET = "\033[0m"


class CLILogFormatter(logging.Formatter):
    NAME_WIDTH = 20
    LEVEL_MAP = {
        logging.CRITICAL: f'{RED}‼ {RESET}',
        logging.ERROR:    f'{RED}✖ {RESET}',
        logging.WARNING:  f'{YELLOW}⚠ {RESET}',
        logging.INFO:     f'{BLUE}• {RESET}',
        logging.DEBUG:    f'{GRAY}· {RESET}',
        logging.NOTSET:   f'{CYAN}- {RESET}',
    }

    def __init__(self, fmt=None):
        super().__init__(fmt or '   %(level_icon)s %(message)s')

    def format(self, record):
        record.level_icon = self.LEVEL_MAP.get(record.levelno, '?')
        short = record.name.rsplit('.', 1)[-1]
        record.short_name = f"{short:<{self.NAME_WIDTH}}"

        return super().format(record)

class FileLogFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(
            '%(asctime)s %(levelname)s %(name)s - %(message)s'
        )

def create_cli_handler(level=logging.INFO):
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(CLILogFormatter())
    return handler

def create_file_handler(path="tilegrab.log", level=logging.DEBUG):
    handler = logging.FileHandler(path)
    handler.setLevel(level)
    handler.setFormatter(FileLogFormatter())
    return handler

def setup_logging(
    enable_cli=True,
    enable_file=True,
    level=logging.INFO
):
    handlers = []

    if enable_cli:
        handlers.append(create_cli_handler(level))

    if enable_file:
        handlers.append(create_file_handler(level=level))

    logging.basicConfig(
        level=level,
        handlers=handlers,
    )
