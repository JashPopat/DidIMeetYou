import os
import hashlib
from config import EPHID_SIZE, PRIME, DH_GENERATOR
from secret_sharing import split_id, reconstruct_id

def generate_ephid():
    return os.urandom(EPHID_SIZE)

def get_ephid_hash(ephid):
    """
    Used for Task 4 verification: Generate a hash of the EphID
    to be sent along with shares.
    """
    return hashlib.sha256(ephid).hexdigest()

def get_shares_for_broadcast(ephid, k, n):
    # Get the shares (x, y)
    shares = split_id(ephid, k, n)
    
    # Generate a hash of the original EphID (Task 4 requires this for verification)
    ephid_hash = hashlib.sha256(ephid).hexdigest()[:16] # Use a prefix to save space
    
    # Return formatted shares ready for UDP
    return shares, ephid_hash
def compute_encid(our_ephid, their_ephid):
    # Convert both EphIDs to integers
    our_int   = int.from_bytes(our_ephid,   'big')
    their_int = int.from_bytes(their_ephid, 'big')

    # Use modulo (PRIME - 2) to keep in valid DH range
    our_private   = our_int   % (PRIME - 2)
    their_private = their_int % (PRIME - 2)

    # Compute DH public keys: g^private mod p
    our_public   = pow(DH_GENERATOR, our_private,   PRIME)
    their_public = pow(DH_GENERATOR, their_private, PRIME)

    # Shared secret: their_public ^ our_private mod p
    # Node A: (g^b)^a mod p
    # Node B: (g^a)^b mod p
    # Both equal g^(ab) mod p — same value
    shared_secret = pow(their_public, our_private, PRIME)

    # Hash to get fixed 32-byte EncID
    encID = hashlib.sha256(
        shared_secret.to_bytes(
            (shared_secret.bit_length() + 7) // 8,
            byteorder='big'
        )
    ).digest()

    print("\n[Task 5] Diffie-Hellman complete.")
    print(f"[Task 5]   Our EphID  : {our_ephid.hex()[:10]}...")
    print(f"[Task 5]   Their EphID: {their_ephid.hex()[:10]}...")
    print(f"[Task 5] EncID        : {encID.hex()[:10]}...")

    return encID