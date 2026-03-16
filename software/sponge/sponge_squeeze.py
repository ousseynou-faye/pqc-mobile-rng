from __future__ import annotations

from dataclasses import dataclass

from .multiplexed_sequence import MultiplexedSequence
from .sponge_state import SpongeState


@dataclass
class SpongeSqueeze:
    sponge_state: SpongeState
    multiplexed_sequence: MultiplexedSequence

    def squeeze_block(self, block_size: int) -> int:
        if block_size <= 0:
            raise ValueError("block_size doit être > 0.")
        if block_size > self.sponge_state.rate:
            raise ValueError("block_size ne doit pas dépasser le rate.")

        mask = (1 << block_size) - 1

        # Convention retenue :
        # les "premiers bits" de l'état sont pris dans la partie rate (LSB side).
        state_block = self.sponge_state.get_rate_part() & mask

        # Filtrage par la séquence multiplexée
        mux_block = self.multiplexed_sequence.next_block(block_size, msb_first=True)
        out = (state_block ^ mux_block) & mask

        self.sponge_state.permute()
        return out

    def squeeze_bits(self, n_bits: int) -> list[int]:
        if n_bits < 0:
            raise ValueError("n_bits doit être >= 0.")

        bits = []
        while len(bits) < n_bits:
            block = self.squeeze_block(1)
            bits.append(block & 1)
        return bits

    def squeeze_bytes(self, n_bytes: int) -> bytes:
        if n_bytes < 0:
            raise ValueError("n_bytes doit être >= 0.")

        out = bytearray()
        for _ in range(n_bytes):
            out.append(self.squeeze_block(8))
        return bytes(out)