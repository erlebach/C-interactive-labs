## Why

C++ initialization is one of the most confusing topics for students learning the language: there are six distinct initialization forms (`default`, `value`, `direct`, `copy`, `list/brace`, `aggregate`), each with subtly different rules, plus a layer of "gotchas" (most vexing parse, `explicit` constructors, `std::initializer_list` hijacking, narrowing rejection). Textbook explanations are static and cannot convey *how the rules change when you toggle a single parameter*. An interactive lab where students manipulate initializer parameters and observe real compiler output — stdout, stderr, exit code, and raw memory bytes — makes the invisible rules visceral and self-discoverable.

This serves the ISC5305 course goal of teaching students to use OpenCode critically with open-source models, by giving them a concrete, explorable artifact built with those very tools.

## What Changes

- Add a Dear PyGui (Python) desktop application: the **C++ Initializer Lab**.
- The app presents a tabbed UI with one tab per initializer topic (9 topics: 6 core forms + 3 gotcha groups).
- Each tab exposes toggles/controls (form selector, type selector, value input, `explicit` checkbox, `initializer_list` ctor toggle, etc.) that generate a C++ source snippet.
- The app shells out to the local `g++` toolchain to compile and run the generated snippet, then displays: the generated source code (read-only), stdout, stderr, exit code, and the raw hex bytes of the initialized variable's memory.
- Students compare initializer forms by switching tabs and observing how the same toggle change produces different results across forms.
- No new dependencies beyond `dearpygui` (pip) and a local `g++` (already required by the course).

## Capabilities

### New Capabilities

- `initializer-lab-ui`: The Dear PyGui application shell — window, tab bar, control panel, and display panels (code, output, memory). Covers layout, topic navigation, and the run/compile trigger.
- `code-generation`: Translates UI control state into a valid C++ source string per topic, using templates with substitution. Produces the snippet shown to students and fed to the compiler.
- `compiler-runner`: Shells out to `g++` to compile and execute the generated snippet in a temp directory, capturing stdout, stderr, exit code, and a hex dump of the target variable's memory. Handles timeouts and compile errors gracefully (errors are pedagogically valuable, not failures).
- `topic-content`: The per-topic definitions — which controls each tab exposes, which C++ template each uses, and what explanatory text accompanies each. Covers the 9 topics: default init, value init, direct init, copy init, list/brace init, aggregate init, most vexing parse, explicit-vs-implicit ctor, initializer_list hijacking.

### Modified Capabilities

(none — this is a greenfield project with no existing specs)

## Impact

- **New code**: A Python package under the project (likely `cpp_initializer_lab/`) with modules for UI, code generation, compiler execution, and topic definitions.
- **Dependencies**: `dearpygui` (pip install). Local `g++` with C++20 support (course prerequisite).
- **No existing code affected**: Greenfield addition; no modifications to existing project files.
- **Runtime**: Desktop GUI app; students run locally. No server, no network.
- **Pedagogical**: Becomes a lab artifact for ISC5305 students to explore and (per the course goal) to study as an example of code produced via OpenCode + open-source models.
