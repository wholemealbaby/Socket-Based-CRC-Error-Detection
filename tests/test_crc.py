"""Unit tests for CRC functions from :mod:`lib.crc`."""

from lib.crc import xor, crc_division, DIVISOR


class TestXor:
    """Tests for :func:`lib.crc.xor`."""

    def test_standard_case(self) -> None:
        """``xor("1100", "1010")`` → ``"0110"``."""
        assert xor("1100", "1010") == "0110"

    def test_all_bits_set(self) -> None:
        """XOR of two all-ones strings yields all zeros."""
        assert xor("111", "111") == "000"

    def test_no_bits_set(self) -> None:
        """XOR of all-zeros with all-ones yields the all-ones string."""
        assert xor("000", "111") == "111"

    def test_single_bit(self) -> None:
        """Single-bit XOR: ``xor("1", "1")`` → ``"0"``."""
        assert xor("1", "1") == "0"

    def test_mismatched_length(self) -> None:
        """``xor`` uses :func:`zip`, so it stops at the shorter input.

        No length validation is performed.  This test documents that
        behaviour — the result length matches the shorter argument.
        """
        result = xor("1100", "10")
        # zip("1100", "10") → [('1','1'), ('1','0')] → "01"
        assert result == "01"
        assert len(result) == 2


class TestCrcDivision:
    """Tests for :func:`lib.crc.crc_division`."""

    def test_known_case(self) -> None:
        """``crc_division("100100", "1101")`` → ``"001"``."""
        assert crc_division("100100", "1101") == "001"

    def test_remainder_length(self) -> None:
        """The remainder length is always ``len(key) - 1``."""
        key = DIVISOR
        expected_len = len(key) - 1
        data_samples = [
            "0",
            "1",
            "00",
            "101",
            "100100",
            "11111111",
            "1010101010",
            "1" * 20,
        ]
        for data in data_samples:
            remainder = crc_division(data, key)
            assert len(remainder) == expected_len, (
                f"Expected length {expected_len}, got {len(remainder)} "
                f"for data={data!r}"
            )

    def test_codeword_validity_property(self) -> None:
        """CRC invariant: ``crc_division(data + remainder, key)`` yields all zeros."""
        import random

        random.seed(42)
        key = DIVISOR

        for _ in range(20):
            length = random.randint(4, 16)
            data = "".join(random.choice("01") for _ in range(length))
            remainder = crc_division(data, key)
            codeword = data + remainder
            result = crc_division(codeword, key)
            assert result == "0" * (len(key) - 1), (
                f"CRC invariant violated for data={data!r}, "
                f"remainder={remainder!r}, got result={result!r}"
            )

    def test_empty_string(self) -> None:
        """An empty data string produces a zero remainder of the expected length."""
        remainder = crc_division("", DIVISOR)
        assert isinstance(remainder, str)
        assert len(remainder) == len(DIVISOR) - 1
        # With no data bits to process, the dividend is just the appended zeros
        assert remainder == "0" * (len(DIVISOR) - 1)

    def test_single_bit_data(self) -> None:
        """CRC division works with single-bit data."""
        remainder = crc_division("1", DIVISOR)
        assert len(remainder) == len(DIVISOR) - 1

    def test_data_shorter_than_key(self) -> None:
        """CRC division works when the data is shorter than the key."""
        # "11" has length 2, DIVISOR "1101" has length 4
        remainder = crc_division("11", DIVISOR)
        assert len(remainder) == len(DIVISOR) - 1
