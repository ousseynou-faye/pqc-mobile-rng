from software.lfsr.recurrence_sequences import RecurrenceSequence
from software.sponge.multiplexed_sponge import MultiplexedSponge

seq_s = RecurrenceSequence(degree=8, seed=0xA5)
seq_t = RecurrenceSequence(degree=9, seed=0x101)

sponge = MultiplexedSponge(
    seq_s=seq_s,
    seq_t=seq_t,
    l=4,
    rate=32,
    capacity=32,
)

# Absorption de blocs de 8 bits
sponge.absorb_blocks([0x12, 0x34, 0x56, 0x78], block_size=8)

# Génération de sortie
bits = sponge.squeeze_bits(256)
data = sponge.squeeze_bytes(32)

print(bits)
print(data.hex())