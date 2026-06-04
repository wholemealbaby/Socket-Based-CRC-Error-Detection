"""Unit tests for CRC functions from :mod:`lib.crc`.

Enhancements over the original 11-test suite:
- Parameterized xor tests (7 cases, up from 4 core + 1 edge)
- Parameterized crc_division known-answer tests (7 cases, up from 1)
- Multiple CRC polynomial keys tested in the invariant property (4 keys)
- Additional edge cases: all-zeros data, very long data (10 000 bits),
  non-binary input characterisation, both ``"0"`` and ``"1"`` single-bit inputs
- Helper extracted for random binary string generation
"""

import random

import pytest

from lib.crc import xor, crc_division, DIVISOR


# -- Helpers ----------------------------------------------------------------


def _random_binary(length: int) -> str:
    """Return a random binary string of *length* bits."""
    return "".join(random.choice("01") for _ in range(length))


# -- Tests for xor() --------------------------------------------------------


class TestXor:
    """Tests for :func:`lib.crc.xor`."""

    @pytest.mark.parametrize(
        "a, b, expected",
        [
            ("1100", "1010", "0110"),   # standard mixed bits
            ("111", "111", "000"),      # XOR identity: same bits -> 0
            ("000", "111", "111"),      # XOR with zero: different bits -> 1
            ("1", "1", "0"),            # single bit (both 1)
            ("0", "0", "0"),            # single bit (both 0)
            ("10101", "01010", "11111"),  # alternating pattern
            ("", "", ""),               # both empty
        ],
    )
    def test_xor_cases(self, a: str, b: str, expected: str) -> None:
        """Parametrized xor correctness checks."""
        assert xor(a, b) == expected

    def test_mismatched_length(self) -> None:
        """``xor`` uses :func:`zip`, so it stops at the shorter input.

        No length validation is performed.  This test documents that
        behaviour — the result length matches the shorter argument.
        """
        result = xor("1100", "10")
        # zip("1100", "10") → [('1','1'), ('1','0')] → "01"
        assert result == "01"
        assert len(result) == 2

    def test_long_strings(self) -> None:
        """xor handles long (2000-bit) binary strings efficiently."""
        a = "1" * 1000 + "0" * 1000
        b = "1" * 2000
        result = xor(a, b)
        expected = "0" * 1000 + "1" * 1000
        assert result == expected
        assert len(result) == 2000


class TestCrcDivision:
    """Tests for :func:`lib.crc.crc_division`."""

    # -- Known-answer tests -------------------------------------------

    @pytest.mark.parametrize(
        "data, key, expected",
        [
            ("100100", "1101", "001"),     # standard worked example (CRC-3)
            ("100100", "1011", "101"),     # alternate CRC-3 polynomial
            ("1101", "1011", "001"),       # data == key prefix pattern
            ("1", "11", "1"),              # minimal key length 2
            ("0", "11", "0"),              # zero data with 2-bit key
            ("1010", "111", "10"),         # CRC-2 polynomial (key length 3)
            ("11111111", "1001", "011"),   # CRC-3 all-ones data
        ],
    )
    def test_known_cases(self, data: str, key: str, expected: str) -> None:
        """Parametrized CRC division known-answer tests."""
        assert crc_division(data, key) == expected

    # -- Remainder length invariant ------------------------------------

    def test_remainder_length(self) -> None:
        """Remainder length is always ``len(key) - 1`` for any data."""
        expected_len = len(DIVISOR) - 1
        data_samples = [
            "0",
            "1",
            "00",
            "101",
            "100100",
            "11111111",
            "1010101010",
            "1" * 20,
            "00000",  # all-zeros (added for edge coverage)
        ]
        for data in data_samples:
            remainder = crc_division(data, DIVISOR)
            assert len(remainder) == expected_len, (
                f"Expected length {expected_len}, got {len(remainder)} "
                f"for data={data!r}"
            )

    # -- Property-based invariant --------------------------------------

    def test_codeword_validity_property(self) -> None:
        """CRC invariant: ``crc_division(data + remainder, key)`` yields all zeros.

        Verified across **4 different polynomials** to ensure the property
        holds regardless of the key used.
        """
        random.seed(42)
        keys = ["1101", "1011", "111", "1001"]

        for key in keys:
            for _ in range(10):
                length = random.randint(4, 16)
                data = _random_binary(length)
                remainder = crc_division(data, key)
                codeword = data + remainder
                result = crc_division(codeword, key)
                assert result == "0" * (len(key) - 1), (
                    f"CRC invariant violated for data={data!r}, key={key!r}, "
                    f"remainder={remainder!r}, got result={result!r}"
                )

    # -- Edge-case inputs ----------------------------------------------

    def test_empty_string(self) -> None:
        """Empty data produces a zero remainder of the expected length."""
        remainder = crc_division("", DIVISOR)
        assert isinstance(remainder, str)
        assert len(remainder) == len(DIVISOR) - 1
        assert remainder == "0" * (len(DIVISOR) - 1)

    def test_all_zeros_data(self) -> None:
        """All-zero binary data produces a zero remainder."""
        remainder = crc_division("00000", DIVISOR)
        assert remainder == "0" * (len(DIVISOR) - 1)
        assert len(remainder) == len(DIVISOR) - 1

    def test_single_bit_data(self) -> None:
        """CRC division works with both single-bit inputs ``'0'`` and ``'1'``."""
        for bit in ("0", "1"):
            remainder = crc_division(bit, DIVISOR)
            assert len(remainder) == len(DIVISOR) - 1, (
                f"Failed for bit={bit!r}"
            )

    def test_data_shorter_than_key(self) -> None:
        """CRC division works when data is shorter than the key."""
        remainder = crc_division("11", DIVISOR)
        assert len(remainder) == len(DIVISOR) - 1

    def test_very_long_data(self) -> None:
        """CRC division handles 10 000-bit data without error."""
        data = "1" * 5000 + "0" * 5000
        remainder = crc_division(data, DIVISOR)
        assert len(remainder) == len(DIVISOR) - 1

    def test_non_binary_input(self) -> None:
        """Non-binary characters are silently ignored (characterisation test).

        Since :func:`crc_division` only checks ``== \"1\"`` to trigger XOR,
        alphabetic characters are treated the same as ``\"0\"`` -- no
        division step is ever taken, so the remainder is all zeros.
        """
        remainder = crc_division("abc", DIVISOR)
        assert isinstance(remainder, str)
        assert len(remainder) == len(DIVISOR) - 1
        assert remainder == "0" * (len(DIVISOR) - 1)
