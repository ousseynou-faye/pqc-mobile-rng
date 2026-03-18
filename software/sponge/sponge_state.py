"""Mutable sponge state container for the prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .permutation import default_permutation


@dataclass
class SpongeState:
    """Hold the current sponge state and apply absorb/permutation steps.

    Bit convention:
    - the full state is stored as one integer on ``rate + capacity`` bits;
    - the rate part occupies the low-order bits of that integer;
    - absorption XORs the provided block into this low-order rate part.
    """

    rate: int = 128
    capacity: int = 128
    permutation: Callable[[int, int], int] = default_permutation

    def __post_init__(self) -> None:
        """Validate dimensions and initialise the zero state."""

        if self.rate <= 0 or self.capacity <= 0:
            raise ValueError("rate et capacity doivent etre > 0.")

        self.size = self.rate + self.capacity
        self.mask = (1 << self.size) - 1
        self.rate_mask = (1 << self.rate) - 1
        self.state = 0

    def reset(self) -> None:
        """Reset the complete sponge state to zero."""

        self.state = 0

    def get_state(self) -> int:
        """Return the full internal state as an integer."""

        return self.state

    def set_state(self, new_state: int) -> None:
        """Overwrite the state after masking it to the configured width."""

        self.state = new_state & self.mask

    def get_rate_part(self) -> int:
        """Return the low-order rate portion of the state."""

        return self.state & self.rate_mask

    def absorb(self, block: int) -> None:
        """XOR one block into the low-order rate portion of the state."""

        self.state ^= block & self.rate_mask
        self.state &= self.mask

    def permute(self) -> None:
        """Apply the configured permutation to the current full state."""

        self.state = self.permutation(self.state, self.size) & self.mask
