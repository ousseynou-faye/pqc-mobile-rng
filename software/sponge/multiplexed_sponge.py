"""High-level orchestrator for the Multiplexed Sponge research prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional

from ..lfsr.recurrence_sequences import RecurrenceSequence
from .multiplexed_sequence import MultiplexedSequence
from .sponge_absorb import SpongeAbsorb
from .sponge_squeeze import SpongeSqueeze
from .sponge_state import SpongeState


@dataclass
class MultiplexedSponge:
    """Coordinate phi, multiplexing, absorption and squeeze operations.

    This class intentionally stays at the level of the mathematical prototype.
    It is not yet an API boundary, a DRBG, an entropy source or a TEE-facing
    component.
    """

    seq_s: RecurrenceSequence
    seq_t: RecurrenceSequence
    l: int
    rate: int = 128
    capacity: int = 128
    phi_offsets: Optional[tuple[int, ...]] = None
    permutation: Optional[Callable[[int, int], int]] = None

    state: SpongeState = field(init=False)
    sequence: MultiplexedSequence = field(init=False)
    absorber: SpongeAbsorb = field(init=False)
    squeezer: SpongeSqueeze = field(init=False)

    def __post_init__(self) -> None:
        """Instantiate the state, multiplexed sequence and phase helpers."""

        if self.permutation is None:
            self.state = SpongeState(rate=self.rate, capacity=self.capacity)
        else:
            self.state = SpongeState(
                rate=self.rate,
                capacity=self.capacity,
                permutation=self.permutation,
            )

        self.sequence = MultiplexedSequence(
            seq_s=self.seq_s,
            seq_t=self.seq_t,
            l=self.l,
            phi_offsets=self.phi_offsets,
            msb_first=True,
        )

        self.absorber = SpongeAbsorb(
            sponge_state=self.state,
            multiplexed_sequence=self.sequence,
        )

        self.squeezer = SpongeSqueeze(
            sponge_state=self.state,
            multiplexed_sequence=self.sequence,
        )

    def absorb_blocks(self, blocks: Iterable[int], block_size: int) -> list[int]:
        """Absorb a sequence of blocks and return the mixed blocks used."""

        return self.absorber.absorb_blocks(blocks, block_size)

    def squeeze_bits(self, n_bits: int) -> list[int]:
        """Return ``n_bits`` output bits from the squeeze phase."""

        return self.squeezer.squeeze_bits(n_bits)

    def squeeze_bytes(self, n_bytes: int) -> bytes:
        """Return ``n_bytes`` output bytes from the squeeze phase."""

        return self.squeezer.squeeze_bytes(n_bytes)
