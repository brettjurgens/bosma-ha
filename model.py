from __future__ import annotations

from dataclasses import dataclass

from bosma.lock import AegisLock


@dataclass
class BosmaData:
    title: str
    lock: AegisLock