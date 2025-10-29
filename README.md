# 7ZipFuzzer
Fazer for 7Zip (.zip format)

## More info
### About .zip
The format .the zip file: the first part of the file contains files with data in any order, the second part (the so-called central directory) is a list of all files with information about each, the end of the central directory contains the signature and information about the directory location.

The local file header (in Part 1) for each file contains:
 The signature 0x04034b50, indicating the beginning of the file, is 4 bytes.;
- The zip version – 2 bytes; 
- Flags – 2 bytes;
- Compression method – 2 bytes;
- Date/time of modification – 2+2 bytes;
- CRC-32 – 4 bytes;
- The file size before/after compression – 4+4 bytes;
- The file name – 2 bytes;
- The length of the additional field (for format extensions) – 2 bytes;
- File name – the length specified above;
- An additional field is of the length specified above.

The central header of the file contains:
- The signature 0x02014b50, indicating the beginning of a directory entry – 4 bytes;
- Fields from the local file header;
- File comment – 2 bytes;
- Disk number (for multi-volume archives) – 2 bytes;
- The offset of the local header (the location of the file in the archive) is – 4 bytes.

The end of the central directory contains:
- The signature 0x06054b50, indicating the end of the archive – 4 bytes;
- Disk numbers: current, with the beginning of the central catalog (for multi–volume archives) - 2+2 bytes;
- The number of files (in the central directory on this disk and in the general central directory) – 2+2 bytes;
- The size of the central directory – 4 bytes;
- Directory mixing (location of the central directory in the archive) – 4 bytes;
- The length of the archive comment – 2 bytes;
- Archive comment.

### About 7ZipFuzzer
The fuzzer uses a .zip file as a starting point, which is subjected to mutations. The mutations are randomly selected and consist of the following:
1. Corruption of 30 bytes after the local header signature (flags, headers, etc.);
2. Corruption of 46 bytes after the central directory signature (central directory entries);
3. Changing the value of the compression method byte;
4. Changing the value of the CRC-32;
5. Changing the value of the file size fields;
6. Insertion of random headers;
7. Mutation of random bits (inversion);
8. Mutation of random bytes (boundary values);
9. Replacement of a sequence of bytes with a single value;
10. Mutation by adding/subtracting/multiplying random bytes by a random value.

To use fuzzer enter command (-h for check available flags):

```
python fuzzer_zip.py base.zip
```
