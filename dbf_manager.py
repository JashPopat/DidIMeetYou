import hashlib
import time
import threading
from config import BLOOM_SIZE_BYTES, BLOOM_NUM_HASHES, MAX_DBFS

# ============================================================
# BLOOM FILTER HELPERS
# ============================================================

def _get_bit_positions(data, bloom_size_bits):
    """
    Given bytes input, returns BLOOM_NUM_HASHES bit positions
    by seeding each hash with a different prefix integer.
    """
    positions = []
    for i in range(BLOOM_NUM_HASHES):
        # Use a different seed for each of the 3 hash functions
        seed = i.to_bytes(4, 'big')
        h = hashlib.sha256(seed + data).hexdigest()
        # Convert first 8 hex chars to int, mod by total bits
        position = int(h[:8], 16) % bloom_size_bits
        positions.append(position)
    return positions

def _set_bit(bloom_bytearray, bit_position):
    """Flip a single bit to 1 in the bloom filter bytearray."""
    byte_index = bit_position // 8
    bit_offset = bit_position % 8
    bloom_bytearray[byte_index] |= (1 << bit_offset)

def _check_bit(bloom_bytearray, bit_position):
    """Check if a single bit is set in the bloom filter."""
    byte_index = bit_position // 8
    bit_offset = bit_position % 8
    return bool(bloom_bytearray[byte_index] & (1 << bit_offset))

def bloom_insert(bloom_bytearray, data_bytes):
    """Insert data_bytes into the bloom filter by setting 3 bits."""
    bloom_size_bits = len(bloom_bytearray) * 8
    positions = _get_bit_positions(data_bytes, bloom_size_bits)
    for pos in positions:
        _set_bit(bloom_bytearray, pos)
    return positions  # return for debug printing

def bloom_check(bloom_bytearray, data_bytes):
    """Check if data_bytes is probably in the bloom filter."""
    bloom_size_bits = len(bloom_bytearray) * 8
    positions = _get_bit_positions(data_bytes, bloom_size_bits)
    return all(_check_bit(bloom_bytearray, pos) for pos in positions)

def bloom_merge(list_of_bloom_bytearrays):
    """OR multiple bloom filters together into one."""
    merged = bytearray(BLOOM_SIZE_BYTES)
    for bf in list_of_bloom_bytearrays:
        for i in range(BLOOM_SIZE_BYTES):
            merged[i] |= bf[i]
    return merged

def count_set_bits(bloom_bytearray):
    """Count how many bits are set to 1 — used for debug display."""
    return sum(bin(byte).count('1') for byte in bloom_bytearray)

# ============================================================
# DBF STATE
# Each DBF is a dict with:
#   'filter'     : bytearray of BLOOM_SIZE_BYTES
#   'created_at' : timestamp when this DBF was started
#   'encid_count': how many EncIDs have been inserted
# ============================================================

dbf_list = []           # list of DBF dicts, oldest first
dbf_lock = threading.Lock()
current_dbf = None      # the active DBF being written to

def _new_dbf():
    """Create a fresh empty DBF."""
    return {
        'filter'     : bytearray(BLOOM_SIZE_BYTES),
        'created_at' : time.time(),
        'encid_count': 0
    }

def initialise_dbf():
    """
    Task 6: Create the first DBF on startup.
    Called once from Dimy.py before the encounter loop starts.
    """
    global current_dbf
    with dbf_lock:
        current_dbf = _new_dbf()
        dbf_list.append(current_dbf)
    print(f"[Task 6] DBF initialised. "
          f"Size: {BLOOM_SIZE_BYTES} bytes, Hashes: {BLOOM_NUM_HASHES}")

# ============================================================
# TASK 6 — INSERT EncID INTO CURRENT DBF
# ============================================================

def add_encid(encid_bytes):
    """
    Task 6: Insert EncID into the current DBF, then delete it.

    Parameters:
        encid_bytes : 32-byte EncID from Diffie-Hellman
    """
    with dbf_lock:
        if current_dbf is None:
            print("[Task 6] ERROR — no active DBF, call initialise_dbf() first.")
            return

        # Insert EncID into bloom filter
        positions = bloom_insert(current_dbf['filter'], encid_bytes)
        current_dbf['encid_count'] += 1

        print(f"\n[Task 6] EncID inserted into DBF.")
        print(f"[Task 6]   Bit positions set : {positions}")
        print(f"[Task 6]   EncIDs in this DBF: {current_dbf['encid_count']}")
        print(f"[Task 6]   Bits set in DBF   : {count_set_bits(current_dbf['filter'])}")

        # EncID deleted from memory — it only lives in the bloom filter now
        encid_bytes = None
        print(f"[Task 6]   EncID deleted from memory.")

# ============================================================
# TASK 7 — DBF ROTATION
# ============================================================

def start_dbf_rotation(t):
    """
    Task 7: Seal current DBF and start a new one every t*6 seconds.
    Keep at most MAX_DBFS (6) DBFs. Delete any older than Dt minutes.
    Dt = (t * 6 * 6) / 60 minutes

    Called once from Dimy.py on startup.
    """
    dbf_window  = t * 6          # seconds per DBF
    dt_seconds  = t * 6 * 6     # max age in seconds before deletion
    dt_minutes  = dt_seconds / 60

    print(f"[Task 7] DBF rotation started.")
    print(f"[Task 7]   New DBF every  : {dbf_window} seconds")
    print(f"[Task 7]   Max DBFs stored: {MAX_DBFS}")
    print(f"[Task 7]   DBF max age    : {dt_minutes:.1f} minutes ({dt_seconds}s)")

    def rotation_loop():
        while True:
            time.sleep(dbf_window)
            _rotate_dbf(dt_seconds)

    threading.Thread(target=rotation_loop, daemon=True).start()


def _rotate_dbf(dt_seconds):
    """
    Seal the current DBF, delete expired ones, start a fresh one.
    Called internally by the rotation loop.
    """
    global current_dbf

    with dbf_lock:
        now = time.time()

        # --- Delete DBFs older than Dt seconds ---
        before_count = len(dbf_list)
        expired = [dbf for dbf in dbf_list
                   if (now - dbf['created_at']) > dt_seconds]
        for dbf in expired:
            dbf_list.remove(dbf)
        expired_count = before_count - len(dbf_list)

        if expired_count > 0:
            print(f"\n[Task 7] Deleted {expired_count} expired DBF(s).")

        # --- Enforce MAX_DBFS cap ---
        # If still over the limit after expiry, remove oldest first
        while len(dbf_list) >= MAX_DBFS:
            removed = dbf_list.pop(0)
            print(f"[Task 7] Max DBF cap reached — removed oldest DBF "
                  f"(had {removed['encid_count']} EncIDs).")

        # --- Create and register new DBF ---
        current_dbf = _new_dbf()
        dbf_list.append(current_dbf)

        print(f"\n[Task 7] New DBF created. Total DBFs stored: {len(dbf_list)}")
        print(f"[Task 7]   DBF ages: "
              f"{[round(now - d['created_at'], 1) for d in dbf_list]} seconds old")
        print(f"[Task 7]   EncIDs per DBF: "
              f"{[d['encid_count'] for d in dbf_list]}")


def get_all_dbfs():
    """
    Returns a copy of all current DBF bytearrays.
    Used by Task 8 (QBF) and Task 9 (CBF).
    """
    with dbf_lock:
        return [bytes(dbf['filter']) for dbf in dbf_list]


def get_dbf_count():
    """Returns how many DBFs are currently stored."""
    with dbf_lock:
        return len(dbf_list)
    
# ============================================================
# TASK 8 — BUILD QBF FROM ALL DBFS
# ============================================================

def build_qbf():
    """
    Task 8: Merge all current DBFs into a single Query Bloom Filter.
    Called every Dt minutes by a background timer in Dimy.py.
    Returns the QBF as bytes.
    """
    with dbf_lock:
        if not dbf_list:
            print("[Task 8] No DBFs available to build QBF.")
            return None

        all_filters = [dbf['filter'] for dbf in dbf_list]
        qbf = bloom_merge(all_filters)

        total_encids = sum(d['encid_count'] for d in dbf_list)
        print(f"\n[Task 8] QBF built from {len(dbf_list)} DBF(s).")
        print(f"[Task 8]   Total EncIDs across all DBFs: {total_encids}")
        print(f"[Task 8]   Bits set in QBF: {count_set_bits(qbf)}")

        return bytes(qbf)

def build_cbf():
    """
    Task 9: Combine all DBFs into a Contact Bloom Filter (CBF).
    """
    with dbf_lock:
        if not dbf_list:
            return None
        # CBF is essentially a QBF uploaded by a positive user
        all_filters = [dbf['filter'] for dbf in dbf_list]
        cbf = bloom_merge(all_filters)
        print(f"[Task 9] CBF prepared from {len(dbf_list)} DBFs.")
        return bytes(cbf)