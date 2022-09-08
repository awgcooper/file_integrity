# file_integrity
Recurse through filesystem identifying:
- corrupt files
- new files
- deleted files
- moved files


Corrupt file identified via following methodology:
- comparing today's version vs yesterday's
- if name and last modification time are the same but the hash value is different, file is labelled as corrupt
- XXHASH3_128 is used for high speed and relatively low chance of collision for a non-cryptographic hash
