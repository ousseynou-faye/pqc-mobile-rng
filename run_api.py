from software.api import RNGService

service = RNGService()
service.instantiate_rng(personalization=b"memoire-demo")

data = service.generate_bytes(32)
blob = service.checkpoint_state(payload_metadata={"caller": "script"})

print("Octets:", data.hex())
print("Blob:", blob.blob_id)
print("Health:", service.health_status())