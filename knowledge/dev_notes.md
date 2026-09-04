# Development Notes

The host test suite currently contains seven CTest tests.

The deterministic controller test uses approximately:
x = 5.15 m
y = -0.97 m

The expected desired steering angle is approximately -11.22 degrees.

The same shared steering controller source has been verified on host,
STM32F429, and Zynq-7000 PS environments.

Source code modification should not be performed automatically in
Project Sentinel v0.1. Safe automated actions are limited to build,
test, configure, and clean rebuild operations.
