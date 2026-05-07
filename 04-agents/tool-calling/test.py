"""
Test module for the calculate_pi function from edit.py
"""

from edit import calculate_pi


def test_calculate_pi():
    """Test the calculate_pi function"""
    
    # Calculate PI to the 5th digit
    pi_value = calculate_pi(digits=5)
    
    print("=" * 50)
    print("Testing calculate_pi() function")
    print("=" * 50)
    print(f"\nPI calculated to 5 digits: {pi_value}")
    print(f"Expected value:            3.14159")
    print(f"Match: {pi_value == 3.14159}")
    
    # Test with different precisions
    print("\n" + "-" * 50)
    print("Testing with different decimal places:")
    print("-" * 50)
    
    for digits in range(1, 11):
        pi_val = calculate_pi(digits=digits)
        print(f"Digits: {digits:2d} | PI = {pi_val}")
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    test_calculate_pi()
