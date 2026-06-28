## ADDED Requirements

### Requirement: Compile and run a generated snippet with timeout
The system SHALL compile the generated C++ source by invoking `g++ -std=c++20 <source> -o <executable>` in a temp directory, then execute the resulting binary. Both the compile and execute steps SHALL be subject to a timeout (default 5 seconds each).

#### Scenario: Successful compile and run
- **WHEN** the generated source is valid C++ that compiles and runs within the timeout
- **THEN** the system returns stdout, stderr, exit code, and the parsed memory bytes

#### Scenario: Compile failure
- **WHEN** g++ exits non-zero during compilation
- **THEN** the system returns the compiler stderr as the result, marks exit as "compile failed", and does not attempt to run the binary

#### Scenario: Execution timeout
- **WHEN** the compiled binary runs longer than the execution timeout
- **THEN** the system terminates the process and returns a result indicating "execution timed out"

### Requirement: Temp directory management
The system SHALL create a fresh temp directory for each run, write the source file there, compile and execute within it, then clean up the directory after the run completes (whether success or failure).

#### Scenario: Cleanup after successful run
- **WHEN** a run completes successfully
- **THEN** the temp directory and all its contents are removed

#### Scenario: Cleanup after failure
- **WHEN** a run fails (compile error or timeout)
- **THEN** the temp directory and all its contents are still removed

### Requirement: Parse memory bytes from stdout
The system SHALL parse the `MEMBYTES:` line from the executed binary's stdout to extract the raw bytes of the target variable, and return them for display in the memory panel.

#### Scenario: Memory bytes parsed
- **WHEN** the binary runs successfully and outputs a `MEMBYTES:` line
- **THEN** the system extracts the hex bytes and returns them as the memory result

#### Scenario: No memory bytes on compile failure
- **WHEN** compilation fails and no binary is produced
- **THEN** the system returns "n/a" for the memory result

### Requirement: g++ capability detection
The system SHALL provide a function that probes the local environment for a g++ binary supporting `-std=c++20`, returning a status indicating availability and version suitability.

#### Scenario: g++ available and capable
- **WHEN** the probe runs and finds g++ on PATH supporting C++20
- **THEN** the function returns a status indicating g++ is available and capable

#### Scenario: g++ not found
- **WHEN** the probe runs and no g++ is found on PATH
- **THEN** the function returns a status indicating g++ is missing, with the PATH searched

#### Scenario: g++ found but too old
- **WHEN** the probe runs and finds g++ but it rejects `-std=c++20`
- **THEN** the function returns a status indicating g++ is present but too old, including the detected version
