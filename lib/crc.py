"""
CRC (Cyclic Redundancy Check) algorithm module.

Provides binary polynomial division utilities for CRC error detection.
"""

DIVISOR: str = "1101"
"""Default CRC polynomial key (binary string)."""


def xor(dividend: str, divisor: str) -> str:
    """Perform a bitwise XOR on two equal-length binary strings.

    Args:
        dividend: First binary string (e.g., ``"1100"``).
        divisor:  Second binary string (e.g., ``"1010"``).

    Returns:
        The XOR result as a binary string of the same length.

    Example:
        >>> xor("1100", "1010")
        '0110'
    """
    return "".join("1" if a != b else "0" for a, b in zip(dividend, divisor))


def crc_division(data: str, key: str) -> str:
    """Perform binary polynomial (modulo-2) division to compute a CRC remainder.

    The algorithm appends ``len(key) - 1`` zeros to the data, then walks through
    each bit of the original data. Whenever a ``1`` is encountered, the next
    ``len(key)`` bits are XORed with the key.  After processing every original
    data bit the last ``len(key) - 1`` bits of the working value form the CRC
    remainder.

    Args:
        data: Binary string representing the original message.
        key:  Binary string representing the CRC polynomial divisor.

    Returns:
        CRC remainder as a binary string of length ``len(key) - 1``.

    Example:
        >>> crc_division("100100", "1101")
        '001'

    A valid codeword (``data + remainder``) will always produce a zero remainder:
        >>> crc_division("100100001", "1101")
        '000'
    """
    # Append len(key) - 1 zeros to form the dividend
    dividend: list[str] = list(data + "0" * (len(key) - 1))

    # Walk through each bit of the original data
    for i in range(len(data)):
        if dividend[i] == "1":
            # XOR the next len(key) bits with the key
            segment = "".join(dividend[i : i + len(key)])
            xored = xor(segment, key)
            for j, bit in enumerate(xored):
                dividend[i + j] = bit

    # The last len(key) - 1 bits are the CRC remainder
    return "".join(dividend[-(len(key) - 1) :])
