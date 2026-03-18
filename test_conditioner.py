from software.conditioner import EntropyMixer

mixer = EntropyMixer(
    toeplitz_output_bits=256,
    shake_output_bytes=32,
)

result = mixer.condition_raw_data(
    raw_data=b"demo entropy block",
    metadata={"source": "src", "ready": True},
    personalization=b"memoire-m2",
)

print("Toeplitz :", result.toeplitz_output.hex())
print("Seedinit :", result.seedinit.hex())

