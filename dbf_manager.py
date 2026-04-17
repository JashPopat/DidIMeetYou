import hashlib
import time
import threading
from config import BLOOM_SIZE_BYTES, BLOOM_NUM_HASHES, MAX_DBFS

# Bloom filter helpers

def get_bit_positions(data, bloom_size_bits):
    positions = []
    for i in range(BLOOM_NUM_HASHES):
        seed = i.to_bytes(4, 'big')
        h = hashlib.sha256(seed + data).hexdigest()
        position = int(h[:8], 16) % bloom_size_bits
        positions.append(position)
    return positions

def set_bit(bloom_bytearray, bit_position):
    byte_index = bit_position // 8
    bit_offset = bit_position % 8
    bloom_bytearray[byte_index] |= (1 << bit_offset)

def check_bit(bloom_bytearray, bit_position):
    byte_index = bit_position // 8
    bit_offset = bit_position % 8
    return bool(bloom_bytearray[byte_index] & (1 << bit_offset))

def bloom_insert(bloom_bytearray, data_bytes):
    bloom_size_bits = len(bloom_bytearray) * 8
    positions = get_bit_positions(data_bytes, bloom_size_bits)
    for pos in positions:
        set_bit(bloom_bytearray, pos)
    return positions  # for debug and help

def bloom_check(bloom_bytearray, data_bytes):
    bloom_size_bits = len(bloom_bytearray) * 8
    positions = get_bit_positions(data_bytes, bloom_size_bits)
    return all(check_bit(bloom_bytearray, pos) for pos in positions)

def bloom_merge(list_of_bloom_bytearrays):
    merged = bytearray(BLOOM_SIZE_BYTES)
    for bf in list_of_bloom_bytearrays:
        for i in range(BLOOM_SIZE_BYTES):
            merged[i] |= bf[i]
    return merged

def count_set_bits(bloom_bytearray):
    return sum(bin(byte).count('1') for byte in bloom_bytearray)

dbf_list = []
dbf_lock = threading.Lock()
current_dbf = None

def new_dbf():
    return {
        'filter' : bytearray(BLOOM_SIZE_BYTES),
        'created_at' : time.time(),
        'encid_count' : 0
    }

def initialise_dbf():
    global current_dbf
    with dbf_lock:
        current_dbf = new_dbf()
        dbf_list.append(current_dbf)
    print(f"[Task 6] DBF initialised. "
          f"Size: {BLOOM_SIZE_BYTES} bytes, Hashes: {BLOOM_NUM_HASHES}")

# Task 6 - Insert EncID into DBF then delete

def add_encid(encid_bytes):
    with dbf_lock:
        if current_dbf is None:
            print("[Task 6] ERROR — no active DBF")
            return

        positions = bloom_insert(current_dbf['filter'], encid_bytes)
        current_dbf['encid_count'] += 1

        print(f"\n[Task 6] EncID inserted into DBF.")
        print(f"[Task 6] Bit positions set : {positions}")
        print(f"[Task 6] EncIDs in this DBF : {current_dbf['encid_count']}")
        print(f"[Task 6] Bits set in DBF : {count_set_bits(current_dbf['filter'])}")

        encid_bytes = None
        print(f"[Task 6] EncID deleted from memory.")

# Task 7 — DBF Rotation

def start_dbf_rotation(t):
    # Called once from Dimy.py on startup.
    dbf_window  = t * 6
    dt_seconds  = t * 6 * 6
    dt_minutes  = dt_seconds / 60

    print(f"[Task 7] DBF rotation started.")
    print(f"[Task 7] New DBF every : {dbf_window} seconds")
    print(f"[Task 7] Max DBFs stored : {MAX_DBFS}")
    print(f"[Task 7] DBF max age : {dt_minutes:.1f} minutes ({dt_seconds}s)")

    def rotation_loop():
        while True:
            time.sleep(dbf_window)
            _rotate_dbf(dt_seconds)

    threading.Thread(target=rotation_loop, daemon=True).start()


def _rotate_dbf(dt_seconds):

    global current_dbf

    with dbf_lock:
        now = time.time()

        before_count = len(dbf_list)
        expired = [dbf for dbf in dbf_list if (now - dbf['created_at']) > dt_seconds]
        for dbf in expired:
            dbf_list.remove(dbf)
        expired_count = before_count - len(dbf_list)

        if expired_count > 0:
            print(f"\n[Task 7] Deleted {expired_count} expired DBF(s).")

        while len(dbf_list) >= MAX_DBFS:
            removed = dbf_list.pop(0)
            print(f"[Task 7] Max DBF cap reached — removed oldest DBF "
                  f"(had {removed['encid_count']} EncIDs).")

        current_dbf = new_dbf()
        dbf_list.append(current_dbf)

        print(f"\n[Task 7] New DBF created. Total DBFs stored: {len(dbf_list)}")
        print(f"[Task 7]   DBF ages: "
              f"{[round(now - d['created_at'], 1) for d in dbf_list]} seconds old")
        print(f"[Task 7]   EncIDs per DBF: "
              f"{[d['encid_count'] for d in dbf_list]}")

def get_all_dbfs():
    with dbf_lock:
        return [bytes(dbf['filter']) for dbf in dbf_list]

def get_dbf_count():
    with dbf_lock:
        return len(dbf_list)
    
# Task 8 — Build QBF from DBFs

def build_qbf():
    with dbf_lock:
        if not dbf_list:
            print("[Task 8] No DBFs available to build QBF.")
            return None

        all_filters = [dbf['filter'] for dbf in dbf_list]
        qbf = bloom_merge(all_filters)

        total_encids = sum(d['encid_count'] for d in dbf_list)
        print(f"\n[Task 8] QBF built from {len(dbf_list)} DBF(s).")
        print(f"[Task 8] Total EncIDs across all DBFs: {total_encids}")
        print(f"[Task 8] Bits set in QBF: {count_set_bits(qbf)}")

        return bytes(qbf)

# Task 9: Combine all DBFs into CBF

def build_cbf():
    with dbf_lock:
        if not dbf_list:
            return None
        all_filters = [dbf['filter'] for dbf in dbf_list]
        cbf = bloom_merge(all_filters)
        print(f"[Task 9] CBF prepared from {len(dbf_list)} DBFs.")
        return bytes(cbf)