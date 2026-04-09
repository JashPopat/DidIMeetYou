import random
from config import EPHID_SIZE, PRIME

# Task 2: Create n shares from the EphID

def split_id(ephid_bytes, k, n):
    secret = int.from_bytes(ephid_bytes, 'big')
    coefficients = [secret] + [random.SystemRandom().randrange(PRIME) for _ in range(k - 1)]
    
    shares = []
    for x in range(1, n + 1):
        y = 0
        for power, coeff in enumerate(coefficients):
            y = (y + coeff * (x**power)) % PRIME
        shares.append((x, y))
    return shares

def reconstruct_id(shares):
    def lagrange(x, x_s, y_s):
        total = 0
        n = len(x_s)
        for i in range(n):
            numerator, denominator = 1, 1
            for j in range(n):
                if i == j: continue
                numerator = (numerator * (x - x_s[j])) % PRIME
                denominator = (denominator * (x_s[i] - x_s[j])) % PRIME
            lagrange_polynomial = (y_s[i] * numerator * pow(denominator, -1, PRIME)) % PRIME
            total = (total + lagrange_polynomial) % PRIME
        return total

    x_s, y_s = zip(*shares)
    secret_int = lagrange(0, x_s, y_s)
    return secret_int.to_bytes(EPHID_SIZE, 'big')
