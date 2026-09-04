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


## Auto-Recovered Incident - 2026-09-04T18:19:06.762708+09:00

### Symptom

Status: BUILD_FAILED

Git status and diff returned no output. Build failed with an explicit Sentinel fault indicating stale or corrupted CMake build state. Tests passed: 7/7.

### Diagnosis

Current test results are healthy, but the build directory is unusable or stale. Historical notes support clean reconfiguration for this condition; they do not indicate a source defect.

### Recovery

Action: clean_rebuild

### Verification

Status: HEALTHY

Build completed successfully and all 7 tests passed.

### Result

AUTO-RECOVERED
