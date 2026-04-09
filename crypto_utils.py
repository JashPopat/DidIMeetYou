import os
import hashlib
from config import EPHID_SIZE, PRIME, DH_GENERATOR
from secret_sharing import split_id, reconstruct_id

def generate_ephid():
    return os.urandom(EPHID_SIZE)

def get_ephid_hash(ephid):
    return hashlib.sha256(ephid).hexdigest()

def get_shares_for_broadcast(ephid, k, n):
    shares = split_id(ephid, k, n)
    ephid_hash = hashlib.sha256(ephid).hexdigest()[:16]
    return shares, ephid_hash

def compute_encid(our_ephid, their_ephid):
    our_int = int.from_bytes(our_ephid, 'big')
    their_int = int.from_bytes(their_ephid, 'big')

    our_private = our_int % (PRIME - 2)
    their_private = their_int % (PRIME - 2)

    our_public   = pow(DH_GENERATOR, our_private, PRIME)
    their_public = pow(DH_GENERATOR, their_private, PRIME)
    shared_secret = pow(their_public, our_private, PRIME)

    encID = hashlib.sha256(shared_secret.to_bytes((shared_secret.bit_length() + 7) // 8, byteorder='big')).digest()

    print("\n[Task 5] Diffie-Hellman complete.")
    print(f"[Task 5]   Our EphID  : {our_ephid.hex()[:10]}...")
    print(f"[Task 5]   Their EphID: {their_ephid.hex()[:10]}...")
    print(f"[Task 5] EncID        : {encID.hex()[:10]}...")

    return encID