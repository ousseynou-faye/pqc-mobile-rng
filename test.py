from software.lfsr.lfsr_core import LFSR
from software.lfsr.primitive_polynomials import get_polynomial
from software.lfsr.recurrence_sequences import RecurrenceSequence



seq = RecurrenceSequence(
    degree=128,
    seed=0xACE1
)
S = RecurrenceSequence(64, 0x12345678)
T = RecurrenceSequence(128, 0x87654321)
bits = seq.generate_sequence(32)

print(S.generate_sequence(256))

