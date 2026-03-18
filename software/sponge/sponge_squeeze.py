"""Squeeze phase of the Multiplexed Sponge prototype."""

from __future__ import annotations

from dataclasses import dataclass

from .multiplexed_sequence import MultiplexedSequence
from .sponge_state import SpongeState


@dataclass
class SpongeSqueeze:
    """Derive output blocks from the sponge state and multiplexed sequence."""

    sponge_state: SpongeState
    multiplexed_sequence: MultiplexedSequence

    def squeeze_block(self, block_size: int) -> int:
        """Return one output block from the current sponge state.

        Convention:
        - the extracted state block is taken from the low-order bits of the rate
          part of the state;
        - the multiplexed mask block is assembled MSB-first;
        - the method then permutes the state for the next squeeze step.
        """

        if block_size <= 0:
            raise ValueError("block_size doit etre > 0.")
        if block_size > self.sponge_state.rate:
            raise ValueError("block_size ne doit pas depasser le rate.")

        mask = (1 << block_size) - 1
        state_block = self.sponge_state.get_rate_part() & mask
        mux_block = self.multiplexed_sequence.next_block(block_size, msb_first=True)
        out = (state_block ^ mux_block) & mask

        self.sponge_state.permute()
        return out

    def squeeze_bits(self, n_bits: int) -> list[int]:
        """Return ``n_bits`` single-bit squeeze outputs."""

        if n_bits < 0:
            raise ValueError("n_bits doit etre >= 0.")

        bits = []
        while len(bits) < n_bits:
            block = self.squeeze_block(1)
            bits.append(block & 1)
        return bits

    def squeeze_bytes(self, n_bytes: int) -> bytes:
        """Return ``n_bytes`` bytes produced from 8-bit squeeze blocks."""

        if n_bytes < 0:
            raise ValueError("n_bytes doit etre >= 0.")

        out = bytearray()
        for _ in range(n_bytes):
            out.append(self.squeeze_block(8))
        return bytes(out)
