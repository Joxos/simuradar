class IntWidth(Enum):
    INT8 = Int8ul
    INT16 = Int16ul
    INT32 = Int32ul


def _parse_int(data: bytes, width: IntWidth) -> int:
    construct_type = width.value
    parser = getattr(construct_type, "parse", None)
    if not callable(parser):
        raise RuntimeError(f"construct {width.name} parser is unavailable")
    parsed = parser(data)
    if isinstance(parsed, int):
        return parsed
    raise RuntimeError(f"construct {width.name} parser returned non-integer value")


def _build_int(value: int, width: IntWidth) -> bytes:
    construct_type = width.value
    builder = getattr(construct_type, "build", None)
    if not callable(builder):
        raise RuntimeError(f"construct {width.name} builder is unavailable")
    built = builder(value)
    if isinstance(built, bytes):
        return built
    if isinstance(built, bytearray):
        return bytes(built)
    raise RuntimeError(f"construct {width.name} builder returned non-bytes value")
