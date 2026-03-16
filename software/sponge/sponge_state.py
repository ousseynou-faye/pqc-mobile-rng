from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .permutation import default_permutation


@dataclass
class SpongeState:
    rate: int = 128
    capacity: int = 128
    permutation: Callable[[int, int], int] = default_permutation

    def __post_init__(self) -> None:
        if self.rate <= 0 or self.capacity <= 0:
            raise ValueError("rate et capacity doivent être > 0.")

        self.size = self.rate + self.capacity
        self.mask = (1 << self.size) - 1
        self.rate_mask = (1 << self.rate) - 1
        self.state = 0

    def reset(self) -> None:
        self.state = 0

    def get_state(self) -> int:
        return self.state

    def set_state(self, new_state: int) -> None:
        self.state = new_state & self.mask

    def get_rate_part(self) -> int:
        return self.state & self.rate_mask

    def absorb(self, block: int) -> None:
        self.state ^= (block & self.rate_mask)
        self.state &= self.mask

    def permute(self) -> None:
        self.state = self.permutation(self.state, self.size) & self.mask