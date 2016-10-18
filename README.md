# 诚尚Micro MCxxxx Emulator

![Travis Build Status](https://travis-ci.org/Yuffster/mcx4.svg)

This library provides an emulator for the 诚尚Micro MCxxxx family of Microprocessors, specifically the MC4000 and MC6000.

## Available Microcontrollers

The MC4000 and MC6000 differ in program memory capacity, number of registers, and XBus port availability.

| Model  | Program Memory | ACC | DAT | XBus | GPIO |
|--------|----------------|-----|-----|------|------|
| MC4000 | 9 lines        | Yes | No  | 2    | 2    | 
| MC6000 | 14 lines       | Yes | Yes | 4    | 2    |  

## GPIO

Microcontrollers can communicate with each other using onboard GPIOs, `p0` and `p1`.

A utility method is provided to gain access to the port of an instantiated Microcontroller object.

Port interfaces have a `link` method which will attach them through a circuit to the desired port.

Additionally, all interfaces and registers have a `read` and `write` method to access and modify their respective values.

When a port is read, the maximum value of all linked ports will be returned.

Ports cannot be connected to any ports within the same processor.

```python
from mcx4 import MC4000

mc1 = MC4000()
mc2 = MC6000()

mc1.p0.link(mc2.p1)  # Link the ports.
mc1.p0.read()  # 0
mc2.p1.read()  # 0

mc1.p0.write(100)
mc2.p1.read()  # 100
```

Reading from a port will reset its output value to 0.

```python
from mcx4 import MC4000

mc1 = MC4000()
mc2 = MC6000()

mc1.p0.link(mc2.p1)  # Link the ports.
mc1.p0.read()  # 0
mc2.p1.read()  # 0

mc1.p0.write(100)
mc1.p0.read()  # 0
mc2.p0.read()  # 0
```

## Instruction Execution

Instructions can be run on a Microcontroller by using the `execute` method.

```python
from mcx4 import MC4000

mc1 = MC4000()

mc1.execute("""
  mov 10 acc
""")

mc1.value('acc')  # 10
```

## Language Reference

This emulator has near complete support for the entire MCxxxx instruction set.

Anything on a line following `#` or `;` will be discarded.

**Note**: `;` is a syntactic element not available on the real world version of the MCxxxx family and provided for preferential use only.  Please remember to discard any `;` comments before attempting to compile your code on actual devices.

```
# This line will be discarded.
mov 1 acc    ; Write 1 to ACC
mov 2 acc    # Write 2 to ACC
; This line will be discarded.
``` 

### nop

No operation, but takes a full cycle.  Useful for synchronizing between two processors.

#### Examples

```
  nop         ; This line doesn't do anything.
```

### mov [Register/Input] [Register]

Copy the value of the first argument into the register named by
the second argument.

#### Examples

Write the value 1 to `ACC`.

```
mov 1 acc
```

Write the value of `p0` to `ACC`.

```
mov p0 acc
```

Write the value of `ACC` to `p0`.

```
mov acc p0
```

### add [Register/Input]

Add the value of the provided register or input to `ACC`.

#### Examples

```
mov 1 acc
add 1
add 1         ; ACC is 3.
```

### sub [Register/Input]

Subtract the value of the provided register or input from `ACC`.

#### Examples

```
mov 0 acc
add 1
add 1         ; ACC is -2.
```

### mul [Register/Input]

Multiply the value of the provided register or input by `ACC` and store the result in the `ACC` register.

#### Examples

```
mov 5 acc
mul 2         ; ACC is 10.
```

### not

Stores the value of 100 in `ACC` if the current value is 0.  Otherwise, stores 0.

### dgt [Register/Input]

Replace the `ACC` register value with that of the digit indicated by the register or input value.

#### Examples

```
mov 567 acc
dgt 0        ; ACC is 7.
```

```
mov 567 acc
dgt 1        ; ACC is 6.
```

```
mov 567 acc
dgt 2         ; ACC is 5.
```

### dst [Register/Input] [Register/Input]

Set the value of the provided digit within `ACC` to the desired value.

### Examples

```
mov 567 acc
dst 0 9       ; ACC is 569.
```

```
mov 567 acc
dst 1 9       ; ACC is 597.
```

```
mov 567 acc
dst 2 9       ; ACC is 967.
```

### jmp

Jump to the instruction following the specified label.

#### Examples

Jump to 'l' label, repeatedly incrementing the value of `ACC`.

```
l:add 1
jmp l
```

### slp [Register/Input]

*Not implemented.*

#### Examples

Sleep for one time unit.

```
slp 1
```

Sleep for the number of time units stored in `ACC`.

```
slp acc
```

### slx [XBus]

*Not implemented.*

Sleep until data is available on the specified XBus port.

#### Examples

Sleep until input is available on `x0`.

```
slx x0
```

### Comparison Operations

The MCxxxx CPU supports a wide range of comparison operations, including `teq`, `tcp`, `tgt` and `tlt`.

When a comparison operation is executed, all instructions prefixed with `-` or `+` will be enabled or disabled depending on the result of the comparison.

For example, the code below would enable the `mov 2 acc` instruction and disable the `mov 0 acc` instruction.

```
  teq acc 1
+ mov 2 acc
- mov 0 acc
```

#### teq

Compares the equality of the first and second values.

| result   |  +               | -              |
|----------|------------------|----------------|
| a  = b   | enabled          | disabled       |
| a != b   | disabled         | enabled        |

#### tcp

Compares first and second values.

| result   |  +               | -              |
|----------|------------------|----------------|
| a > b    | enabled          | disabled       |
| a < b    | disabled         | enabled        |
| a = b    | disabled         | disabled       |

#### tgt

Determines whether a is greater than b.

| result   |  +               | -              |
|----------|------------------|----------------|
| a > b    | enabled          | disabled       |
| a < b    | disabled         | enabled        |
| a = b    | disabled         | disabled       |

#### tlt

Determines whether a is less than b.

| result   |  +               | -              |
|----------|------------------|----------------|
| a > b    | disabled         | enabled        |
| a < b    | enabled          | disabled       |
| a = b    | disabled         | disabled       |
