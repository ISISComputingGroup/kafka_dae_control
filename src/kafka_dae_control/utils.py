"""Bitwise utilities."""


def or_two_int_lists(x: list[int], y: list[int]) -> int:
    """A bitwise OR of two lists of ints.

    This iterates through the elements and ORs them together,
    resulting in a single integer.

    Args:
        x: the first list to OR
        y: the second list to OR

    Returns: The result of ORing the two lists.

    """
    result = 0
    for s, h in zip(x, y, strict=True):
        result = (result << 1) | (s | h)
    return result
