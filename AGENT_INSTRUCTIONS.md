# Portable group collaboration instructions — protocol 0.1

Give this file and `specs/` to each local coding agent. This is a portable repository instruction document, not an API integration. Follow the authoritative eight specifications in `specs/`; do not rename their prompt commands or change their event semantics. The human's commands below are prompts, NOT terminal aliases. Use `python /absolute/path/groupctl.py ...` from the target repository (Windows: `py`).

## Tool/judgment boundary
Git and groupctl establish facts. You inspect actual diffs, understand intent, resolve conflicts, review semantic compatibility, and explain evidence. Never claim semantic approval merely because Git or tests succeeded. A CLI `--semantic pass` records your performed review; it does not perform one. Likewise `--human-confirmed` records a real explicit confirmation; never supply it without one for a real group finalization. The automated demo simulates that interaction only inside its disposable repositories.

Read `.group/group.json`, assignment, member files and events first. Membership assumes a trusted group; it is not authentication. Local identity and caches in `.group/local/` are not authoritative. Events are immutable after publication. Discover remote feature-branch events, not just main. Important information must be committed/pushed. Do not broadcast private conversations or all internal thoughts.

## SYNC
1. Run `groupctl status` to record branch/commit/dirty state and fetch. Read the relevant newly discovered events, including pending reviews, questions and blockers.
2. Protect unfinished work: ask for a coherent commit/stash when needed; never reset or overwrite it. This implementation conservatively refuses dirty mutations.
3. When clean and suitable, run `groupctl sync --update`. Configured policy for v0.1 here is **merge**, never rebase/force-push. It only merges origin's configured canonical branch.
4. If a conflict occurs, inspect intent and resolve safely, then commit and run tests. Otherwise stop, preserve work and report a blocker. Do not report SYNC success while conflicted.
5. Inspect quick-check output when code changes. Explain new information, incorporated changes, changes remaining separate, and invalidated assumptions. Plain `sync` does metadata discovery without merging. It marks events seen, so inspect the returned `before.new_events` now; events remain available through `events` later.

## PUB
1. Inspect `git status`, working diff, staged diff and outgoing commit history. Identify one coherent contribution. Review for secrets/generated files; CLI scanning is only an extra heuristic.
2. Run appropriate checks, stage only intended paths and create meaningful commits. CLI publish deliberately requires a clean tree rather than automatically staging everything.
3. Run `groupctl publish --summary "..." --interface "..." --issue "..."` on your own `people/<person_id>/<topic>` branch. Repeat optional flags for lists; omit empty flags.
4. It tests an exact committed snapshot, pushes the work, then commits/pushes a uniquely identified change_published event. Report the resulting change_id. If checks/push fail, report failure precisely. Publishing is not canonical acceptance.

## INT <change_id>
1. Fetch metadata; run `groupctl inspect <change_id>`. Read its event AND actual diff and surrounding code BEFORE merging. Identify interface and assumption changes.
2. On a clean intended target branch run `groupctl integrate <change_id>`. It records a pending integration and performs a merge of the exact published commit.
3. If conflict: inspect each side and determine intended combined behavior. Edit deliberately, stage resolved files, `git commit`. Never blindly choose ours/theirs. If unclear, stop and consult human. Preserve the conflict until a deliberate resolution/abort decision.
4. To publish a blocker while the original tree is conflicted, use a separate clean worktree with a new personal topic branch based on the pre-merge commit, initialize that worktree's local identity with `join`, and publish a blocker there. Do not stage conflict markers as a workaround. After an explicitly chosen abort, finish-integration can record needs_human; incorporation will be false.
5. Inspect behavior and automated evidence. Run `groupctl finish-integration --semantic pass|fail|needs_human --summary "actual resolution and compatibility reasoning"`. This checks incorporation, markers, build/tests and publishes integration_result. No tests configured means no automatic success.
6. Explain the target branch; integrating into a personal branch does not update main. To accept into canonical, use a clean up-to-date canonical branch, deliberately merge the accepted work branch, run tests and semantic review, and push without force. No extra human shorthand command is invented.

## REV <change_id>
Use `inspect`; inspect relevant surrounding code, interfaces, regressions and missing tests. Use `test <change_id>` if practical (isolated snapshot). Separate definite defects, plausible risks and subjective preferences. Write a temporary JSON payload **outside tracked project paths** containing:
```json
{"event_type":"review","change_id":"C-...","verdict":"needs_more_evidence","summary":"Reasoned assessment","issues":[],"tests_run":[],"related_events":["E-..."]}
```
Use `groupctl event /path/review.json`. Verdicts: accept, accept_with_changes, reject, needs_more_evidence. Positive review does NOT merge code.

## TEST [scope]
`groupctl test` / `groupctl test main` / `groupctl test C-...`. CLI runs `.group/group.json` optional `checks` argv arrays in a detached disposable worktree for the exact target commit; `{python}` uses the current interpreter. It publishes output and exit codes. Counts represent check commands, explicitly labeled count_unit; do not describe them as individual unit tests.
Investigate failures: implementation, test mistake, environment, or inconclusive. Never edit expected results solely to pass. Extend tests based on independently justified requirements. Inspect configured tests for adequacy before relying on them. Human checks must be concrete steps and their outcome must be recorded honestly in a finding/review when completed. Each check command has a 300-second timeout. No checks => not_available, missing executable/timeout => partial. Nonzero check => fail. A successful CLI operation may publish a failing test_result: read its result field.

## STATUS
Run `groupctl status`, summarize identity, group, branch/commit, dirty state, ahead/behind (first number = ahead, second = behind relative to canonical), new events, published local changes, exact-commit test evidence, unresolved blockers and next action. Events list includes historical blockers; reason over related findings/answers/reviews to decide what remains unresolved. Do not merge or rewrite code.

## FINAL
Any recognized member may initiate; no unanimous vote required.
1. Synchronize metadata. Work on clean, up-to-date canonical branch. Inspect all published but unincorporated changes and all reviews/blockers/questions/tests. Determine whether pending work is intentionally rejected/obsolete or still important/unknown. Stop for important unresolved work or failures.
2. Record justified dispositions in an external JSON object keyed by change_id or concern event_id. This is an implementation extension, not a new protocol field requirement. Do not use a reason string to waive genuinely blocking work.
3. Finish concrete human checks. Run `groupctl final-prepare [--decisions /path/decisions.json] [--human-checks-done]`. It publishes final test evidence and final_candidate, writes candidate.md, and pins the tested canonical commit.
4. Improve candidate's substantive Result, Assignment, Important Changes, Validation, Known Limitations, Contributors. List actual material contributors; initial template lists registered members for review. Replace the limitations placeholder. Show the entire candidate to the initiating human and obtain explicit confirmation. Commit/push only report edits. Do not claim template generation is human review.
5. Only then run `groupctl final-confirm --human-confirmed [--limitation "..."]`. Code/config changes after testing or remote branch movement require re-preparation. It writes final_report.md, final.json and final_result, then commits/pushes.
6. Report tested canonical commit and report path. Later metadata commits are intentionally distinct from the tested source commit to avoid self-referential hashes. FINAL never submits an unpushed personal work directory.

## Errors and recovery
Never force-push, reset shared history or silently retry a failed publish as though it succeeded. On push rejection fetch/inspect and merge safely. Local commits remain available; after resolving divergence push them. A failed event push leaves the event commit locally: push that commit, do not edit its event. Pending integration state is local support only; canonical commits/events remain the durable evidence. If the machine/session changes, recover facts from Git and published events, explain any unfinished unrecorded integration, and perform fresh verification.
