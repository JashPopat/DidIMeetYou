import os
import hashlib
from config import EPHID_SIZE

def generate_ephid():
    return os.urandom(EPHID_SIZE)

def get_ephid_hash(ephid):
    """
    Used for Task 4 verification: Generate a hash of the EphID
    to be sent along with shares.
    """
    return hashlib.sha256(ephid).hexdigest()

