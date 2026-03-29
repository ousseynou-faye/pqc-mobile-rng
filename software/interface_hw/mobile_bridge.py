from __future__ import annotations

import platform
import struct
from dataclasses import dataclass
from enum import IntEnum

from software.api import get_rng_service
from software.api.exceptions import RNGInvalidLengthError, RNGNotInitializedError

FRAME_MAGIC = b"PMBR"
FRAME_VERSION = 1
FRAME_HEADER = struct.Struct("<4sBBHIII")
HEALTH_PAYLOAD = struct.Struct("<BBBBI")
MAX_BRIDGE_ADDITIONAL_INPUT = 1024
MAX_BRIDGE_GENERATE_BYTES = 4096


class MobileOpcode(IntEnum):
    INSTANTIATE = 1
    GENERATE = 2
    RESEED = 3
    HEALTH = 4
    ZEROIZE = 5
    EXPORT_STATE = 6
    IMPORT_STATE = 7


class MobileStatus(IntEnum):
    OK = 0
    INVALID_ARGUMENT = 1
    NOT_INITIALIZED = 2
    RESEED_REQUIRED = 3
    HEALTH_ERROR = 4
    UNSUPPORTED = 5
    INTERNAL_ERROR = 255


class MobileHealthCode(IntEnum):
    OK = 0
    WARNING = 1
    ERROR = 2
    UNKNOWN = 255


class MobileLifecycleCode(IntEnum):
    ABSENT_OR_UNKNOWN = 0
    READY = 1
    NEED_RESEED = 2
    FAIL_STOP = 3
    ZEROIZED = 4
    OTHER = 255


@dataclass(slots=True)
class MobileFrame:
    code: int
    request_id: int
    payload: bytes = b""
    flags: int = 0
    detail_code: int = 0

    def encode(self) -> bytes:
        header = FRAME_HEADER.pack(
            FRAME_MAGIC,
            FRAME_VERSION,
            int(self.code),
            self.flags,
            self.request_id,
            len(self.payload),
            self.detail_code,
        )
        return header + self.payload

    @classmethod
    def decode(cls, data: bytes) -> "MobileFrame":
        if len(data) < FRAME_HEADER.size:
            raise ValueError("Frame tronquee.")
        magic, version, code, flags, request_id, payload_len, detail_code = FRAME_HEADER.unpack(
            data[: FRAME_HEADER.size]
        )
        if magic != FRAME_MAGIC:
            raise ValueError("Magic mobile invalide.")
        if version != FRAME_VERSION:
            raise ValueError("Version mobile non supportee.")
        if flags != 0:
            raise ValueError("Flags reserves non supportes.")
        payload = data[FRAME_HEADER.size :]
        if len(payload) != payload_len:
            raise ValueError("Longueur de payload incoherente.")
        return cls(code=code, request_id=request_id, payload=payload, flags=flags, detail_code=detail_code)


def _pack_var_bytes(data: bytes) -> bytes:
    return struct.pack("<H", len(data)) + data


def _unpack_var_bytes(payload: bytes, *, offset: int = 0) -> tuple[bytes, int]:
    if len(payload) < offset + 2:
        raise ValueError("Payload tronque.")
    length = struct.unpack_from("<H", payload, offset)[0]
    start = offset + 2
    end = start + length
    if len(payload) < end:
        raise ValueError("Payload tronque.")
    return payload[start:end], end


def encode_instantiate_request(request_id: int, *, personalization: bytes = b"") -> bytes:
    return MobileFrame(
        code=MobileOpcode.INSTANTIATE,
        request_id=request_id,
        payload=_pack_var_bytes(personalization),
    ).encode()


def encode_generate_request(request_id: int, *, length: int, additional_input: bytes = b"") -> bytes:
    payload = struct.pack("<I", length) + _pack_var_bytes(additional_input)
    return MobileFrame(code=MobileOpcode.GENERATE, request_id=request_id, payload=payload).encode()


def encode_reseed_request(request_id: int, *, additional_input: bytes = b"") -> bytes:
    return MobileFrame(
        code=MobileOpcode.RESEED,
        request_id=request_id,
        payload=_pack_var_bytes(additional_input),
    ).encode()


def encode_health_request(request_id: int) -> bytes:
    return MobileFrame(code=MobileOpcode.HEALTH, request_id=request_id).encode()


def encode_zeroize_request(request_id: int) -> bytes:
    return MobileFrame(code=MobileOpcode.ZEROIZE, request_id=request_id).encode()


def collect_mobile_environment() -> dict[str, object]:
    machine = platform.machine() or "unknown"
    return {
        "machine": machine,
        "processor": platform.processor() or "unknown",
        "system": platform.system(),
        "platform": platform.platform(),
        "is_arm": machine.lower() in {"arm64", "aarch64", "armv7l"},
        "bridge_type": "python_transition_contract",
        "native_wrapper_present": False,
    }


def _status_from_exception(exc: Exception) -> MobileStatus:
    if isinstance(exc, ValueError):
        return MobileStatus.INVALID_ARGUMENT
    if isinstance(exc, RNGInvalidLengthError):
        return MobileStatus.INVALID_ARGUMENT
    if isinstance(exc, RNGNotInitializedError):
        return MobileStatus.NOT_INITIALIZED
    return MobileStatus.INTERNAL_ERROR


def _decode_health_code(status: str | None) -> MobileHealthCode:
    if status == "ok":
        return MobileHealthCode.OK
    if status == "warning":
        return MobileHealthCode.WARNING
    if status == "error":
        return MobileHealthCode.ERROR
    return MobileHealthCode.UNKNOWN


def _decode_lifecycle_code(state: str | None) -> MobileLifecycleCode:
    if state == "ready":
        return MobileLifecycleCode.READY
    if state == "need_reseed":
        return MobileLifecycleCode.NEED_RESEED
    if state == "fail_stop":
        return MobileLifecycleCode.FAIL_STOP
    if state == "zeroized":
        return MobileLifecycleCode.ZEROIZED
    if state in {None, ""}:
        return MobileLifecycleCode.ABSENT_OR_UNKNOWN
    return MobileLifecycleCode.OTHER


class MobileBridge:
    """Reference binary contract for a future mobile wrapper.

    This class is intentionally Python-only. It does not claim JNI, NDK, Rust,
    or C integration. It exists to freeze operation semantics and buffer
    handling before a native layer is introduced.
    """

    def __init__(self) -> None:
        self._service = get_rng_service()

    def handle_frame(self, frame_bytes: bytes) -> bytes:
        try:
            frame = MobileFrame.decode(frame_bytes)
        except Exception:
            return MobileFrame(
                code=MobileStatus.INVALID_ARGUMENT,
                request_id=0,
            ).encode()

        try:
            opcode = MobileOpcode(frame.code)
        except ValueError:
            return MobileFrame(
                code=MobileStatus.UNSUPPORTED,
                request_id=frame.request_id,
            ).encode()

        try:
            if opcode == MobileOpcode.INSTANTIATE:
                self._handle_instantiate(frame.payload)
                return MobileFrame(code=MobileStatus.OK, request_id=frame.request_id).encode()
            if opcode == MobileOpcode.GENERATE:
                data = self._handle_generate(frame.payload)
                return MobileFrame(code=MobileStatus.OK, request_id=frame.request_id, payload=data).encode()
            if opcode == MobileOpcode.RESEED:
                self._handle_reseed(frame.payload)
                return MobileFrame(code=MobileStatus.OK, request_id=frame.request_id).encode()
            if opcode == MobileOpcode.HEALTH:
                payload = self._handle_health()
                return MobileFrame(code=MobileStatus.OK, request_id=frame.request_id, payload=payload).encode()
            if opcode == MobileOpcode.ZEROIZE:
                self._service.zeroize()
                return MobileFrame(code=MobileStatus.OK, request_id=frame.request_id).encode()
            return MobileFrame(code=MobileStatus.UNSUPPORTED, request_id=frame.request_id).encode()
        except Exception as exc:
            return MobileFrame(
                code=_status_from_exception(exc),
                request_id=frame.request_id,
            ).encode()

    def _handle_instantiate(self, payload: bytes) -> None:
        personalization, offset = _unpack_var_bytes(payload)
        if offset != len(payload):
            raise ValueError("Payload instantiate invalide.")
        self._service.instantiate_rng(personalization=personalization)

    def _handle_generate(self, payload: bytes) -> bytes:
        if len(payload) < 4:
            raise ValueError("Payload generate invalide.")
        length = struct.unpack_from("<I", payload, 0)[0]
        additional_input, offset = _unpack_var_bytes(payload, offset=4)
        if offset != len(payload):
            raise ValueError("Payload generate invalide.")
        if self._service.drbg is None:
            raise RNGNotInitializedError("Bridge mobile non instantie.")
        if length == 0 or length > MAX_BRIDGE_GENERATE_BYTES:
            raise RNGInvalidLengthError("length invalide pour le bridge mobile.")
        if len(additional_input) > MAX_BRIDGE_ADDITIONAL_INPUT:
            raise RNGInvalidLengthError("additional_input trop long pour le bridge mobile.")
        return self._service.generate_bytes(length, additional_input=additional_input)

    def _handle_reseed(self, payload: bytes) -> None:
        additional_input, offset = _unpack_var_bytes(payload)
        if offset != len(payload):
            raise ValueError("Payload reseed invalide.")
        if self._service.drbg is None:
            raise RNGNotInitializedError("Bridge mobile non instantie.")
        if len(additional_input) > MAX_BRIDGE_ADDITIONAL_INPUT:
            raise RNGInvalidLengthError("additional_input trop long pour le bridge mobile.")
        self._service.reseed_rng(additional_input=additional_input)

    def _handle_health(self) -> bytes:
        status = self._service.sdk_status()
        flags = 0
        if status.get("instantiated"):
            flags |= 1 << 0
        if status.get("reseed_supported"):
            flags |= 1 << 1
        return HEALTH_PAYLOAD.pack(
            int(bool(status.get("initialized"))),
            int(bool(status.get("state_available"))),
            int(_decode_health_code(status.get("health_status"))),
            int(_decode_lifecycle_code(status.get("lifecycle_state"))),
            flags,
        )


def decode_health_payload(payload: bytes) -> dict[str, int | bool]:
    if len(payload) != HEALTH_PAYLOAD.size:
        raise ValueError("Payload health invalide.")
    initialized, state_available, health_code, lifecycle_code, capability_flags = HEALTH_PAYLOAD.unpack(payload)
    return {
        "initialized": bool(initialized),
        "state_available": bool(state_available),
        "health_code": health_code,
        "lifecycle_code": lifecycle_code,
        "capability_flags": capability_flags,
    }
