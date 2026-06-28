## Context

This is a greenfield project under the ISC5305 course workspace (`/Users/erlebach/src/2026/isc5305_f2026/opencode`). The course teaches students to use OpenCode critically with open-source models. The C++ Initializer Lab is both a teaching artifact (students explore C++ initialization interactively) and an example of code produced via the OpenCode workflow.

The project currently contains only OpenSpec scaffolding — no application code exists yet. Students are assumed to have a local `g++` supporting C++20 and Python 3.10+ with pip available.

The lab is a **desktop GUI app** (Dear PyGui) that generates C++ snippets from UI controls, compiles and runs them with the local `g++`, and displays real compiler/runtime output plus a hex dump of the initialized variable's memory.

## Goals / Non-Goals

**Goals:**
- Let students explore all 6 core C++ initialization forms and 3 gotcha topics by toggling parameters and observing real compiler behavior.
- Show the generated C++ source (read-only) so students connect UI controls to syntax.
- Display stdout, stderr, exit code, and raw memory bytes of the initialized variable.
- Run entirely locally with no network or server dependencies.
- Be robust enough for self-paced student use (graceful handling of compile errors, timeouts, missing g++).

**Non-Goals:**
- A full C++ interpreter or REPL — we compile real snippets with g++, not interpret them.
- Student-editable code — the code panel is read-only; students manipulate via toggles only. (A future change could add an editable mode.)
- Web deployment — desktop only.
- Coverage of C++20 designated initializers, member initializer list ordering, or CTAD — these are out of scope for this change (could be a follow-up).
- Grading or assessment features — this is an exploration tool, not a quiz.

## Decisions

### Decision 1: Dear PyGui (Python) over a native C++ GUI

**Choice:** Build the UI in Python with Dear PyGui, shelling out to `g++` for compilation.

**Rationale:** Dear PyGui provides immediate-mode GUI with minimal boilerplate, runs locally without a browser, and Python's `subprocess` makes shelling out to `g++` trivial. A native C++ GUI (Qt, ImGui-via-C++) would couple the UI to the same compiler being demonstrated, complicating the build and muddying the "this is the compiler under test" message. Python keeps the UI and the compiler-under-test cleanly separated.

**Alternatives considered:**
- *Shiny for Python (web)*: More familiar to some students, but adds a server process and browser dependency, and the "local toolchain" choice favors a self-contained desktop app.
- *Pure C++ CLI menu*: Simplest, but loses the live-toggle pedagogy the user explicitly chose.

### Decision 2: Template-based code generation with substitution

**Choice:** Each topic defines a Python string template with named placeholders (e.g., `{type}`, `{value}`, `{form}`). The UI control state fills the placeholders to produce the final C++ source.

**Rationale:** C++ initialization syntax is regular enough within a single topic that string templates with substitution are sufficient and readable. A full AST-based generator would be over-engineering for ~9 topics and would obscure the template-to-syntax mapping that is itself pedagogically useful.

**Alternatives considered:**
- *AST manipulation (libclang)*: Too heavy; the snippets are small and template-shaped.
- *Hand-written if/else string building*: Equivalent to templates but less readable.

### Decision 3: Compile to temp dir, run, capture output, hex-dump memory

**Choice:** For each "Run":
1. Write the generated `.cpp` to a temp directory.
2. Invoke `g++ -std=c++20 <file> -o <exe>` with a timeout.
3. If compile succeeds, run the exe and capture stdout/stderr/exit code.
4. For the memory view: the generated snippet writes the target variable's bytes to a file (or stdout in a structured format) which the app reads and displays as hex.

**Rationale:** Compile errors are pedagogically valuable (e.g., narrowing rejection, `explicit` + copy-init). The runner must treat non-zero exit and stderr as *results to display*, not failures. Memory bytes require the snippet to explicitly dump them — we inject a small helper into the generated code that prints `sizeof` and the raw bytes of the target variable.

**Alternatives considered:**
- *GDB/LLDB to inspect memory*: Too heavyweight and fragile across platforms.
- *Pre-computed results per toggle combination*: Dishonest — defeats the purpose of using a real compiler.

### Decision 4: Tabbed navigation, one tab per topic

**Choice:** A tab bar with 9 tabs (6 core forms + 3 gotchas), possibly grouped (Core / Gotchas).

**Rationale:** Self-paced use requires non-linear navigation and easy comparison between forms. Tabs make the full topic scope visible at a glance and allow one-click comparison — the core pedagogical motion for initializers. Dropdowns hide scope; guided walkthroughs impose a rigid path.

**Alternatives considered:**
- *Dropdown topic selector*: Hides the topic list; students won't know what they haven't explored.
- *Guided linear walkthrough*: Too rigid for self-paced curiosity-driven exploration.

### Decision 5: Generated snippet includes a memory-dump helper

**Choice:** The code generator wraps the student-visible initialization line in a harness that, after initialization, prints the variable's type, size, and raw bytes to stdout in a parseable format (e.g., a `MEMBYTES:` line). The app parses this to populate the memory panel.

**Rationale:** Keeps the student-visible code focused on the initialization itself while still producing the memory data. The harness is clearly delimited with comments so students see it's instrumentation, not the lesson.

## Risks / Trade-offs

- **[Risk] g++ not installed or wrong version** → On startup, the app probes for `g++ --version` and reports a clear error if missing or pre-C++20. The UI still loads so students can read the topic content, but the Run button is disabled with an explanatory message.
- **[Risk] Infinite loop in generated snippet** → The runner enforces a timeout (e.g., 5 seconds) on both compile and execute steps, and reports the timeout as a result.
- **[Risk] Malicious or accidental filesystem writes in generated code** → Snippets are generated from constrained templates, not student-written, so this is low-risk. Temp dir is cleaned up per run. (If a future change adds editable code, sandboxing becomes required.)
- **[Trade-off] Template-based generation limits flexibility** → Students can't write arbitrary C++, only toggle within the designed parameter space. This is intentional for a guided lab but limits free exploration. Acceptable for this change; editable mode is a non-goal.
- **[Trade-off] Memory dump requires injected harness code** → Students see slightly more than just the initialization line. Mitigated by clearly commenting the harness as instrumentation.
- **[Risk] Platform differences in g++ output/error formatting** → The app displays raw stderr without parsing it, so format differences don't break anything — they just look different across platforms. Acceptable.
