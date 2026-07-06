# Installing the demonstration-builder skill

This guide gets the skill working on your computer. It assumes no prior setup.
You do **not** need to understand the internals — just follow the steps in order.

Everything here uses paths *relative* to where you put things, so it works no
matter which folder you install into.

---

## What this skill does

It helps you build interactive C++ teaching pages ("demonstrations") from simple
text files. It comes with its own built-in engine, so it does not rely on anything
already being on your machine besides the three prerequisites below.

---

## What you need first (one-time prerequisites)

Three things must be available on your computer:

1. **Python** (version 3.10 or newer) — the engine is written in Python.
2. **A C++ compiler** — either `g++` or `clang++`. This actually compiles the
   example code so the pages show real output. On a Mac, installing Apple's
   "Command Line Tools" provides `clang++`. On Linux, install `g++`.
3. **The PyYAML add-on for Python** — installed in one command in Step 3 below.

To check whether the first two are already there, open a terminal and type:

```bash
python3 --version
g++ --version        # or:  clang++ --version
```

If each prints a version number, you're ready. If not, install the missing one
before continuing.

---

## Step 1 — Put the skill where your assistant can find it

The skill is the folder that contains this `INSTALL.md` file (named
`demonstration-builder`). Copy that **entire folder** — with everything inside it —
into one of these two places:

- **For one project only:** into that project's `.claude/skills/` folder.
- **For every project:** into your personal `.claude/skills/` folder in your home
  directory.

Either location works. The skill figures out where it is on its own.

---

## Step 2 — Install the engine into your project

Open a terminal and go to the top folder of the project where you want to build
teaching pages. Then run the skill's installer (replace `<skill-folder>` with the
path to the folder from Step 1):

```bash
<skill-folder>/scripts/install_engine.sh
```

This copies the engine into your project. It is safe to run again later — it never
deletes or overwrites your own content.

---

## Step 3 — Install the PyYAML add-on

Still in the terminal, install the one Python add-on the engine needs:

```bash
pip install -r <skill-folder>/engine/requirements.txt
```

(You only do this once per computer, or once per Python environment.)

---

## Step 4 — Build your first page to confirm it works

From the same project folder, create a sample page and build it:

```bash
<skill-folder>/scripts/scaffold_subject.sh sample
./build_labs.sh sample
```

If everything is set up correctly, the second command ends with a line like:

```
built 1, failed 0
```

and a finished web page appears under the project's `dist_labs/` folder. Open that
`.html` file in a web browser to see it.

You can delete the `sample` folder (`cpp_labs/sample/`) afterward — it was only a
check that the setup works.

---

## You're done

From here, just tell your assistant what C++ topic you want to teach, and the skill
walks you through building the page. See `SKILL.md` for how the assistant uses it.

---

## If something goes wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| `command not found: python3` | Python isn't installed | Install Python 3.10+ |
| `No module named 'yaml'` | PyYAML add-on missing | Re-run Step 3 |
| Build says a compiler error or `built 0, failed 1` | No C++ compiler found | Install `g++` or `clang++` (Step, prerequisites) |
| `engine not installed` when scaffolding | Skipped Step 2 | Run the installer from Step 2 first |
| `permission denied` running a script | Script lost its run permission | Put `bash` in front, e.g. `bash <skill-folder>/scripts/install_engine.sh` |
