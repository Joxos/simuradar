def _parse_int32(data: bytes) -> int:
    parser = getattr(Int32ul, "parse", None)
    if not callable(parser):
        raise RuntimeError("construct Int32ul parser is unavailable")
    parsed = parser(data)
    if isinstance(parsed, int):
        return parsed
    raise RuntimeError("construct Int32ul parser returned non-integer value")


def _parse_int16(data: bytes) -> int:
    parser = getattr(Int16ul, "parse", None)
    if not callable(parser):
        raise RuntimeError("construct Int16ul parser is unavailable")
    parsed = parser(data)
    if isinstance(parsed, int):
        return parsed
    raise RuntimeError("construct Int16ul parser returned non-integer value")


def _parse_int8(data: bytes) -> int:
    parser = getattr(Int8ul, "parse", None)
    if not callable(parser):
        raise RuntimeError("construct Int8ul parser is unavailable")
    parsed = parser(data)
    if isinstance(parsed, int):
        return parsed
    raise RuntimeError("construct Int8ul parser returned non-integer value")


def _build_int32(value: int) -> bytes:
    builder = getattr(Int32ul, "build", None)
    if not callable(builder):
        raise RuntimeError("construct Int32ul builder is unavailable")
    built = builder(value)
    if isinstance(built, bytes):
        return built
    if isinstance(built, bytearray):
        return bytes(built)
    raise RuntimeError("construct Int32ul builder returned non-bytes value")


def _build_int16(value: int) -> bytes:
    builder = getattr(Int16ul, "build", None)
    if not callable(builder):
        raise RuntimeError("construct Int16ul builder is unavailable")
    built = builder(value)
    if isinstance(built, bytes):
        return built
    if isinstance(built, bytearray):
        return bytes(built)
    raise RuntimeError("construct Int16ul builder returned non-bytes value")


def _build_int8(value: int) -> bytes:
    builder = getattr(Int8ul, "build", None)
    if not callable(builder):
        raise RuntimeError("construct Int8ul builder is unavailable")
    built = builder(value)
    if isinstance(built, bytes):
        return built
    if isinstance(built, bytearray):
        return bytes(built)
    raise RuntimeError("construct Int8ul builder returned non-bytes value")
