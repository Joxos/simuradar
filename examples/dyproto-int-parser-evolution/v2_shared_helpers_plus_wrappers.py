def _parse_int(data: bytes, construct_type: object, type_name: str) -> int:
    parser = getattr(construct_type, "parse", None)
    if not callable(parser):
        raise RuntimeError(f"construct {type_name} parser is unavailable")
    parsed = parser(data)
    if isinstance(parsed, int):
        return parsed
    raise RuntimeError(f"construct {type_name} parser returned non-integer value")


def _build_int(value: int, construct_type: object, type_name: str) -> bytes:
    builder = getattr(construct_type, "build", None)
    if not callable(builder):
        raise RuntimeError(f"construct {type_name} builder is unavailable")
    built = builder(value)
    if isinstance(built, bytes):
        return built
    if isinstance(built, bytearray):
        return bytes(built)
    raise RuntimeError(f"construct {type_name} builder returned non-bytes value")


def _parse_int32(data: bytes) -> int:
    return _parse_int(data, Int32ul, "Int32ul")


def _parse_int16(data: bytes) -> int:
    return _parse_int(data, Int16ul, "Int16ul")


def _parse_int8(data: bytes) -> int:
    return _parse_int(data, Int8ul, "Int8ul")


def _build_int32(value: int) -> bytes:
    return _build_int(value, Int32ul, "Int32ul")


def _build_int16(value: int) -> bytes:
    return _build_int(value, Int16ul, "Int16ul")


def _build_int8(value: int) -> bytes:
    return _build_int(value, Int8ul, "Int8ul")
