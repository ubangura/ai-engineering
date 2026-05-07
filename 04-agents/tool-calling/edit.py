def greeting():
    print("Hello")


def calculate_pi(digits=5):
    """
    Calculate PI to the specified number of decimal digits.
    Uses Machin's formula: PI/4 = 4*arctan(1/5) - arctan(1/239)
    """
    from decimal import Decimal, getcontext
    
    # Set precision higher than needed to avoid rounding errors
    getcontext().prec = digits + 10
    
    # Calculate arctan using Taylor series
    def arctan(x, num_terms=500):
        """Calculate arctan(x) using Taylor series"""
        x = Decimal(x)
        power = x
        result = power
        for n in range(1, num_terms):
            power *= -x * x
            result += power / (2 * n + 1)
        return result
    
    # Machin's formula: PI/4 = 4*arctan(1/5) - arctan(1/239)
    pi = 4 * (4 * arctan(Decimal(1) / Decimal(5)) - arctan(Decimal(1) / Decimal(239)))
    
    # Return PI rounded to the specified number of digits
    return float(round(pi, digits))
