from typing import Generator
import time
# fmt: off

K = [
    0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee,
    0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501,
    0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be,
    0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821,
    0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa,
    0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
    0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed,
    0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
    0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c,
    0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70,
    0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05,
    0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
    0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039,
    0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
    0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1,
    0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391
]

S = [
    7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,
    5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,
    4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,
    6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21
]

# fmt: on
def leftrotate(data: int, ammount_bits: int) -> int:
    rotation = ammount_bits % 32
    return (data << rotation | data >> (32 - rotation)) & 0xFFFFFFFF


def chunks(data: memoryview[bytes]) -> Generator[memoryview[bytes], None, None]:
    WIDTH = 64
    for i in range(0, len(data), WIDTH):
        yield data[i : i + WIDTH]


def _md5_hash_impl(DATA: str) -> bytes:
    A0 = 0x67452301
    B0 = 0xEFCDAB89
    C0 = 0x98BADCFE
    D0 = 0x10325476
    data_bytes = DATA.encode()

    original_length_bits = len(data_bytes) * 8

    data_bytes += b"\x80"

    MOD = len(data_bytes) % (512 // 8)

    if MOD < 448 // 8:
        data_bytes += (448 // 8 - MOD) * b"\x00"
    elif MOD > 448 // 8:
        data_bytes += (448 // 8 + 512 // 8 - MOD) * b"\x00"

    data_bytes += (original_length_bits & 0xFFFFFFFFFFFFFFFF).to_bytes(
        8, byteorder="little"
    )

    for chunk in chunks(memoryview(data_bytes)):
        M = [chunk[i : i + 4] for i in range(0, 512 // 8, 4)]
        A = A0
        B = B0
        C = C0
        D = D0

        for i in range(64):
            if 0 <= i <= 15:
                F = (B & C) | (~B & D)
                g = i
            elif 16 <= i <= 31:
                F = (D & B) | (~D & C)
                g = (5 * i + 1) % 16
            elif 32 <= i <= 47:
                F = B ^ C ^ D
                g = (3 * i + 5) % 16
            elif 48 <= i <= 63:
                F = C ^ (B | ~D)
                g = (7 * i) % 16

            F = (F + A + K[i] + int.from_bytes(M[g], "little")) & 0xFFFFFFFF
            A = D
            D = C
            C = B
            B = (B + leftrotate(F, S[i])) & 0xFFFFFFFF

        A0 += A
        B0 += B
        C0 += C
        D0 += D
        A0 %= 1 << 32
        B0 %= 1 << 32
        C0 %= 1 << 32
        D0 %= 1 << 32

    b = (
        A0.to_bytes(4, "little")
        + B0.to_bytes(4, "little")
        + C0.to_bytes(4, "little")
        + D0.to_bytes(4, "little")
    )
    return b


def md5(string: str) -> bytes:
    return _md5_hash_impl(string)


data: list[tuple[int, float]] = []


for i in range(8):
    LENGTH = 10**i
    MY_STRING = "a" * LENGTH
    initial = time.monotonic()
    md5(MY_STRING).hex()
    after = time.monotonic()
    data.append((LENGTH, after - initial))

with open("file", "a") as f:
    f.write(str(data))
