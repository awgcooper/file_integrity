# file_integrity
For a single disk non-zfs/-btrfs filesystem, scan all directories to identify:
- corrupt files, new files, deleted files, moved files
<br/>

Corrupt files identified as follows:
- compare current version vs yesterday
- if name and last modification time are the same but the hash value is different, file is labelled as corrupt
- XXHASH3_128 is used for high speed and low chance of collision for a non-cryptographic hash
