# Past Errors

## Timeout Boundary Behavior

The steering controller uses a timeout threshold of 300 ms.
When no valid target update arrives for the timeout duration,
the controller transitions to neutral steering.

Boundary conditions around 300 ms should be tested carefully because
a comparison change between > and >= can cause test failures.

## UART Frame Validation

Malformed UART frames must be rejected before deserialization.
CRC-16 validation is performed before TargetCommand is accepted.

## Build Configuration

Stale CMake build directories can occasionally cause configuration
or dependency problems. A clean configure and rebuild can be used as
a safe recovery action.
