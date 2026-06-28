# cpp_initializer_lab

A small Dear PyGui desktop application for the ISC5305 **C++ Initializer Lab**.

The lab lets students explore how C++ initializes variables in memory by
generating small C++ snippets, compiling them with `g++`, running them, and
displaying the resulting memory bytes in a GUI.

## Prerequisites

- **Python 3.10+** (developed on 3.14)
- **`g++`** with support for `-std=c++20`
  - On macOS, install the Xcode Command Line Tools:
    ```bash
    xcode-select --install
    ```
  - Verify:
    ```bash
    g++ --version
    ```
- A desktop environment (the GUI needs a display).

## Install

From the project root:

```bash
pip install -r requirements.txt
```

## Run

```bash
python -m cpp_initializer_lab.app
```

This opens the Dear PyGui window. The app will probe for `g++` on startup and
warn you if it is missing or too old to support C++20.

## Project layout

```
cpp_initializer_lab/
    __init__.py
    compiler_runner.py   # g++ probe + compile/run logic
    code_generator.py    # builds C++ source from lab parameters  (other module)
    topics.py            # lab topic definitions                  (other module)
    app.py               # Dear PyGui entry point                 (other module)
    tests/
        __init__.py
        test_compiler_runner.py
```

## Tests

```bash
python -m pytest cpp_initializer_lab/tests/ -v
```
