# **Parallel Autonomous Implementation Pipeline — Briefing Document**

## **1. Purpose of This Document**

This document provides a clear, engineering-aligned overview of the direction we are taking to build a **parallel autonomous implementation workflow**. It is written to be consumed by the team for brainstorming, refinement, and architecture planning.

No code is included—only conceptual design, constraints, and operational details.

______________________________________________________________________

# **2. Problem We’re Trying to Solve**

We want to accelerate development by allowing **multiple autonomous coding agents** (e.g., Claude Code CLI, other CLI-based LLM coders) to work on the **same task in parallel**, producing different implementations.

Our key goals:

1. **Speed & diversity**: Generate multiple independent solutions in parallel (“N competing implementations”).

1. **Quality**: Select the best implementation using a judge process (tests + LLM-based critique).

1. **Learning / Synthesis**: Optionally merge strengths from *all* attempts into a final, refined solution.

1. **Safety**: Keep fully-autonomous agents sandboxed to prevent accidental destructive changes.

1. **Local-first**:

   - No GitHub Actions.
   - No API calls (cost, latency, flexibility).
   - All LLMs are used via CLI (Claude Code CLI, local models via Ollama, etc.).

1. **Determinism**: All coders run in an isolated but identical environment using our existing `devenv` tooling.

We want a workflow that is:

- reproducible
- cheap (leveraging our CLI-based subscriptions)
- locally controllable
- safe
- easy to extend or automate later

______________________________________________________________________

# **3. Why Existing Tools Don’t Fit**

While tools like LangGraph, SWE-agent, OpenHands, and Cursor offer agent capabilities, they all assume one or more of the following:

- heavy reliance on **API access** to the model
- integration with hosted platforms or cloud runners
- a non-deterministic execution environment
- too much abstraction around workflow orchestration
- insufficient sandboxing for fully autonomous runs

Since our constraint is **CLI-only / local-only**, these tools are too high-level or incompatible.

______________________________________________________________________

# **4. Final Direction We’ve Settled On**

We will build a **local, containerized, multi-worktree parallel execution pipeline**.

Each autonomous agent runs inside its **own isolated devenv OCI container**, with its own **Git worktree** mounted into the container. The agent will directly modify files in its assigned worktree. After all agents finish, the host environment inspects each worktree to produce diffs, run evaluations, and select a winner.

This gives us:

- **True isolation:** each agent’s filesystem is contained.
- **Native editing:** agents directly edit real files, not patch text.
- **Deterministic environment:** all tools + services from `devenv`.
- **Full reproducibility:** each worktree is versioned and can be committed independently.
- **Zero reliance on remote APIs.**
- **Post-mortem analysis:** we compute patches/diffs *after* agent runs.
- **Parallelism:** simply run N containers at once.

______________________________________________________________________

# **5. High-Level Architecture**

### **5.1 Components**

1. **Host Orchestrator**
   A local script/service responsible for:

   - creating Git worktrees
   - launching containers
   - passing prompts to each agent’s CLI
   - collecting results
   - performing judging
   - (optional) running a synthesis pass
   - producing a final report

1. **Worktrees**
   Worktrees are created **on the host**, *before* container execution.
   This avoids Git path issues and ensures that all changes in containers appear directly on the host.

1. **Per-Attempt Containers**
   Each attempt runs in an isolated devenv OCI container:

   - container sees only its assigned worktree
   - read-only filesystem except the mounted worktree
   - no network unless explicitly allowed
   - no privileged capabilities
   - consistent toolchain thanks to `devenv`

1. **LLM Coders (CLI-based)**
   Each container runs one CLI-only model, e.g.:

   - Claude Code CLI
   - Codex CLI
   - local `ollama run` model
   - any LLM available via command-line

   These agents:

   - receive a structured prompt
   - autonomously modify files in the mounted worktree
   - optionally run tests to self-correct
   - commit their final changes inside the worktree

1. **Judge Component**
   Runs *after* all attempts finish.
   Responsibilities:

   - diff each worktree against base

   - apply objective criteria:

     - correctness (tests)
     - compile/build success
     - lints/typechecks

   - apply subjective scoring:

     - code cleanliness
     - readability
     - algorithmic quality
     - risk
     - maintainability

   - uses a separate LLM judge (also CLI-based), if desired.

1. **Synthesis Component (Optional / Deferred)**

   - Reserved for future work; default flow stops after judging for now

### **5.2 Host Orchestrator Scope**

- Reads a YAML config file (see §5.3) to determine attempt count, container image, CLI launcher, base prompt, and worktree root.
- Creates Git worktrees on the host and spawns one prebuilt devenv container per worktree.
- Mounts only the assigned worktree into each container, injects the configured prompt/command, and lets the CLI agent run autonomously.
- Records completion solely by container exit status; there are no retries, rescheduling, or post-run cleanup beyond pruning worktrees.
- Treats every container failure as a terminal outcome that downstream judging must handle.

### **5.3 Run Configuration (YAML)**

Suggested keys for the config file:

- `num_attempts`
- `worktree_root`
- `container_image`
- `cli_command` (full command with flags/permissions the agent needs)
- `base_prompt` or path to the prompt template
- `timeout_seconds` (per-container wall clock limit)

Additional per-attempt env vars or mounts can be added as needed, but the orchestrator stays lightweight and declarative.

______________________________________________________________________

# **6. The Execution Workflow**

### **Step 1 — Prepare**

- Read the YAML config to determine attempt count, image, CLI launcher, prompt, timeout, and worktree root.
- Host creates N Git worktrees:
  `.attempts/1`, `.attempts/2`, ... `.attempts/N`
- Each worktree is tied to the same base commit.

### **Step 2 — Run Parallel Agents**

For each worktree:

- Launch a hardened devenv OCI container

- Mount the worktree directory into `/workspace`

- Set the working directory inside container to `/workspace`

- Pass the agent prompt to the CLI LLM

- Agent performs:

  - file modifications
  - iterative editing (if allowed)
  - optional self-testing
  - creates commits in the worktree

- Whether tests run mid-attempt is entirely up to the agent prompt/config; the framework just ensures tools are available.

- Containers run with a single wall-clock timeout from config; if a container exits or times out, we record the attempt as-is with no retry.

At this point, the host filesystem now contains:

- N sets of changes
- N histories/commits
- N varyingly complete/messy implementations

### **Step 3 — Evaluation / Judging**

Performed on the host (or in another neutral container):

1. For each attempt:

   - compute diff to base
   - apply diff to a clean workspace (safety check)
   - run full test suite
   - capture logs/output

1. For subjective scoring:

   - feed diffs + test results + metrics to a CLI LLM judge
   - get back a structured evaluation

1. Rank all attempts

1. Declare a winner after running 1:1 tournament rounds (bracket or round-robin) until one attempt beats all others.

1. Produce judge-facing artifacts for each matchup plus a final narrative on why the champion defeated the field.

#### **Tournament Judging Deliverables**

- For every comparison, capture the paired diffs/tests plus the judge’s short rationale naming the winner.
- Store the per-match rationales and bracket outcome in a single Markdown report; container logs stay inside the containers unless humans need to inspect them manually.
- Detect empty or failed attempts by the absence of commits and let the judge treat them as forfeits.

### **Step 4 — Optional Synthesis Pass (Deferred)**

- Placeholder for a future editor agent; the current scope stops after tournament judging.

### **Step 5 — Human Review**

The team reviews:

- final patch
- tournament report
- synthesis results

Finalize manually before merging into the main codebase.

______________________________________________________________________

# **7. Isolation & Safety Model**

### **Why do we need isolation?**

Autonomous agents can:

- make destructive refactors
- accidentally delete directories
- modify system files
- run harmful shell commands
- infinite-loop if misprompted

### **Isolation strategy**

- **One container per attempt**

- **Bind-mounted worktree only**

- **Container root filesystem read-only**

- **No privileges, no capabilities**

- **Network allowed by default**, with the worktree mount remaining the only writable host surface

- **Optional timeouts + resource limits (CPU/memory)**

- Agents can only touch:

  - the mounted worktree
  - their temporary memory

This keeps them both safe and reproducible.

______________________________________________________________________

# **8. Why Worktrees Are the Perfect Mechanism**

Worktrees give us:

- separate working directories per attempt
- shared history and references
- no duplicate full repos
- easy cleanup (`git worktree prune`)
- simple diffing and retrospective analysis
- deterministic FS states across containers

Most importantly:

- **Git paths inside `.git/worktrees` remain valid when created on the host**, even when mount-bound into containers
- All edits made inside containers immediately appear on host within `.attempts` directories

______________________________________________________________________

# **9. Benefits of This Architecture**

### **Speed**

Multiple implementations generated in parallel.

### **Cost efficiency**

LLM calls use cheap **CLI subscriptions**, **local models**, or hybrid setups.

### **Control**

Everything is:

- local
- reproducible
- inspectable
- easy to iterate on

### **Quality**

The judge pipeline lets us produce:

- higher-quality code
- stylistic consistency
- deeper cross-pollination
- lower regression risk

### **Extensibility**

Supports:

- multi-agent workflows
- role-based agents
- iterative self-refinement
- human-in-the-loop augmentations

______________________________________________________________________

# **10. Open Questions for Team Discussion**

### **Prompt Design**

- How much repository context do we give each agent?
- Should the coders run tests during execution or be write-only?

### **Test Strategy**

- Should agents rely on incremental tests or only we test afterward?
- How do we ensure flaky tests don’t skew results?

### **Resource Tuning**

- How many parallel attempts is optimal (N = 3? 5? 8?)
- Container CPU/memory constraints?

### **Judging Rubrics**

- How do we weight correctness vs readability vs performance?

### **Synthesis Pass**

- Should synthesis be automatic or opt-in?
- Should synthesis output be tested again?

### **Failure Handling**

- What if an agent produces no useful diff?
- What if multiple agents produce valid but incompatible changes?

### **Human Control**

- Should human review always be required before merging?
- Should we introduce “hard mode” where AI can propose direct PRs?
