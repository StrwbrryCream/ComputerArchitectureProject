import math
MASK32 = 0xFFFFFFFF

# ------------------------------------------------------------
# 32-bit helpers
# ------------------------------------------------------------

def fmt_hex32(x):
    return f"0x{(x & 0xFFFFFFFF):08X}"

def u32(x):
    """
    Return x truncated to 32 bits (unsigned).
    Hint: mask with 0xFFFFFFFF
    """
    return (x & MASK32)


def s32(x):
    """
    TODO
    Convert a 32-bit unsigned value to signed two's complement.
    If bit 31 is 1, subtract 2^32.
    """
    x &= MASK32
    return x if x < 0x80000000 else x - 0x100000000


def sign_extend(value, bits):
    """
    Sign-extend 'value' which is 'bits' wide.

    Example:
    sign_extend(0b1111,4) -> -1
    """
    sign_bit = 1 << (bits-1)
    return (value & (sign_bit -1)) - (value & sign_bit)


def get_bits(x, hi, lo):
    """
    Extract bits from position hi down to lo (inclusive).

    Example:
    get_bits(0b101100,3,1) -> 0b110
    """
    mask = (1 << (hi-lo+1)) - 1
    return (x >> lo) & mask

# ------------------------------------------------------------
# Immediate Generators
# ------------------------------------------------------------

def imm_i(instr):
    """
    TODO
    I-type immediate = bits [31:20]
    Sign extend to 32 bits
    """
    return sign_extend(get_bits(instr, 31, 20), 32)


def imm_s(instr):
    """
    S-type immediate uses:
        bits [31:25] and [11:7]
    Combine then sign extend.
    """
    imm = ((get_bits(instr, 31, 25) << 5) | (get_bits(instr, 11, 7)))
    return sign_extend(imm, 32)


def imm_b(instr):
    """
    B-type immediate uses scattered bits:

        imm[12]   = instr[31]
        imm[11]   = instr[7]
        imm[10:5] = instr[30:25]
        imm[4:1]  = instr[11:8]
        imm[0]    = 0

    Then sign extend to 32 bits.
    """
    imm = ((get_bits(instr, 31, 31) << 12) | (get_bits(instr, 7, 7) << 11) | (get_bits(instr, 30, 25) << 5) | (get_bits(instr, 11, 8) << 1) | (0))
    return sign_extend(imm, 32)


def imm_u(instr):
    """
    TODO
    U-type immediate = bits [31:12] << 12
    """
    return (get_bits(instr,31,12) << 12)


def imm_j(instr):
    """
    TODO
    J-type immediate for JAL instruction.

        imm[20]   = instr[31]
        imm[10:1] = instr[30:21]
        imm[11]   = instr[20]
        imm[19:12]= instr[19:12]
        imm[0]    = 0

    Then sign extend.
    """
    imm = ((get_bits(instr, 31, 31) << 20) | (get_bits(instr, 19, 12) << 12) | (get_bits(instr, 20, 20) << 11) | (get_bits(instr, 30, 21) << 1) | (0)) 
    return sign_extend(imm, 32)

# ------------------------------------------------------------
# Instruction Decode
# ------------------------------------------------------------

def decode(instr):
    """
    Extract instruction fields and return dictionary with:

    opcode
    rd
    funct3
    rs1
    rs2
    funct7

    Also compute all immediates and store:

    imm_I
    imm_S
    imm_B
    imm_U
    imm_J
    """

    d = {}
    d["instr"] = instr
    d["opcode"] = get_bits(instr, 6, 0)
    d["rd"] = get_bits(instr, 11, 7)
    d["funct3"] = get_bits(instr, 14 ,12)
    d["rs1"] = get_bits(instr, 19, 15)
    d["rs2"] = get_bits(instr, 24, 20)
    d["funct7"] = get_bits(instr,31, 25)

    d["imm_I"] = imm_i(instr)
    d["imm_S"] = imm_s(instr)
    d["imm_B"] = imm_b(instr)
    d["imm_U"] = imm_u(instr)
    d["imm_J"] = imm_j(instr)

    return d

# ------------------------------------------------------------
# Control Unit
# ------------------------------------------------------------

def main_control(d):
    """
    TODO
    Implement the main control unit.

    Based on opcode, generate control signals:

    RegWrite
    MemRead
    MemWrite
    MemToReg
    ALUSrc
    Branch
    Jump
    JumpReg
    ALUOp
    ImmSel
    BrType
    """   

    c = {
        "RegWrite": 0,
        "MemRead": 0,
        "MemWrite": 0,
        "MemToReg": 0,
        "ALUSrc": 0,
        "Branch": 0,
        "Jump": 0,
        "JumpReg": 0,
        "ALUOp": None,
        "ImmSel": None,
        "BrType": None,
    }

    if d["opcode"] == 0x33: #Rtype
        c["RegWrite"] = 1
        c["ALUOp"] = "RType"
    elif d["opcode"] == 0x13: #Itype
        c["RegWrite"] = 1
        c["ALUSrc"] = 1
        c["ALUOp"] = "IType"
        c["ImmSel"] = "I"
    elif d["opcode"] == 0x3: #lw
        c["ALUSrc"] = 1
        c["MemToReg"] = 1
        c["RegWrite"] = 1
        c["MemRead"] = 1
        c["ImmSel"] = "I"
    elif d["opcode"] == 0x23: #sw
        c["ALUSrc"] = 1
        c["MemWrite"] = 1
        c["ImmSel"] = "S"
    elif d["opcode"] == 0x63:
        c["Branch"] = 1
        c["ImmSel"] = "B"
        if d["funct3"] == 0x0:
            c["BrType"] = "beq" 
        elif d["funct3"] == 0x1:
            c["BrType"] = "bne"
        elif d["funct3"] == 0x4:
            c["BrType"] = "blt"
        elif d["funct3"] == 0x5:
            c["BrType"] = "bge"
        elif d["funct3"] == 0x6:
            c["BrType"] = "bltu"
        elif d["funct3"] == 0x7:
            c["BrType"] = "bgeu"
    elif d["opcode"] == 0x6f:
        c["RegWrite"] = 1
        c["Jump"] = 1
        c["ImmSel"] = "J"
        c["ALUSrc"] = 1
    elif d["opcode"] == 0x67:
        c["RegWrite"] = 1
        c["JumpReg"] = 1
        c["ImmSel"] = "I"
        c["ALUSrc"] = 1
    return c


# ------------------------------------------------------------
# ALU Control
# ------------------------------------------------------------

def alu_control(c, d):
    """
    TODO
    Determine ALU operation string:

    ADD
    SUB
    AND
    OR
    XOR
    SLL
    SRL
    SRA
    SLT
    SLTU

    Use:
    - ALUOp
    - funct3
    - funct7
    """

    if c["ALUOp"] == "RType":
        if d["funct3"] == 0x0:
            if d["funct7"] == 0x00:
                return "ADD"
            if d["funct7"] == 0x01:
                return "MUL"
            if d["funct7"] == 0x20:
                return "SUB"
        elif d["funct3"] == 0x7:
            return "AND"
        elif d["funct3"] == 0x6:
            if d["funct7"] == 0x00:
                return "OR"
            if d["funct7"] == 0x01:
                return "MOD"
        elif d["funct3"] == 0x4:
            if d["funct7"] == 0x00:
                return "XOR"
            if d["funct7"] == 0x01:
                return "DIV"
        elif d["funct3"] == 0x1:
            return "SLL"
        elif d["funct3"] == 0x5:
            if d["funct7"] == 0x00:
                return "SRL"
            if d["funct7"] == 0x20:
                return "SRA"
        elif d["funct3"] == 0x2:
            return "SLT"
        elif d["funct3"] == 0x3:
            return "SLTU"
        else:
            return None
    elif c["ALUOp"] == "IType":
        if d["funct3"] == 0x0:
            return "ADDI"
        elif d["funct3"] == 0x7:
            return "ANDI"
        elif d["funct3"] == 0x6:
            return "ORI"
        elif d["funct3"] == 0x4:
            return "XORI"
        elif d["funct3"] == 0x1:
            return "SLLI"
        elif d["funct3"] == 0x5 and d["funct7"] == 0x00:
            return "SRLI"
        elif d["funct3"] == 0x5 and d["funct7"] == 0x20:
            return "SRAI"
        elif d["funct3"] == 0x2:
            return "SLTI"
        elif d["funct3"] == 0x3:
            return "SLTIU"
        else:
            return None
    else:
        return None
    return None


# ------------------------------------------------------------
# ALU
# ------------------------------------------------------------

def alu_exec(op, a, b):
    """
    TODO
    Execute ALU operation.

    Must support:

    ADD
    SUB
    AND
    OR
    XOR
    SLL
    SRL
    SRA
    SLT
    SLTU

    Return 32-bit result.
    """
    if op == "ADD" or op == "ADDI":
        return a + b
    elif op == "MUL":
        return a * b
    elif op == "DIV":
        #division in riscv32 rounds to the whole number towards 0, i.e. 10/4 = 2
        if b != 0:
            return a//b
        #riscv32 does not exception handle for division by 0, instead it simply returns 0xFFFFFFFF, or -1 since this is signed division
        else:
            return -1
    #This operation is referred to as "rem" in the official riscv32 instruction encodings, but we all know it as mod
    elif op == "MOD":
        #simply returns the remainder of the division of a and b
        if b != 0:
            return a % b
        #if mod by 0 is attempted, riscv32 returns the value stored in rs1 rather than raising an error
        else:
            return a
    elif op == "SUB":
        return a - b
    elif op == "AND" or op == "ANDI":
        return a & b
    elif op == "OR" or op == "ORI":
        return a | b
    elif op == "XOR" or op == "XORI":
        return a ^ b
    elif op == "SLL" or op == "SLLI":
        return a << b
    elif op == "SRL" or op == "SRLI":
        return a >> b
    elif op == "SRA" or op == "SRAI":
        return a >> b
    elif op == "SLT" or op == "SLTI":
        if s32(a) < s32(b):
            return 1
        else:
            return 0
    elif op == "SLTU" or op == "SLTIU":
        if u32(a) < u32(b):
            return 1
        else:
            return 0
    return 0


# ------------------------------------------------------------
# IF Stage
# ------------------------------------------------------------

def stage_if(pc, imem):
    """
    Instruction Fetch stage.

    Compute:
        pc
        pc_plus4
        instr

    If PC not in instruction memory,
    return instr=None to signal halt.
    """

    out = {}
    out["pc"] = pc
    out["pc_plus4"] = pc + 4
    if pc in imem.keys():
        out["instr"] = imem[pc]
    else:
        out["instr"] = None
    return out


# ------------------------------------------------------------
# Immediate Selector
# ------------------------------------------------------------

def select_imm(d, c):
    """
    Return correct immediate depending on control signal ImmSel.
    """
    if c["ImmSel"] == "I":
        return d["imm_I"]
    elif c["ImmSel"] == "S":
        return d["imm_S"]
    elif c["ImmSel"] == "B":
        return d["imm_B"]
    elif c["ImmSel"] == "J":
        return d["imm_J"]
    elif c["ImmSel"] == "U":
        return d["imm_U"]
    else:
        return None


# ------------------------------------------------------------
# ID Stage
# ------------------------------------------------------------

def stage_id(instr, regs):
    """
    TODO

    Decode instruction
    Generate control signals
    Read register file
    Select immediate

    Return dictionary with:
        decoded instruction
        control signals
        rs1_val
        rs2_val
        rd
        immediate
    """

    instruction = decode(instr)

    control = main_control(instruction)

    out = {}

    out["d"] = instruction
    out["c"] = control
    out["imm"] = select_imm(instruction, control)
    out["rs1_val"] = regs[instruction["rs1"]]
    out["rs2_val"] = regs[instruction["rs2"]]
    out["rd"] = instruction["rd"]
    out["rs1"] = instruction["rs1"]
    out["rs2"] = instruction["rs2"]

    return out


# ------------------------------------------------------------
# Branch Logic
# ------------------------------------------------------------

def branch_taken(br_type, rs1_val, rs2_val):
    """
    TODO

    Implement branch comparisons:

    beq
    bne
    blt
    bge
    bltu
    bgeu
    """
    if br_type == "beq":
        if rs1_val == rs2_val:
            return True
        else:
            return False
    elif br_type == "bne":
        if rs1_val != rs2_val:
            return True
        else:
            return False
    elif br_type == "blt":
        if rs1_val < rs2_val:
            return True
        else:
            return False
    elif br_type == "bge":
        if rs1_val >= rs2_val:
            return True
        else:
            return False
    elif br_type == "bltu":
        if u32(rs1_val) < u32(rs2_val):
            return True
        else:
            return False
    elif br_type == "bgeu":
        if u32(rs1_val) >= u32(rs2_val):
            return True
        else:
            return False
    else:
        return False


# ------------------------------------------------------------
# EX Stage
# ------------------------------------------------------------

def stage_ex(pc, pc_plus4, id_out):
    """
    Execute stage responsibilities:

    - determine ALU operation
    - select ALU input2
    - compute ALU result
    - evaluate branch condition
    - compute branch target
    - compute jump target
    - determine next PC
    - set flag for type of instruction
    """

    out = {}

    alu_operation = alu_control(id_out["c"], id_out["d"])
    branch = branch_taken(id_out["c"]["BrType"], id_out["rs1_val"], id_out["rs2_val"])

    out["alu_op"] = alu_operation
    out["alu_res"] = 0
    out["next_pc"] = pc_plus4
    out["taken"] = False
    out["br_target"] = 0
    out["jal_target"] = 0
    out["jalr_target"] = 0
    out["arith"] = 0
    out["mem"] = 0
    out["branch"]= 0
    out["jump"] = 0

    if id_out["c"]["ALUOp"] == "RType":
        alu_result = alu_exec(alu_operation, id_out["rs1_val"], id_out["rs2_val"])
        out["alu_res"] = alu_result
        out["arith"] = 1
    elif id_out["c"]["ALUOp"] == "IType":
        alu_result = alu_exec(alu_operation, id_out["rs1_val"], id_out["imm"])
        out["alu_res"] = alu_result
        out["arith"] = 1

    if id_out["c"]["Branch"] == 0 and id_out["c"]["Jump"] == 0 and id_out["c"]["JumpReg"] == 0:
        out["next_pc"] = pc_plus4
        out["taken"] = False
    elif id_out["c"]["Branch"] == 1:
        if branch == True:
            out["next_pc"] = pc + id_out["imm"]
            out["br_target"] = pc + id_out["imm"]
            out["taken"] = True
            out["branch"] = 1
        else:
            out["next_pc"] = pc_plus4
            out["taken"] = False
            out["branch"] = 1
    elif id_out["c"]["Jump"] == 1:
        pc_result = alu_exec("ADD", pc, id_out["imm"])
        out["next_pc"] = pc_result
        out["jal_target"] = pc_result
        out["jump"] = 1
    elif id_out["c"]["JumpReg"] == 1:
        pc_result = ((alu_exec("ADD", id_out["rs1_val"], id_out["imm"])) &~1)
        out["next_pc"] = pc_result
        out["jalr_target"] = pc_result
        out["jump"] = 1

    if id_out["c"]["MemWrite"] or id_out["c"]["MemRead"]:
        alu_result = id_out["rs1_val"] + id_out["imm"]
        out["alu_res"] = alu_result
        out["mem"] = 1

    return out

# ------------------------------------------------------------
# Data Memory
# ------------------------------------------------------------

def dmem_load_word(dmem, addr):
    """
    TODO

    Load word from data memory.

    Enforce 4-byte alignment.
    """

    return dmem[addr]


def dmem_store_word(dmem, addr, value):
    """
    TODO

    Store word into data memory.

    Enforce 4-byte alignment.
    """
    dmem[addr] = value
    pass

# ------------------------------------------------------------
# MEM Stage
# ------------------------------------------------------------

def stage_mem(id_out, ex_out, dmem):
    """
    TODO

    Handle memory access.

    If lw:
        read from memory

    If sw:
        write to memory
    """

    out = {}

    out["mem_data"] = 0
    out["addr"] = 0

    out["addr"] = ex_out["alu_res"]

    if id_out["c"]["MemWrite"] == 1:
        out["mem_data"] = id_out["rs2_val"]
        dmem_store_word(dmem, out["addr"], out["mem_data"])
    elif id_out["c"]["MemRead"] == 1:
        out["mem_data"] = dmem_load_word(dmem, out["addr"])

    return out


# ------------------------------------------------------------
# WB Stage
# ------------------------------------------------------------

def stage_wb(pc_plus4, id_out, ex_out, mem_out, regs):
    """
    TODO

    Writeback stage:

    Determine writeback value.

    Write to register file if RegWrite.

    Ensure x0 always stays 0.
    """

    out = {}

    out["wb_val"] = 0
    out["wb_rd"] = 0
    out["did_write"] = False

    if id_out["c"]["RegWrite"] == 1:
        out["wb_rd"] = id_out["rd"]
        if id_out["c"]["ALUOp"] == "RType" or id_out["c"]["ALUOp"] == "IType":
            out["wb_val"] = ex_out["alu_res"]
        elif id_out["c"]["MemToReg"] == 1:
            out["wb_val"] = mem_out["mem_data"]
        elif id_out["c"]["Jump"]  == 1 or id_out["c"]["JumpReg"]  == 1:
            out["wb_val"] = pc_plus4
        regs[id_out["rd"]] = out["wb_val"]
        out["did_write"] = True

    if out["wb_rd"] == 0:
        out["did_write"] = False
    regs[0] = 0x0

    return out


# ------------------------------------------------------------
# Trace Generation
# ------------------------------------------------------------

def trace_line(step, if_out, id_out, ex_out, mem_out, wb_out):
    """
    TODO

    Produce readable trace string containing:

    step
    PC
    instruction
    ALU result
    memory access
    register writeback
    next PC
    """
    if ex_out["alu_op"] != None:
        mnem = ex_out["alu_op"].lower()
    elif id_out["c"]["BrType"] != None:
        mnem = id_out["c"]["BrType"]
    elif id_out["c"]["MemToReg"] == 1:
        mnem = "lw"
    elif id_out["c"]["MemWrite"] == 1:
        mnem = "sw"
    elif id_out["c"]["Jump"] == 1:
        mnem = "jal"
    elif id_out["c"]["JumpReg"] == 1:
        mnem = "jalr"
    else:
        mnem = "unknown instruction"
    
    return f"{step} | pc={fmt_hex32(if_out["pc"])} | instr={fmt_hex32(if_out["instr"])} | {mnem}\nRegW={id_out["c"]["RegWrite"]} MemR={id_out["c"]["MemRead"]} MemW={id_out["c"]["MemWrite"]} ALUSrc={id_out["c"]["ALUSrc"]} Br={id_out["c"]["Branch"]}\nalu={ex_out["alu_op"]} res={ex_out["alu_res"]}\nwb={wb_out["wb_rd"]}<-{wb_out["wb_val"]}\nnext_pc={fmt_hex32(ex_out["next_pc"])}"

# ------------------------------------------------------------
# Program Loader
# ------------------------------------------------------------

def load_imem_from_file(path):

    imem = {}
    pc = 0

    f = open(path)

    for line in f:
        s = line.strip()
        if not s:
            continue

        instr = int(s, 16) & MASK32

        imem[pc] = instr
        pc += 4

    f.close()

    return imem

# ------------------------------------------------------------
# Log Writers
# ------------------------------------------------------------

def write_trace_log(lines):

    f = open("trace.log", "w")

    for l in lines:
        f.write(l + "\n")

    f.close()

def write_instruction_mix_log(icount, imix):

    f = open("instruction_mix.log", "w")

    f.write("Instruction Count\n--------------------\n")
    for i in icount:
        f.write(i + "\n")
    f.write("====================\n")
    f.write("Instruction Percentages\n--------------------\n")
    for i in imix:
        f.write(i + "\n")


def write_regs_log(regs):

    f = open("regs_final.log", "w")

    for i in range(32):
        f.write("x%d = 0x%08X\n" % (i, regs[i]))

    f.close()


def write_dmem_log(dmem):

    f = open("dmem_final.log", "w")

    for a in sorted(dmem.keys()):
        f.write("0x%08X : 0x%08X\n" % (a, dmem[a]))

    f.close()


# ------------------------------------------------------------
# Main Simulation Loop
# ------------------------------------------------------------

def main():

    imem = load_imem_from_file("hex_inst.txt")

    regs = [0] * 32
    dmem = {}

    pc = 0
    steps = 0

    trace_lines = []
    instr_count = []
    instr_mix = []

    total_instructions = 0
    memory_instructions = 0
    arithmetic_instructions = 0
    branch_instructions = 0
    jump_instructions = 0

    while True:

        if_out = stage_if(pc, imem)

        if if_out["instr"] is None:
            break

        pc_plus4 = if_out["pc_plus4"]
        instr = if_out["instr"]

        id_out = stage_id(instr, regs)

        ex_out = stage_ex(pc, pc_plus4, id_out)

        mem_out = stage_mem(id_out, ex_out, dmem)

        wb_out = stage_wb(pc_plus4, id_out, ex_out, mem_out, regs)

        trace_lines.append(trace_line(steps, if_out, id_out, ex_out, mem_out, wb_out))

        pc = ex_out["next_pc"]

        regs[0] = 0

        steps += 1

        total_instructions += 1
        if ex_out["arith"] == 1:
            arithmetic_instructions += 1
        elif ex_out["mem"] == 1:
            memory_instructions += 1
        elif ex_out["branch"] == 1:
            branch_instructions += 1
        elif ex_out["jump"] == 1:
            jump_instructions += 1

    instr_count.append(f"Arithmetic: {arithmetic_instructions}")
    instr_count.append(f"Memory: {memory_instructions}")
    instr_count.append(f"Branch: {branch_instructions}")
    instr_count.append(f"Jump: {jump_instructions}")
    instr_mix.append(f"Arithmetic: {(round(arithmetic_instructions/total_instructions*100, 2))}%")
    instr_mix.append(f"Memory: {(round(memory_instructions/total_instructions*100, 2))}%")
    instr_mix.append(f"Branch: {(round(branch_instructions/total_instructions*100, 2))}%")
    instr_mix.append(f"Jump: {(round(jump_instructions/total_instructions*100, 2))}%")

    write_trace_log(trace_lines)
    write_regs_log(regs)
    write_dmem_log(dmem)
    write_instruction_mix_log(instr_count, instr_mix)

    print("HALT")
    print("steps =", steps)


if __name__ == "__main__":
    main()
