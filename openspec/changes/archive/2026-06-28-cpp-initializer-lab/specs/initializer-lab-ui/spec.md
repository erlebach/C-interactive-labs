## ADDED Requirements

### Requirement: Application window with tabbed topic navigation
The system SHALL present a Dear PyGui application window containing a tab bar with one tab per initializer topic. Tabs SHALL be grouped into "Core" (6 tabs: default, value, direct, copy, list/brace, aggregate) and "Gotchas" (3 tabs: most vexing parse, explicit-vs-implicit, initializer_list hijacking).

#### Scenario: App launch shows all topic tabs
- **WHEN** the application is launched
- **THEN** the window displays a tab bar with 9 tabs grouped under "Core" and "Gotchas" headers

#### Scenario: Switching tabs changes the control panel
- **WHEN** the user clicks a different topic tab
- **THEN** the control panel updates to show the controls relevant to that topic, and the code/output/memory panels reset to their last-run state for that topic (or empty if not yet run)

### Requirement: Control panel per topic
Each topic tab SHALL expose a set of UI controls (radio buttons, dropdowns, text inputs, checkboxes) that parameterize the C++ initialization demonstrated by that topic. The available controls SHALL be defined per-topic in the topic-content capability.

#### Scenario: Toggling a control updates the generated code preview
- **WHEN** the user changes any control in the active topic's control panel
- **THEN** the code panel updates to show the newly generated C++ source string (without running it)

### Requirement: Read-only code display panel
The system SHALL display the generated C++ source code in a read-only text panel. Students SHALL NOT be able to edit the code directly; manipulation is via controls only.

#### Scenario: Code panel reflects current control state
- **WHEN** controls are changed or a topic is switched
- **THEN** the code panel shows the C++ source corresponding to the current control state

### Requirement: Run button triggers compilation and execution
Each topic tab SHALL have a "Run" button that compiles and executes the currently generated C++ snippet using the local g++ toolchain.

#### Scenario: Successful run displays output
- **WHEN** the user clicks Run and the snippet compiles and runs successfully
- **THEN** the output panel displays stdout, stderr (if any), and exit code; the memory panel displays the hex bytes of the target variable

#### Scenario: Compile error displayed as a result
- **WHEN** the user clicks Run and g++ produces a compile error
- **THEN** the output panel displays the compiler stderr and a non-zero exit indicator; the memory panel shows "n/a (compile failed)"; this is treated as a valid result, not an application error

### Requirement: g++ availability check on startup
The system SHALL probe for a local g++ supporting C++20 on startup. If unavailable, the app SHALL still launch but disable the Run button with an explanatory message.

#### Scenario: g++ missing
- **WHEN** the app starts and g++ is not found on PATH
- **THEN** the Run button is disabled on all tabs and a status message reads "g++ not found — install a C++20-capable g++ to run snippets"

#### Scenario: g++ too old
- **WHEN** the app starts and g++ is found but does not support -std=c++20
- **THEN** the Run button is disabled and a status message indicates the g++ version is too old
