from enum import IntEnum

class DownloadStatus(IntEnum):
    SUCCESS = 200
    SKIP_AND_EXISTS = 100
    SKIP = 101
    UNDEFINED = 900
    ALREADY_EXISTS = 500
    FAILED = 401
    EMPTY = 400

