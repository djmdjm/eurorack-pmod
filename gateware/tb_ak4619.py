import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, FallingEdge, RisingEdge, ClockCycles


async def clock_out_word(dut, word):
    for i in range(16):
        await FallingEdge(dut.bick)
        dut.sdout1.value = (word >> (0xF-i)) & 1
    for i in range(16):
        await FallingEdge(dut.bick)
        dut.sdout1.value = 0

async def clock_in_word(dut):
    word = 0x0000
    for i in range(16+1):
        await RisingEdge(dut.bick)
        word |= dut.sdin1.value << (16-i)
    for i in range(15):
        await RisingEdge(dut.bick)
    return word

def bit_not(n, numbits=16):
    return (1 << numbits) - 1 - n

@cocotb.test()
async def test_adc_dac(dut):

    clock = Clock(dut.CLK, 83, units='ns')
    cocotb.start_soon(clock.start())

    TEST_L0 = 0xFC14
    TEST_R0 = 0xAD0F
    TEST_L1 = 0xDEAD
    TEST_R1 = 0xBEEF

    top = dut
    dut = dut.ak4619_instance
    dut.sdout1.value = 0


    await FallingEdge(dut.lrck)
    await clock_out_word(dut, TEST_L0)
    await clock_out_word(dut, TEST_R0)
    await clock_out_word(dut, TEST_L1)
    await clock_out_word(dut, TEST_R1)

    # Note: this edge is also where dac_words <= sample_in (sample.sv)

    print("Data clocked from sdout1 present at sample_outX:")
    print(hex(dut.sample_out0.value))
    print(hex(dut.sample_out1.value))
    print(hex(dut.sample_out2.value))
    print(hex(dut.sample_out3.value))

    await FallingEdge(dut.lrck)

    result_l0 = await clock_in_word(dut)
    result_r0 = await clock_in_word(dut)
    result_l1 = await clock_in_word(dut)
    result_r1 = await clock_in_word(dut)

    print("Data clocked from sample_inX out to sdin1:")
    print(hex(result_l0), "(inverted: ", hex(bit_not(result_l0)), ")")
    print(hex(result_r0), "(inverted: ", hex(bit_not(result_r0)), ")")
    print(hex(result_l1), "(inverted: ", hex(bit_not(result_l1)), ")")
    print(hex(result_r1), "(inverted: ", hex(bit_not(result_r1)), ")")

    assert result_l0 == bit_not(TEST_L0)
    assert result_r0 == bit_not(TEST_R0)
    assert result_l1 == bit_not(TEST_L1)
    assert result_r1 == bit_not(TEST_R1)

    await FallingEdge(dut.lrck)

@cocotb.test()
async def test_sample(dut):

    clock = Clock(dut.sample_instance.sample_clk, 83, units='ns')
    cocotb.start_soon(clock.start())

    test_values = [
            23173,
            bit_not(14928)+1,
            30000,
            bit_not(30000)+1
    ]

    for value in test_values:
        dut.sample_instance.sample_in0.value = value
        print(f"Stimulus: {hex(value)} {int(value)} (twos comp: {int(bit_not(value) + 1)})")
        await RisingEdge(dut.sample_instance.sample_clk)
        await RisingEdge(dut.sample_instance.sample_clk)
        output = dut.sample_instance.sample_out0.value
        print(f"Response: {hex(output)} {int(output)} (twos comp: {int(bit_not(output) + 1)})")
        print("---")
