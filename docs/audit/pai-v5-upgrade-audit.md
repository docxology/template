# PAI v5.0.0 Upgrade Audit

Date: 2026-05-15

Scope: local `~/.claude` PAI upgrade and template-repo PAI-facing documentation alignment.

## Upstream Target

- GitHub marks `danielmiessler/Personal_AI_Infrastructure` release `v5.0.0` as the latest release, titled "PAI v5.0.0 - Life Operating System".
- The release page documents the one-line installer: `curl -sSL https://ourpai.ai/install.sh | bash`.
- Preflight inspection of `https://ourpai.ai/install.sh` found `PAI_VERSION="${PAI_VERSION:-5.0.0}"`.
- The `v5.0.0` tag is present upstream. Main had commits after the release, so the target for this upgrade was the release tag, not post-release `main`.

## Local Before

- Existing `~/.claude` was a dirty git checkout on `main`, with `origin` at `https://github.com/docxology/pai.git` and `upstream` at `https://github.com/danielmiessler/Personal_AI_Infrastructure.git`.
- Pre-install HEAD was `9791ca6`.
- Local evidence matched the older PRD-era loop: Algorithm `v1.5.0`, no visible `PAI_SYSTEM_PROMPT.md`, no Pulse `31337` markers, and no Algorithm `v6.3.0`/ISA-first structure.
- Existing preflight backup path already present: `/Users/4d/.claude.backup-20260512`.

## Installer Run

- First official installer attempt stopped before modifying `~/.claude` because `bun` was not on `PATH`.
- Second attempt ran with `/Users/4d/.bun/bin` on `PATH` and completed through the official installer wizard.
- The installer moved the prior install to `/Users/4d/.claude.backup-20260515-105316`.
- The installer also created `/Users/4d/.claude.backup-2026-05-15T18-21-36-469Z` during its bundled migration flow.
- Three timestamped backups remained available after cutover: `/Users/4d/.claude.backup-20260512`, `/Users/4d/.claude.backup-20260515-105316`, and `/Users/4d/.claude.backup-2026-05-15T18-21-36-469Z`.
- Installer identity setup selected principal `Daniel`, DA name `PAI`, project directory `~/Documents/GitHub`, Pulse install enabled, and macOS notification fallback for voice because no ElevenLabs API key was configured.

## Migration

- No old hooks or skills were overlaid into v5.
- Durable TELOS files missing from the v5 tree were restored additively from `/Users/4d/.claude.backup-20260515-105316/PAI/USER/TELOS/` into `/Users/4d/.claude/PAI/USER/TELOS/` with `--ignore-existing`.
- Existing v5 identity files such as `PAI/USER/PRINCIPAL_IDENTITY.md` and `PAI/USER/DA_IDENTITY.md` were preserved.
- The old backup did not contain a `MEMORY/KNOWLEDGE` directory, so broad old MEMORY history remains in the backup for explicit future migration rather than being copied into the new v5 layout.

## Post-install Verification

- `~/.claude/PAI/PAI_SYSTEM_PROMPT.md` exists.
- `~/.claude/PAI/ALGORITHM/v6.3.0.md` exists.
- `~/.claude/skills/ISA/SKILL.md` exists and contains Ideal State Artifact doctrine.
- `rg "v6\\.3\\.0|Ideal State Artifact|Pulse|31337" ~/.claude/PAI ~/.claude/skills` returns v5 markers.
- Pulse health succeeds at `http://127.0.0.1:31337/api/pulse/health`.
- Pulse notify succeeds with `POST http://127.0.0.1:31337/notify`.
- The Life Dashboard serves HTML from `http://127.0.0.1:31337/` after setting `dashboard_dir` to `/Users/4d/.claude/PAI/PULSE/Observability/out`.

## Local Pulse Notes

- To get a stable daemon after the first launch, optional modules that were not needed for validation stayed disabled: Telegram, performance, syslog, DA assistant jobs.
- Observability is enabled for the dashboard.
- Voice is enabled with desktop notifications; ElevenLabs API use is not configured.
- `subsystems.cron.jobs` originally showed a prior `assistant-tasks` error result. After adding and manually validating the assistant scaffold, that historical state row was cleared while DA assistant jobs remained disabled.
- Post-review hardening added a zero-AI-cost `pulse-self-audit` job at 06:00 daily. It records the latest local readiness report at `/Users/4d/.claude/PAI/MEMORY/PAISYSTEMUPDATES/pulse-self-audit.json` and blocks staged re-enablement when configured job targets are missing.
- Pulse process management now runs the same self-audit before `start` and `install`, so critical readiness failures prevent daemon launch instead of becoming delayed cron failures.
- The Life Dashboard now exposes a `Ready` route at `http://127.0.0.1:31337/readiness`, backed by `GET /api/pulse/self-audit`.
- A conservative `PULSE/Assistant/` scaffold now provides backing files for Phase 1 assistant jobs without enabling them automatically.
- The local Codex skill mirror at `/Users/4d/.agents/skills/PAI/SKILL.md` now starts with an active PAI v5 runtime override so future Codex sessions do not treat the legacy Algorithm `v1.5.0` material as current doctrine.
- Deep review found `~/.claude/settings.json` still reporting Algorithm `6.2.0` while `PAI/ALGORITHM/LATEST` reported `6.3.0`; settings now reports `6.3.0`, and the self-audit checks this pointer alignment.
- The self-audit also checks that the three timestamped rollback backups remain present.
- The readiness report now groups findings by rollout phase. Current status is baseline ready, doctrine ready, runtime ready, Phase 1 assistant ready, Phase 2 monitors attention, and Phase 3 communications ready.
- `PULSE/Assistant/checks/growth.ts` now writes phase-aware next actions to `/Users/4d/.claude/PAI/MEMORY/PAISYSTEMUPDATES/assistant-growth-readiness.md`.

## Template Alignment

- PAI-facing template docs now use Life OS, DA, Pulse, Algorithm `v6.3.0`, and ISA-first terminology.
- PRD-era loop language is documented as historical only.
- No template Python public API changed.
