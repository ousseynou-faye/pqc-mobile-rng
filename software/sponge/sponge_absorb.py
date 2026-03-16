from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .multiplexed_sequence import MultiplexedSequence
from .sponge_state import SpongeState


@dataclass
class SpongeAbsorb:
    sponge_state: SpongeState
    multiplexed_sequence: MultiplexedSequence

    def absorb_block(self, block: int, block_size: int) -> int:
        if block_size <= 0:
            raise ValueError("block_size doit être > 0.")
        if block_size > self.sponge_state.rate:
            raise ValueError("block_size ne doit pas dépasser le rate.")

        mask = (1 << block_size) - 1

        # Filtrage du bloc par la séquence multiplexée
        mux_block = self.multiplexed_sequence.next_block(block_size, msb_first=True)
        mixed_block = (block ^ mux_block) & mask

        self.sponge_state.absorb(mixed_block)
        self.sponge_state.permute()

        return mixed_block

    def absorb_blocks(self, blocks: Iterable[int], block_size: int) -> list[int]:
        mixed = []
        for block in blocks:
            mixed.append(self.absorb_block(block, block_size))
        return mixed