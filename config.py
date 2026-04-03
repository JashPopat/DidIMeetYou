#DBF, QBF and CBF are all of size 100KB and use 3 hashes
BLOOM_SIZE_BYTES = 100 * 1024   # 100KB
BLOOM_NUM_HASHES = 3

#backend server using TCP port No 55000
SERVER_PORT = 55000

#32-Byte EphID
EPHID_SIZE = 32

#broadcast these n shares @ 1 unique share per 3 seconds
SHARE_BROADCAST_INTERVAL = 3   # seconds

#each node stores at most 6 DBFs
MAX_DBFS = 6

# We need a large Prime for the finite field (Mersenne prime)
PRIME = 2**521 - 1 