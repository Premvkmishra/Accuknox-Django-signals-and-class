"""
Tests for the Rectangle class.

This module contains comprehensive tests for the Rectangle class,
including iteration protocol, edge cases, and mathematical operations.
"""
import logging
from typing import Any

import pytest
from django.test import TestCase

from core.rectangle import Rectangle

logger = logging.getLogger(__name__)


class RectangleTests(TestCase):
    """Test suite for the Rectangle class."""

    def test_rectangle_initialization(self) -> None:
        """Test Rectangle initialization with valid parameters."""
        rectangle = Rectangle(10, 5)

        self.assertEqual(rectangle.length, 10)
        self.assertEqual(rectangle.width, 5)
        logger.info(
            "Rectangle initialization test passed",
            extra={"test": "test_rectangle_initialization"},
        )

    def test_rectangle_initialization_with_negative_values(self) -> None:
        """Test Rectangle initialization rejects negative values."""
        with self.assertRaises(ValueError):
            Rectangle(-10, 5)

        with self.assertRaises(ValueError):
            Rectangle(10, -5)

        with self.assertRaises(ValueError):
            Rectangle(-10, -5)

        logger.info(
            "Rectangle negative values test passed",
            extra={"test": "test_rectangle_initialization_with_negative_values"},
        )

    def test_rectangle_initialization_with_zero(self) -> None:
        """Test Rectangle initialization rejects zero values."""
        with self.assertRaises(ValueError):
            Rectangle(0, 5)

        with self.assertRaises(ValueError):
            Rectangle(10, 0)

        with self.assertRaises(ValueError):
            Rectangle(0, 0)

        logger.info(
            "Rectangle zero values test passed",
            extra={"test": "test_rectangle_initialization_with_zero"},
        )

    def test_rectangle_initialization_with_non_integer(self) -> None:
        """Test Rectangle initialization rejects non-integer values."""
        with self.assertRaises(TypeError):
            Rectangle(10.5, 5)  # type: ignore

        with self.assertRaises(TypeError):
            Rectangle(10, 5.5)  # type: ignore

        with self.assertRaises(TypeError):
            Rectangle("10", 5)  # type: ignore

        logger.info(
            "Rectangle non-integer values test passed",
            extra={"test": "test_rectangle_initialization_with_non_integer"},
        )

    def test_rectangle_iteration(self) -> None:
        """Test Rectangle iteration yields correct dictionaries."""
        rectangle = Rectangle(10, 5)
        result = list(rectangle)

        expected = [{"length": 10}, {"width": 5}]

        self.assertEqual(result, expected)
        logger.info(
            "Rectangle iteration test passed",
            extra={"test": "test_rectangle_iteration", "result": result},
        )

    def test_rectangle_iteration_multiple_times(self) -> None:
        """Test that Rectangle can be iterated multiple times."""
        rectangle = Rectangle(10, 5)

        first_iteration = list(rectangle)
        second_iteration = list(rectangle)
        third_iteration = list(rectangle)

        expected = [{"length": 10}, {"width": 5}]

        self.assertEqual(first_iteration, expected)
        self.assertEqual(second_iteration, expected)
        self.assertEqual(third_iteration, expected)

        logger.info(
            "Rectangle multiple iteration test passed",
            extra={"test": "test_rectangle_iteration_multiple_times"},
        )

    def test_rectangle_iteration_order(self) -> None:
        """Test that Rectangle iteration yields length before width."""
        rectangle = Rectangle(10, 5)
        result = list(rectangle)

        self.assertEqual(result[0], {"length": 10})
        self.assertEqual(result[1], {"width": 5})

        logger.info(
            "Rectangle iteration order test passed",
            extra={"test": "test_rectangle_iteration_order"},
        )

    def test_rectangle_for_loop(self) -> None:
        """Test Rectangle iteration using for loop."""
        rectangle = Rectangle(10, 5)
        items = []

        for item in rectangle:
            items.append(item)

        expected = [{"length": 10}, {"width": 5}]
        self.assertEqual(items, expected)

        logger.info(
            "Rectangle for loop test passed",
            extra={"test": "test_rectangle_for_loop"},
        )

    def test_rectangle_area(self) -> None:
        """Test Rectangle area calculation."""
        rectangle = Rectangle(10, 5)
        area = rectangle.area()

        self.assertEqual(area, 50)
        logger.info(
            "Rectangle area test passed",
            extra={"test": "test_rectangle_area", "area": area},
        )

    def test_rectangle_perimeter(self) -> None:
        """Test Rectangle perimeter calculation."""
        rectangle = Rectangle(10, 5)
        perimeter = rectangle.perimeter()

        self.assertEqual(perimeter, 30)
        logger.info(
            "Rectangle perimeter test passed",
            extra={"test": "test_rectangle_perimeter", "perimeter": perimeter},
        )

    def test_rectangle_repr(self) -> None:
        """Test Rectangle string representation."""
        rectangle = Rectangle(10, 5)
        repr_str = repr(rectangle)

        self.assertEqual(repr_str, "Rectangle(length=10, width=5)")
        logger.info(
            "Rectangle repr test passed",
            extra={"test": "test_rectangle_repr", "repr": repr_str},
        )

    def test_rectangle_equality(self) -> None:
        """Test Rectangle equality comparison."""
        rectangle1 = Rectangle(10, 5)
        rectangle2 = Rectangle(10, 5)
        rectangle3 = Rectangle(5, 10)

        self.assertEqual(rectangle1, rectangle2)
        self.assertNotEqual(rectangle1, rectangle3)

        logger.info(
            "Rectangle equality test passed",
            extra={"test": "test_rectangle_equality"},
        )

    def test_rectangle_hash(self) -> None:
        """Test Rectangle hashing for use in sets and dicts."""
        rectangle1 = Rectangle(10, 5)
        rectangle2 = Rectangle(10, 5)
        rectangle3 = Rectangle(5, 10)

        # Equal rectangles should have equal hashes
        self.assertEqual(hash(rectangle1), hash(rectangle2))
        self.assertNotEqual(hash(rectangle1), hash(rectangle3))

        # Should be usable in sets
        rectangle_set = {rectangle1, rectangle2, rectangle3}
        self.assertEqual(len(rectangle_set), 2)  # rectangle1 and rectangle2 are equal

        logger.info(
            "Rectangle hash test passed",
            extra={"test": "test_rectangle_hash"},
        )

    def test_rectangle_immutability_of_dimensions(self) -> None:
        """Test that rectangle dimensions are immutable."""
        rectangle = Rectangle(10, 5)

        # Try to modify length (should not work as it's a property)
        with self.assertRaises(AttributeError):
            rectangle.length = 20  # type: ignore

        # Try to modify width (should not work as it's a property)
        with self.assertRaises(AttributeError):
            rectangle.width = 10  # type: ignore

        logger.info(
            "Rectangle immutability test passed",
            extra={"test": "test_rectangle_immutability_of_dimensions"},
        )

    def test_rectangle_with_large_values(self) -> None:
        """Test Rectangle with large integer values."""
        rectangle = Rectangle(1000000, 500000)
        result = list(rectangle)

        expected = [{"length": 1000000}, {"width": 500000}]
        self.assertEqual(result, expected)

        logger.info(
            "Rectangle large values test passed",
            extra={"test": "test_rectangle_with_large_values"},
        )

    def test_rectangle_square(self) -> None:
        """Test Rectangle with equal length and width (square)."""
        rectangle = Rectangle(5, 5)
        result = list(rectangle)

        expected = [{"length": 5}, {"width": 5}]
        self.assertEqual(result, expected)

        self.assertEqual(rectangle.area(), 25)
        self.assertEqual(rectangle.perimeter(), 20)

        logger.info(
            "Rectangle square test passed",
            extra={"test": "test_rectangle_square"},
        )

    def test_rectangle_iteration_protocol_compliance(self) -> None:
        """Test that Rectangle properly implements the iterator protocol."""
        rectangle = Rectangle(10, 5)

        # Test __iter__ returns self
        iterator = iter(rectangle)
        self.assertIs(iterator, rectangle)

        # Test __next__ returns correct values
        self.assertEqual(next(iterator), {"length": 10})
        self.assertEqual(next(iterator), {"width": 5})

        # Test StopIteration is raised
        with self.assertRaises(StopIteration):
            next(iterator)

        logger.info(
            "Rectangle iteration protocol compliance test passed",
            extra={"test": "test_rectangle_iteration_protocol_compliance"},
        )

    def test_rectangle_iterator_reset(self) -> None:
        """Test that iterator is reset when starting new iteration."""
        rectangle = Rectangle(10, 5)

        # First iteration
        first_result = list(rectangle)

        # Second iteration should start fresh
        second_result = list(rectangle)

        self.assertEqual(first_result, second_result)

        logger.info(
            "Rectangle iterator reset test passed",
            extra={"test": "test_rectangle_iterator_reset"},
        )


@pytest.mark.django_db
class RectanglePytestTests:
    """Pytest-based tests for Rectangle class."""

    def test_rectangle_basic_pytest(self) -> None:
        """Test basic Rectangle functionality with pytest."""
        rectangle = Rectangle(10, 5)
        result = list(rectangle)

        assert result == [{"length": 10}, {"width": 5}]
        assert rectangle.area() == 50
        assert rectangle.perimeter() == 30

        logger.info(
            "Rectangle basic pytest test passed",
            extra={"test": "test_rectangle_basic_pytest"},
        )

    def test_rectangle_edge_cases_pytest(self) -> None:
        """Test Rectangle edge cases with pytest."""
        # Minimum valid values
        rectangle = Rectangle(1, 1)
        assert list(rectangle) == [{"length": 1}, {"width": 1}]

        # Large values
        rectangle = Rectangle(999999, 888888)
        assert list(rectangle) == [{"length": 999999}, {"width": 888888}]

        logger.info(
            "Rectangle edge cases pytest test passed",
            extra={"test": "test_rectangle_edge_cases_pytest"},
        )

    @pytest.mark.parametrize(
        "length,width,expected_area,expected_perimeter",
        [
            (10, 5, 50, 30),
            (1, 1, 1, 4),
            (100, 50, 5000, 300),
            (7, 3, 21, 20),
        ],
    )
    def test_rectangle_calculations_parametrized(
        self, length: int, width: int, expected_area: int, expected_perimeter: int
    ) -> None:
        """Test Rectangle calculations with various dimensions."""
        rectangle = Rectangle(length, width)

        assert rectangle.area() == expected_area
        assert rectangle.perimeter() == expected_perimeter

        logger.info(
            "Rectangle parametrized test passed",
            extra={
                "test": "test_rectangle_calculations_parametrized",
                "length": length,
                "width": width,
            },
        )
