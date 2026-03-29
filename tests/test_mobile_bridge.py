from __future__ import annotations

from software.api import get_rng_service
from software.api.rng_service import RNGServiceConfig, StateConfig
from software.interface_hw.mobile_bridge import (
    MobileBridge,
    MobileFrame,
    MobileHealthCode,
    MobileLifecycleCode,
    MobileOpcode,
    MobileStatus,
    collect_mobile_environment,
    decode_health_payload,
    encode_generate_request,
    encode_health_request,
    encode_instantiate_request,
    encode_reseed_request,
    encode_zeroize_request,
)


def configure_mobile_service(tmp_path, name: str = "mobile_bridge"):
    config = RNGServiceConfig(
        state=StateConfig(
            root_dir=tmp_path / "tests_runtime_mobile",
            device_id=f"{name}-device",
            namespace=f"{name}-namespace",
            blob_id=f"{name}-blob",
            checkpoint_metadata={"purpose": f"{name}-checkpoint"},
        )
    )
    return get_rng_service(reset=True, config=config)


def test_mobile_frame_round_trip():
    frame = MobileFrame(code=MobileOpcode.HEALTH, request_id=7, payload=b"abc")

    decoded = MobileFrame.decode(frame.encode())

    assert decoded.code == MobileOpcode.HEALTH
    assert decoded.request_id == 7
    assert decoded.payload == b"abc"


def test_mobile_bridge_generate_requires_instantiate(tmp_path):
    configure_mobile_service(tmp_path, "generate_requires_init")
    bridge = MobileBridge()

    response = MobileFrame.decode(bridge.handle_frame(encode_generate_request(3, length=16)))

    assert response.code == MobileStatus.NOT_INITIALIZED
    assert response.request_id == 3


def test_mobile_bridge_lifecycle_round_trip(tmp_path):
    configure_mobile_service(tmp_path, "lifecycle")
    bridge = MobileBridge()

    instantiate = MobileFrame.decode(bridge.handle_frame(encode_instantiate_request(1, personalization=b"mob")))
    generated = MobileFrame.decode(bridge.handle_frame(encode_generate_request(2, length=24)))
    reseeded = MobileFrame.decode(bridge.handle_frame(encode_reseed_request(4, additional_input=b"fresh")))
    health = MobileFrame.decode(bridge.handle_frame(encode_health_request(5)))
    zeroized = MobileFrame.decode(bridge.handle_frame(encode_zeroize_request(6)))

    assert instantiate.code == MobileStatus.OK
    assert generated.code == MobileStatus.OK
    assert len(generated.payload) == 24
    assert reseeded.code == MobileStatus.OK
    assert zeroized.code == MobileStatus.OK

    health_payload = decode_health_payload(health.payload)
    assert health.code == MobileStatus.OK
    assert health_payload["initialized"] is True
    assert health_payload["health_code"] in {
        MobileHealthCode.OK,
        MobileHealthCode.WARNING,
        MobileHealthCode.ERROR,
    }
    assert health_payload["lifecycle_code"] == MobileLifecycleCode.READY


def test_mobile_bridge_rejects_reserved_flags():
    encoded = MobileFrame(code=MobileOpcode.HEALTH, request_id=9, flags=1).encode()

    response = MobileFrame.decode(MobileBridge().handle_frame(encoded))

    assert response.code == MobileStatus.INVALID_ARGUMENT


def test_mobile_environment_marks_python_transition_contract():
    environment = collect_mobile_environment()

    assert environment["bridge_type"] == "python_transition_contract"
    assert environment["native_wrapper_present"] is False
