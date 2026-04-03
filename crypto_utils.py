import os
import hashlib
from config import EPHID_SIZE
import hashlib
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