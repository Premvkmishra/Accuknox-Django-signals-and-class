"""
Rectangle class with iteration protocol implementation.

This module implements a Rectangle class that is iterable according to
the Python iterator protocol, yielding dictionaries containing length and width.
"""
from typing import Dict, Iterator, Union


class Rectangle:
    """A rectangle class that implements the iteration protocol.

    This class represents a rectangle with length and width dimensions.
    It implements the iterator protocol to yield its dimensions as dictionaries.

    Attributes:
        length: The length of the rectangle (must be positive)
        width: The width of the rectangle (must be positive)

    Example:
        >>> r = Rectangle(10, 5)
        >>> for dimension in r:
        ...     print(dimension)
        {"length": 10}
        {"width": 5}
    """

    def __init__(self, length: int, width: int) -> None:
        """Initialize a Rectangle instance.

        Args:
            length: The length of the rectangle (must be positive integer)
            width: The width of the rectangle (must be positive integer)

        Raises:
            ValueError: If length or width is not positive
            TypeError: If length or width is not an integer
        """
        if not isinstance(length, int) or not isinstance(width, int):
            raise TypeError("Length and width must be integers")

        if length <= 0 or width <= 0:
            raise ValueError("Length and width must be positive integers")

        self._length = length
        self._width = width
        self._iteration_index = 0

    @property
    def length(self) -> int:
        """Get the length of the rectangle.

        Returns:
            The length of the rectangle.
        """
        return self._length

    @property
    def width(self) -> int:
        """Get the width of the rectangle.

        Returns:
            The width of the rectangle.
        """
        return self._width

    def __iter__(self) -> Iterator[Dict[str, int]]:
        """Return the iterator object.

        This method is called when an iterator is required for the container.
        It resets the iteration index and returns self.

        Returns:
            The iterator object (self).
        """
        self._iteration_index = 0
        return self

    def __next__(self) -> Dict[str, int]:
        """Return the next item in the iteration.

        This method is called to get the next item in the iteration.
        It yields dictionaries containing length and width in sequence.

        Returns:
            A dictionary with either 'length' or 'width' key.

        Raises:
            StopIteration: When all dimensions have been yielded.
        """
        if self._iteration_index == 0:
            self._iteration_index += 1
            return {"length": self._length}
        elif self._iteration_index == 1:
            self._iteration_index += 1
            return {"width": self._width}
        else:
            raise StopIteration

    def area(self) -> int:
        """Calculate the area of the rectangle.

        Returns:
            The area of the rectangle (length * width).
        """
        return self._length * self._width

    def perimeter(self) -> int:
        """Calculate the perimeter of the rectangle.

        Returns:
            The perimeter of the rectangle (2 * (length + width)).
        """
        return 2 * (self._length + self._width)

    def __repr__(self) -> str:
        """Return the string representation of the Rectangle.

        Returns:
            A string representation of the Rectangle.
        """
        return f"Rectangle(length={self._length}, width={self._width})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another Rectangle.

        Args:
            other: The object to compare with.

        Returns:
            True if the other object is a Rectangle with the same dimensions.
        """
        if not isinstance(other, Rectangle):
            return False
        return self._length == other._length and self._width == other._width

    def __hash__(self) -> int:
        """Return the hash of the Rectangle.

        Returns:
            The hash value based on length and width.
        """
        return hash((self._length, self._width))
