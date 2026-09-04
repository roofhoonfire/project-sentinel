# Project Architecture

The latency-aware-target-control project separates platform-independent
control logic from platform-specific runtime and hardware code.

The common control application receives TargetState data and calculates
desired steering angle using the shared steering controller.

The same common control source is used by host, STM32F429 FreeRTOS,
and Zynq-7000 PS FreeRTOS targets.

The STM32 runtime receives TargetCommand frames over UART, validates
the frame and CRC, converts the payload to TargetState, runs the common
steering controller, maps the desired steering angle to SG90 PWM, and
drives TIM4 CH2 on PB7.

The controller applies steering saturation, deadband, invalid-input
rejection, hold-last behavior, and timeout-to-neutral behavior.
