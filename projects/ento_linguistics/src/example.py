"""Example source file for testing coverage."""
from typing import List, Optional


def add_numbers(a: float, b: float) -> float:
    """Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    return a + b


def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Product of a and b
    """
    return a * b


def calculate_average(numbers: List[float]) -> Optional[float]:
    """Calculate the average of a list of numbers.
    
    Args:
        numbers: List of numbers to average
        
    Returns:
        Average of the numbers, or None if list is empty
    """
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def find_maximum(numbers: List[float]) -> Optional[float]:
    """Find the maximum value in a list of numbers.
    
    Args:
        numbers: List of numbers to search
        
    Returns:
        Maximum value, or None if list is empty
    """
    if not numbers:
        return None
    return max(numbers)


def find_minimum(numbers: List[float]) -> Optional[float]:
    """Find the minimum value in a list of numbers.
    
    Args:
        numbers: List of numbers to search
        
    Returns:
        Minimum value, or None if list is empty
    """
    if not numbers:
        return None
    return min(numbers)


def is_even(number: int) -> bool:
    """Check if a number is even.
    
    Args:
        number: Integer to check
        
    Returns:
        True if number is even, False otherwise
    """
    return number % 2 == 0


def is_odd(number: int) -> bool:
    """Check if a number is odd.
    
    Args:
        number: Integer to check
        
    Returns:
        True if number is odd, False otherwise
    """
    return not is_even(number)
