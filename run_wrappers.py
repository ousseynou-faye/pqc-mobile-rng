from software.api import instantiate_rng, generate_bytes, get_rng_health

instantiate_rng(personalization=b"wrapper")
data = generate_bytes(32)
health = get_rng_health()

print("Octets:", data.hex())
print("Health:", health)