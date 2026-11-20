# Lint, type-check, boundary and hook tooling (Nov 2026)

Research date: 2026-11-20. Context: a personal TypeScript project on Node 24, with no build step (`.ts` runs through Node type stripping), using pnpm and mise. Plans: many project-specific custom lint rules, TypeScript 7 for type checking, deep-module boundaries enforced with dependency-cruiser, and a hard 3 s pre-commit budget.

Legend: **[source]** = stated by a primary source (linked). **[measured]** = I ran it today (see "Benchmark setup"). **[opinion]** = my judgement. Facts are kept out of the Recommendation section, and vice versa.

## Versions as of 2026-11-20

From the npm registry `dist-tags.latest` and publish times, plus GitHub releases **[source]**:

| Tool | Latest | Published |
|---|---|---|
| `typescript` (Go-based "TS 7") | 7.0.2 (`beta`: 7.1.0-beta, 2026-10-20; `next`: 7.1.0-dev nightlies) | 2026-07-08 |
| `@typescript/typescript6` (TS 6 API + `tsc6` binary) | 6.0.2 | 2026-07-06 |
| `eslint` | 10.15.0 (v9 is EOL since 2026-08-06) | 2026-11-13 |
| `typescript-eslint` | 8.73.0 | 2026-11-16 |
| `oxlint` | 1.94.0 | 2026-11-16 |
| `oxlint-tsgolint` | 7.0.2007 | 2026-11-12 |
| `tsrs` (Rust port of the TS 7 checker, alternative oxlint backend) | 7.1.0-beta.tsrs3 | 2026-11-18 |
| `@biomejs/biome` | 2.6.8 | 2026-11-15 |
| `dependency-cruiser` | 18.8.0 | 2026-11-16 |
| `eslint-plugin-boundaries` | 7.4.4 | 2026-11-15 |
| `hk` | v2.13.0 | 2026-11-16 |
| `lefthook` | 2.2.2 | 2026-10-13 |
| `mise` | v2026.11.11 | 2026-11-20 |

---

## 1. Custom lint rules

### ESLint 10 + typescript-eslint 8.73

- **Language and API:** JS or TS modules exporting `{ meta, create(context) }`, with an ESTree AST, selectors, scope manager, code-path analysis and token APIs. Typed rules use `ESLintUtils.RuleCreator` from `@typescript-eslint/utils`. **[source]** https://eslint.org/docs/latest/extend/custom-rules, https://typescript-eslint.io/developers/custom-rules
- **Type information:** Full access. `ESLintUtils.getParserServices(context)` exposes `getTypeAtLocation(node)` and `getSymbolAtLocation(node)`, and `services.program.getTypeChecker()` exposes the whole TS checker API. **[source]** typescript-eslint custom-rules page.
- **Maturity:** The most mature and stable API. It has been the de facto standard for about 10 years, and ESLint 10.0.0 shipped 2026-02 (https://eslint.org/blog/2026/02/eslint-v10.0.0-released/). **[source]**
- **Autofix:** `fix` and `suggest` in `context.report`. **[source]**
- **Testing:** `RuleTester` from `eslint`, and for typed rules `RuleTester` from `@typescript-eslint/rule-tester`, which needs `parserOptions.projectService.allowDefaultProject` and `tsconfigRootDir`. **[source]** typescript-eslint custom-rules page.
- **No build step:** A local plugin written in `.ts` and imported from `eslint.config.js` loads and works on Node 24.10 through Node's type stripping. **[measured]** A `.ts` *config* file still needs `jiti`, or the `unstable_native_nodejs_ts_config` flag (https://eslint.org/docs/latest/use/configure/configuration-files#typescript-configuration-files). **[source]**
- **Performance of custom rules:** Cheap compared with typed parsing. 30 custom rules added about 0 ms on top of a typed run at both 40 and 400 files. An untyped run with 30 rules took 463 ms (40 files) and 1195 ms (400 files). **[measured]**

### oxlint 1.94 (JS plugins)

- **Language and API:** An ESLint-compatible plugin API ("compatible with ESLint v9+", "nearly all" of it implemented). Rules are written in JS or TS. Supported: selectors, fixes, suggestions, the SourceCode and token APIs, scope analysis and code paths. The optional `createOnce` plus `before`/`after` hooks API comes through `eslintCompatPlugin` in `@oxlint/plugins`, so one plugin can run under both oxlint and ESLint. **[source]** https://oxc.rs/docs/guide/usage/linter/js-plugins.html, https://oxc.rs/docs/guide/usage/linter/writing-js-plugins.html
- **Type information: not available to JS plugins.** The docs list "Lint rules that depend on TypeScript type information" as unsupported. Issue [oxc-project/oxc#19596](https://github.com/oxc-project/oxc/issues/19596) ("make type information available to custom JS plugins") is still open. On 2026-03-04 a maintainer wrote that it's "pretty hard… tsgo currently doesn't expose type info in a way that it could be consumed by JS plugins. And even if it did, it'd be hard to make it work without tanking perf due to all the boundary-crossing between Go and JS". On 2026-06-12 the answer to "any update?" was "Not at this time". `sourceCode.parserServices` is `{}` ([#19962](https://github.com/oxc-project/oxc/issues/19962), open). **[source]** The only type-aware rules are the built-in ports of typescript-eslint rules (60 of 62 per the docs). Custom type-aware rules today mean a userland shim that builds your own `ts.Program` (described in #19596, 2026-11-19), which brings back the TS 6 JS API. **[source]**
- **Maturity:** **alpha**. "JS plugins are currently in alpha, and remain under active development". The alpha was announced 2026-03-11 (https://oxc.rs/blog/2026-03-11-oxlint-js-plugins-alpha). Conformance: 100% of ESLint's built-in rule tests (33,006) pass. **[source]**
- **Autofix:** Fixes and suggestions are supported. **[source]**
- **Testing:** `RuleTester` from `oxlint/plugins-dev`. You plug in your own `describe`/`it`, and the docs example uses Vitest. **[source]**
- **No build step:** A `.ts` plugin file listed in `jsPlugins` loads on Node 24.10. **[measured]**
- **Performance and FFI:** oxlint uses "raw transfer" to pass the AST from Rust to JS. The blog says it "reduces the cost of moving data between Rust and JS almost to zero", but only a "first iteration" has shipped. `createOnce` "isn't [faster] yet… *will be soon*". Published numbers: on the Node.js repo, ESLint took 1m43s and oxlint 21s (4.8x), with 75 JS-plugin rules plus 23 custom JS rules. **[source]** My measurements: 30 JS-plugin rules added **~130 ms at 40 files and ~165 ms at 400 files** over plain oxlint (67→194 ms, 70→236 ms). Most of that is fixed JS-runtime startup, not per-file cost. **[measured]**

### Biome 2.6.8 (GritQL and JS plugins)

- **GritQL plugins:** A pattern DSL in `.grit` files. Rewrites (`=>`) can act as code fixes with `fix_kind = "safe" | "unsafe"` (code fixes landed in v2.5, 2026-06-05). GritQL plugins "don't have access to information such as the semantic model, file kind, etc." and "run on every file". **[source]** https://biomejs.dev/linter/plugins/
- **JS plugins (new in v2.6, 2026-10-15):** **Developer Preview**, meaning "Breaking changes can happen in patch releases, and some features are missing". Rules use `defineRule({ query: ast("JS_CALL_EXPRESSION") | grit("`…`"), run(node, ctx) })` with `registerDiagnostic(node, severity, message)` from `@biomejs/runtime/plugin`. They run in Boa, an embedded JS engine written in Rust, not Node. They work on Biome's CST, not ESTree. `ctx.model` is the semantic model (bindings, scopes) when `{ semantic: true }` is set. Variables captured by a `grit()` query aren't passed to `run` yet. **[source]** https://biomejs.dev/blog/biome-v2-6/, plugins page.
- **Type information:** Not exposed to plugins. The v2.6 post says Biome "intentionally decided to expose a subset of services". It describes type inference and the module graph only as potential future additions. **[source]**
- **Autofix in JS plugins:** Not documented. GritQL plugins have it. **[source]**
- **Testing:** Neither plugin form documents a rule-testing harness. **[source]** (absence noted on the plugins page)
- **Performance:** I measured 30 rules each way. GritQL: +22 ms at 40 files and +218 ms at 400 files (87→109 ms, 128→346 ms). JS plugins: +113 ms at 40 files and +248 ms at 400 files. **[measured]** In other words, GritQL's per-file cost grows with the file count ("run on every file").
- **Ecosystem:** ESLint plugins don't run in Biome.

### Other options looked at

- **rslint** (`@rslint/core` 0.10.1, 2026-11-10): Built on typescript-go and forked from tsgolint. Its README claims custom rules can access "AST, type information, and global checker data", and pkg.go.dev describes it as "in an experimental phase". **[source]** https://github.com/web-infra-dev/rslint I didn't test it, and I didn't confirm what language its custom rules are written in.
- **tsl** 1.0.30: Type-aware rules in TS on top of tsc. Its peer range is `typescript ~5.8 || ~5.9 || ~6.0`, so it doesn't support TS 7. **[source]** (npm metadata)
- **Deno lint, TSSLint:** Not pursued, since they don't fit a pnpm/Node project as well. **[opinion]**

---

## 2. TypeScript 7 (typescript-go)

### Release status **[source]**

- **TS 7.0 stable on 2026-07-08** (https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/). `npm i -D typescript` gives a native `tsc`. There is no separate `tsgo` binary in the stable release; `@typescript/native-preview` was the preview channel.
- "While TypeScript 7.0 is here, **it does not ship with an API.** We expect TypeScript 7.1 to ship with a new (and different) API." To run TS 6 alongside, the blog recommends `@typescript/typescript6` (a `tsc6` binary plus the TS 6 API), using npm aliases: `"typescript": "npm:@typescript/typescript6@^6.0.2"` and `"@typescript/native": "npm:typescript@^7.0.2"`.
- **TS 7.1 beta on 2026-10-20** (https://devblogs.microsoft.com/typescript/announcing-typescript-7-1-beta/). It adds the API as `typescript/sync`, `typescript/async`, `typescript/fs` and `typescript/ast`. The plan was an RC "in about a month" and then a final release "shortly thereafter", so 7.1 stable is roughly due now (late November or December 2026) but not yet published.
- typescript-go's README feature table marks watch mode, build mode/project references and **incremental build** as "done", and **API** as "not ready". **[source]** https://github.com/microsoft/typescript-go

### Linter coexistence with a TS 7 project

| | Works with a project on TS 7? | How type-aware rules get types | `no-floating-promises` |
|---|---|---|---|
| **ESLint + typescript-eslint 8.73** | Yes, if TS 6 is installed alongside. `typescript-eslint` peer range is `typescript >=4.8.4 <6.1.0`. **[source]** (npm) Installing only TS 7.0 makes typescript-estree crash (`Cannot read properties of undefined (reading 'Cjs')`) ([#12518](https://github.com/typescript-eslint/typescript-eslint/issues/12518), closed as a duplicate of [#10940](https://github.com/typescript-eslint/typescript-eslint/issues/10940)). **[source]** | Default: the TS 6 JS API in-process. **New in 8.73.0 (2026-11-16):** an opt-in `parserOptions.projectService.EXPERIMENTAL_backend: 'tsgo'` that talks to TS 7.1 over IPC, with optional peer `@typescript/native: >=7.1.0-beta` ([#12803](https://github.com/typescript-eslint/typescript-eslint/pull/12803), merged 2026-11-10). The PR's own benchmark: native is 0.86x to 1.72x the *time* of classic. It is about equal for `no-floating-promises` alone and up to 1.7x slower for `recommendedTypeChecked` on large file counts, because "Each native API call is a synchronous round trip to the separate `tsgo` process". The PR says this will improve once TS 7.1 has bulk APIs. **[source]** | Yes. Caught 42/42 of my planted cases on both backends. **[measured]** |
| **oxlint + tsgolint 7.0.2007** | Yes. tsgolint "is built directly on TypeScript v7" and "tracks TypeScript v7.0.2". Type-aware linting was declared **stable on 2026-07-22**. You don't install TypeScript separately, but the tsconfig must be TS 7-valid (no `baseUrl` and no options removed in 7.0). **[source]** https://oxc.rs/blog/2026-07-22-type-aware-linting-stable, https://oxc.rs/docs/guide/usage/linter/type-aware.html | Go binary built on typescript-go; it doesn't use your installed `typescript`. `--type-check` / `options.typeCheck` also reports TS diagnostics from the same program, **but only for the files oxlint lints**. The docs tell you to run `tsc --noEmit` for whole-project checks. **[source]** | Yes. Caught 42/42. **[measured]** |
| **oxlint + tsrs 7.1.0-beta.tsrs3** | Yes. A Rust port of the TS 7.1 checker, auto-used when installed. Announced 2026-11-17: "up to 5×" faster than tsgolint with about 70% less memory, and implements all 61 tsgolint rules. Still pre-stable ("help… reach a more stable release"; the version is a 7.1 *beta*). **[source]** https://oxc.rs/blog/2026-11-17-faster-type-aware-linting-with-tsrs, https://github.com/oxc-project/tsrs | Own Rust checker. | Yes. Caught 42/42. **[measured]** |
| **Biome 2.6.8** | Yes, fully independent of `typescript`, since Biome has its own type inference engine in Rust. **[source]** https://biomejs.dev/linter/rules/no-floating-promises/ | Biome's own inference (the `types` domain plus the project scanner). | **Nursery** rule since v2.0.0 ("can change at any time"). **[source]** Caught 41/42 of my cases. It **missed a call through an indexed `Record<string, () => Promise<void>>`** (`rec['x']!()`). **[measured]** |

### `no-floating-promises` reliability test **[measured]**

I planted 32 simple cases across 40 files (direct method call; `.then` without a rejection handler; an array of promises from `.map(async…)`; a call through a local arrow). I added 10 harder cases in one file: an interface method, a type-alias function, `Promise|undefined`, a generic identity wrapper, a `typeof` alias, an indexed record, `Promise.race`, an async IIFE, `.finally`, and a bare identifier. A custom thenable is not flagged by any of the tools, which matches typescript-eslint's default `checkThenables: false`.

- typescript-eslint (TS 6 classic backend), typescript-eslint (`EXPERIMENTAL_backend: 'tsgo'` on TS 7.1-beta), oxlint+tsgolint, and oxlint+tsrs: **42/42**, no false positives on `void x` / `await Promise.all` / `.catch`.
- Biome: **41/42** (missed the indexed-record call). No false positives.

---

## 3. Pre-commit speed (3 s budget)

### Published data **[source]**

- **TS 7 vs 6, full builds:** vscode 125.7 s→10.6 s (11.9x), sentry 139.8→15.7 s, bluesky 24.3→2.8 s, playwright 12.8→1.47 s, tldraw 11.2→1.46 s (TS 7.0 blog). 7.1-beta is a further 1.2 to 1.9x faster than 7.0 on `--noEmit` (7.1 beta blog).
- **tsgolint vs ESLint + typescript-eslint:** 12 to 18x faster (vscode 83.2→6.96 s; typeorm 13.2→0.75 s) (stable blog, M4 Pro).
- **tsrs vs tsgolint:** "up to 5×"; vs typescript-eslint "up to 98×" (tsrs blog; no absolute numbers in the text).

### Benchmark setup **[measured]**

The machine is an Intel Core Ultra 7 155U (14 threads, laptop) on Linux. The synthetic project has an import chain (`modN` imports `modN-1`) with async functions, generic classes and the planted floating promises, at 40 files and at 400 files. Each figure is the median of 5 runs after 1 warm-up, measured as wall time from process start. Most runs used Node 26.13; I spot-checked on Node 24.10 and got the same results within noise. The rule set was `no-floating-promises` only ("nfp").

| Command | 40 files | 400 files | 2 files of 400 (staged) |
|---|---|---|---|
| `tsc` 7.0.2 `--noEmit` | **106 ms** | **206 ms** | n/a (see below) |
| `tsc6` 6.0 `--noEmit` | 505 ms | 1115 ms | |
| `tsc` 7 `--incremental`, warm, no change | 94 ms | ~130 ms | |
| `tsc` 7 `--incremental` after a 1-file edit | | 130 to 200 ms | |
| oxlint (no type-aware, default rules) | 67 ms | 70 ms | |
| oxlint `--type-aware` (tsgolint) | 166 ms | 259 ms | |
| oxlint `--type-aware` + 30 custom JS rules | 246 ms | 355 ms | 252 ms |
| oxlint `--type-aware --type-check` + 30 JS rules | | | 239 ms |
| oxlint `--type-aware` (tsrs) | 145 ms | | |
| oxlint `--type-aware --type-check` (tsrs) | 147 ms | | |
| `tsrs --noEmit` | 81 ms | | |
| ESLint + typescript-eslint typed (TS 6 backend) | 915 ms | 2306 ms | |
| same + 30 custom rules | 913 ms | 2313 ms | 839 ms |
| ESLint + typescript-eslint, `EXPERIMENTAL_backend: 'tsgo'` (TS 7.1-beta) | 825 ms (41 files) | | 502 ms (2 of 41) |
| ESLint, 30 custom rules, untyped | 463 ms | 1195 ms | |
| Biome lint (nfp, types domain) | 87 ms | 128 ms | 105 ms |
| Biome + 30 GritQL plugins | 109 ms | 346 ms | |
| Biome + 30 JS plugins | 200 ms | 376 ms | |
| dependency-cruiser 18.8 (3 boundary rules; TS 6 API) | 387 ms | 546 ms | |
| dependency-cruiser (TS 7.1-beta native API) | 275 ms | 512 ms | |
| dependency-cruiser `--cache`, warm | | 331 ms | |
| dependency-cruiser `--affected HEAD` (1 staged file) | | 570 ms | |

Observations **[measured]**:

- Typed linting on a few staged files costs about the same as on the whole project at this scale. For every tool, building the program dominates. With ESLint, 2 staged files cost 839 ms versus 2313 ms for all 400.
- Every combination of `tsc` 7 plus any linter plus dependency-cruiser fits easily inside 3 s at 400 files. The slowest realistic stack is ESLint typed on staged files (~0.85 s) + `tsc` 7 (~0.2 s) + depcruise (~0.55 s), run serially ≈ 1.6 s. With oxlint or Biome the lint step drops to ~0.1 to 0.35 s.

### Can a type check be limited to staged files? **No (confirmed)**

- `tsc` with file arguments ignores `tsconfig.json`. TS 7 actually errors (`TS5112: tsconfig.json is present but will not be loaded if files are specified on commandline`) unless you pass `--ignoreConfig`, and then all your compiler options have to be repeated on the command line. **[measured]**
- Even then it type-checks the whole **import closure**. `tsc --listFilesOnly src/mod399.ts` lists all 400 files in my chain. It also **misses errors in files that import the changed file** (dependents), which is the usual way a change breaks things. **[measured]**
- oxlint's `--type-check` on staged files has the same blind spot: it reports diagnostics "only for files Oxlint lints". **[source]**
- The meaningful cheap option is `tsc --incremental` (or `-b`) over the whole project, which TS 7 supports. **[source]** At this project's size, a full `tsc` 7 run (~0.1 to 0.2 s) is already cheap enough that incremental mode barely matters. **[measured]**

---

## 4. Hook runner

| | hk v2.13.0 (jdx) | lefthook 2.2.2 | `mise generate git-pre-commit` |
|---|---|---|---|
| Config | Pkl (`hk.pkl`), typed. **[source]** https://hk.jdx.dev/ | YAML / TOML / JSON(C). **[source]** https://lefthook.dev/configuration/ | A mise task (default `pre-commit`). **[source]** https://mise.jdx.dev/cli/generate/git-pre-commit.html |
| Staged files | Per-step `glob` and `{{files}}`; "Unstaged work is stashed, so linters see only what you staged". **[source]** | `{staged_files}` / `glob`; hides unstaged changes in pre-commit since [#402](https://github.com/evilmartians/lefthook/pull/402), with restore fixes in [#1416](https://github.com/evilmartians/lefthook/pull/1416)/[#1417](https://github.com/evilmartians/lefthook/pull/1417). **[source]** (CHANGELOG) | Staged names are passed in the `STAGED` env var. The page doesn't mention stashing. **[source]** |
| Parallelism | Runs independent steps in parallel by default, with read/write file locks ("Checks can read a file concurrently; fixes wait for exclusive access"). **[source]** | Sequential by default; `parallel: true` opts in. **[source]** (docs/configuration/parallel.md) | Whatever the mise task does (mise can run task deps in parallel); no hook-specific features. |
| Fix and re-stage | `check` and `fix` modes per step; `hk fix`. **[source]** | `stage_fixed: true` re-adds fixed files. **[source]** | Do it yourself. |
| Builtins | Has builtins for `biome`, `ox_lint`, `eslint`, `tsc`, `knip`, `vp_lint` and others. The `tsc` builtin runs `tsc --noEmit -p {{workspace_indicator}}`, i.e. the whole project. **[source]** (jdx/hk `pkl/builtins/`) | None, write your own commands. | None. |
| Caching | v2.13.0 (2026-11-16) adds opt-in `cache = true`, which skips checks that passed on identical inputs, with `cache_inputs` for whole-project checks. **[source]** | No | No |
| Speed claim | 6,159 files, 10 fixers: hk 3.22 s vs lefthook 5.04 s (vendor benchmark). **[source]** | | |
| mise | `mise use hk`; mise's own page points users who want a full hook manager to hk. **[source]** | Installable via mise. **[source]** | Built in. |

---

## 5. dependency-cruiser and module boundaries

The target rules are: other packages import `src/packages/<name>/` only through root files; subfolders are private; tests in `<pkg>/tests/` import only entry points; no cycles.

### How it parses TypeScript **[source: code in dependency-cruiser 18.8.0, `src/extract/`, `src/utl/typescript-facade.mjs`]**

- Dependencies: acorn (JS) plus optional transpilers. For `.ts` it uses **the `typescript` package you have installed**, through `createSourceFile`/`transpileModule`. It can use `@swc/core` instead (`parser: "swc"`). There is no peer dependency; it `tryImport`s `typescript` within the range `>=2.0.0 <7.0.0 || >=7.1.0 <8.0.0`.
- **TS 7.1 native support landed in 18.8.0 (2026-11-16)**: "adds support for typescript >=7.1 (the native compiler)… currently works with the typescript 7.1 beta" (release notes; issue [sverweij/dependency-cruiser#1112](https://github.com/sverweij/dependency-cruiser/issues/1112)). It uses a facade that drives `typescript/sync` and `typescript/ast` (a separate compiler process). **TS 7.0 is explicitly unsupported** ("its API lacks what dependency-cruiser needs").

### Behaviour by installed `typescript` **[measured]**, using a fixture with 3 planted violations (deep import, a test importing `internal/`, a cycle)

| `typescript` resolves to | Result |
|---|---|
| 6.0 (via the `@typescript/typescript6` alias) | 3 violations found, exit 3 |
| **7.0.2** | **"✔ no dependency violations found (0 modules, 0 dependencies cruised)", exit 0.** With `options.tsConfig` set, it prints a `missing-tsc-transpiler` warning; without it, nothing at all. **It silently passes.** |
| 7.1.0-beta | 3 violations found, exit 3 |

So with TS 7.0 you need either the TS 6 alias (the TS 7.0 blog's own side-by-side setup) or 7.1-beta/stable. `@swc/core` is the other route.

### Runtime and staged-only

- At 40 files it takes ~0.28 to 0.39 s and at 400 files ~0.51 to 0.55 s (table above). `--cache` (warm) takes 0.33 s at 400 files. **[measured]**
- `--affected [revision]` means "only include modules changed since the revision + all modules that can reach them". **[source]** (CLI help) It narrows the *report*, not the work: 570 ms with 1 changed file versus 546 ms full, at 400 files. **[measured]** Running on the full tree every commit already fits the budget at this scale.

### Can the linters express the same rules natively?

| Rule | Biome 2.6.8 | oxlint 1.94 | ESLint 10 |
|---|---|---|---|
| No cycles | `noImportCycles` (suspicious, since 2.0.0, `project` domain). Caught the planted cycle, even when linting only the one file. **[measured]** | Native `import/no-cycle`. Caught it, including in single-file runs. **[measured]** | `import-x/no-cycle` (known to be slow; not measured). |
| Only through root files / subfolders private / tests only through entry points | `noRestrictedImports` matches the **import specifier as written, not the resolved path**: a `src/packages/*/internal/**` pattern did not fire, while a `../*/internal/*` pattern did. **[measured]** Expressing the rule therefore depends on relative-path depth (per-folder `overrides`). `noPrivateImports` uses JSDoc `@package`/`@private` visibility per export, which is a different model. **[source]** (`biome explain`) GritQL plugins have no resolver or module graph. | No native `no-restricted-paths`. **But `eslint-plugin-boundaries` 7.4.4 runs as an oxlint `jsPlugin`** with the same `settings`, and caught both boundary violations in my fixture. Combined with native `import/no-cycle`, it covers all four rules. 400 files: 616 ms full, 571 ms for 2 files. **[measured]** | `eslint-plugin-boundaries` (`boundaries/dependencies`, `entry-point`, `no-private`) caught both. `import-x/no-restricted-paths` is an alternative. **[measured]** / **[source]** |

Notes: the v7 plugin warns that `entry-point` and the `mode`/`rules` options I used are deprecated in favour of `boundaries/dependencies` with `policies`, but they still work. The element setup I used: `pkg-tests` = `src/packages/*/tests`, `pkg` = `src/packages/*`, and `entry-point` allows `*.ts` (root files only). Linter-based boundary checks run per file, so they work on staged files. They don't need the `typescript` package beyond the parser.

---

## Recommendation [opinion]

1. **Type check with `tsc` 7.** It is 5x faster than TS 6 here, and the whole project at 400 files takes about 0.2 s. Don't try to limit the type check to staged files. Run `tsc` on the whole project every commit; add `--incremental` once it grows.
2. **Linter: it depends on whether your custom rules need types.**
   - If many of your custom rules need **type information**, the only mature route is **ESLint 10 + typescript-eslint**. Use the TS 6 alias alongside TS 7 now (`typescript` → `@typescript/typescript6`, `@typescript/native` → TS 7). Move to `EXPERIMENTAL_backend: 'tsgo'` once TS 7.1 is stable and the backend loses the `EXPERIMENTAL_` prefix. At your scale it costs about 0.85 s per commit on staged files, inside budget. oxlint and Biome can't run custom type-aware rules today, and neither has a public timeline for it.
   - If custom rules are **syntactic or scope-based**, use **oxlint** with `--type-aware` for the built-in `no-floating-promises` and friends. It runs ESLint-API JS plugins, which can later move to ESLint unchanged through `eslintCompatPlugin`, has a real `RuleTester`, and supports fixes, at about 0.25 to 0.35 s. Start on tsgolint (stable) and try tsrs once it leaves 7.1 beta. JS plugins being alpha is the main risk, but the API is ESLint's, so the fallback is cheap.
   - Biome is the fastest and its GritQL is nice for simple pattern bans. But JS plugins are in Developer Preview (breaking changes in patch releases), there is no rule-testing harness, rules aren't portable, `noFloatingPromises` is nursery and missed 1 of 42 cases, and there's no type access. It's a poorer fit for "MANY custom rules".
   - A hybrid works within budget: oxlint for most rules, plus a small ESLint config only for the few type-aware custom rules, running in parallel.
3. **Boundaries:** On oxlint or ESLint, `eslint-plugin-boundaries` + `no-cycle` cover all four rules inside the linter, so dependency-cruiser becomes optional. Keep depcruise if you want its richer graph rules and reports. In that case **pin TS 6 or use TS ≥ 7.1 for it, and set `options.tsConfig`, because on TS 7.0 it passes silently.** A cheap guard is a CI or pre-commit check that depcruise reports a module count greater than 0.
4. **Hook runner: hk.** It runs steps in parallel by default, stashes unstaged changes, has builtins for oxlint/eslint/biome/tsc, offers opt-in caching as of v2.13, and is a jdx tool. Lefthook is a fine alternative. `mise generate git-pre-commit` is just a task launcher, and mise's own docs point to hk.

## Unresolved / not verified

- The rslint custom-rule API (language, stability) was not checked.
- The tsrs blog's absolute benchmark numbers are only in charts; I quoted the text figures.
- Hook-runner overhead was not measured locally (neither hk nor lefthook is installed here).
- typescript-eslint's `EXPERIMENTAL_backend` performance on large typed rule sets is reported by the PR (up to 1.7x slower), not by me; at 41 files it was faster than classic.
