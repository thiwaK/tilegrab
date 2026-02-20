from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DownloadConfig:
    timeout: float = 15.0
    max_retries: int = 5
    backoff_factor: float = 0.3
    overwrite: bool = True