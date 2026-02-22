from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Iterator, Union

from tilegrab.downloader.status import DownloadStatus
from tilegrab.tiles import TileIndex
from tilegrab.tiles import Tile


@dataclass(frozen=True, slots=True)
class ProgressItem:
    tileIndex: TileIndex
    downloadStatus: DownloadStatus
    tileURL: str
    tileImagePath: Path
    tileSourceId: str

    @property
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tileIndex': [self.tileIndex.x, self.tileIndex.y, self.tileIndex.z],
            'downloadStatus': self.downloadStatus,
            'tileURL': self.tileURL,
            'tileImagePath': str(self.tileImagePath),
            'tileSourceId': self.tileSourceId,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProgressItem":
        x, y, z = d['tileIndex']
        return cls(
            tileIndex=TileIndex(x=x, y=y, z=z),
            downloadStatus=DownloadStatus(d['downloadStatus']),
            tileURL=d['tileURL'],
            tileImagePath=Path(d['tileImagePath']),
            tileSourceId=d['tileSourceId'],
        )

class ProgressStore:

    _REQUIRED_KEYS = {
        'tileIndex',
        'downloadStatus',
        'tileURL',
        'tileImagePath',
        'tileSourceId',
    }

    _NAME = ".dlprog.tilegrab"
    _SCHEMA_VERSION = 1

    def __init__(
        self,
        tile_dir: Path,
        initial: Optional[Dict[str, Any]] = None,
        indent: int = 2,
    ):
        self.path = Path(tile_dir) / self._NAME
        self.indent = indent
        self._suspend_flush = False

        self._state: Dict[str, Any] = initial or {
            'schemaVersion': self._SCHEMA_VERSION,
            'lastRunDate': '',
            'lastRunTime': '',
            'progress': [],
        }

        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding='utf-8'))
                if isinstance(loaded, dict):
                    self._state = loaded
            except Exception as e:
                raise RuntimeError(f"Failed to load progress file: {self.path}") from e

        self._last_serial = self._serialize()

    def __iter__(self) -> Iterator[ProgressItem]:
        for p in self._state.get('progress', []):
            yield ProgressItem.from_dict(p)

    def __getitem__(self, index: int) -> ProgressItem:
        return ProgressItem.from_dict(self._state['progress'][index])

    def __len__(self) -> int:
        return len(self._state.get('progress', []))


    def _serialize(self) -> str:
        return json.dumps(self._state, sort_keys=True)

    def _validate_item(self, item: Dict[str, Any]):
        missing = self._REQUIRED_KEYS - item.keys()
        if missing:
            raise ValueError(f"Invalid progress item, missing: {missing}")

    def _flush_if_changed(self):
        if self._suspend_flush:
            return

        serial = self._serialize()
        if serial == self._last_serial:
            return

        payload = json.dumps(
            self._state,
            indent=self.indent,
            ensure_ascii=False,
        )

        tmp = self.path.with_suffix(self.path.suffix + '.tmp')
        tmp.write_text(payload, encoding='utf-8')
        tmp.replace(self.path)

        self._last_serial = serial


    def append(self, item: ProgressItem):
        d = item.to_dict
        self._validate_item(d)
        self._state.setdefault('progress', []).append(d)
        self._flush_if_changed()

    def update(self, index: int, item: ProgressItem):
        prog = self._state.setdefault('progress', [])
        if not (0 <= index < len(prog)):
            raise IndexError(f"Progress index out of range: {index}")

        d = item.to_dict
        self._validate_item(d)
        prog[index] = d
        self._flush_if_changed()

    def remove(self, index: int):
        prog = self._state.setdefault('progress', [])
        if not (0 <= index < len(prog)):
            raise IndexError(f"Progress index out of range: {index}")

        del prog[index]
        self._flush_if_changed()

    def upsert_by_tile_index(self, item: ProgressItem):
        d = item.to_dict
        self._validate_item(d)

        ti = d['tileIndex']
        prog = self._state.setdefault('progress', [])

        for i, p in enumerate(prog):
            if p['tileIndex'] == ti:
                prog[i] = d
                self._flush_if_changed()
                return

        prog.append(d)
        self._flush_if_changed()

    def progress_by_tile(self, item: Tile) -> Union[ProgressItem, None]:

        prog = self._state.setdefault('progress', [])

        for i, p in enumerate(prog):
            if p['tileIndex'] == item:
                return ProgressItem.from_dict(p)

    def suspend_flush(self):
        self._suspend_flush = True

    def resume_flush(self):
        self._suspend_flush = False
        self._flush_if_changed()

