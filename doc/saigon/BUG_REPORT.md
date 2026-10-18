# Sài Gòn 2000s: bug reports from playtests

One bug, one file. The lead turns each report into a unit in [PROGRESS.md](PROGRESS.md), so a report
must stand on its own: someone who was not there should be able to see the bug again from it.

## Where reports go

- Folder: [`doc/saigon/playtest/`](playtest/README.md).
- File name: `PT-xx_short-name.md`.
  - `PT-xx` is the check in [PLAYTEST.md](PLAYTEST.md) where you found the bug.
  - `short-name` is two to five words, lower case, joined with dashes. Example:
    `PT-22_flood-never-drains.md`.
  - If one check finds two bugs, add a letter: `PT-22a_…`, `PT-22b_…`.
  - A bug that fits no check uses `PT-00`.
- Add a row to the index table in [playtest/README.md](playtest/README.md).
- Attachments: run `tools/saigon/collect_bug_report.sh -w "<world>" -t PT-xx` and give the zip path it
  prints. Screenshots can also go next to the report as `PT-xx_short-name_1.png`, `_2.png`. Keep large
  saves out of git: give the path to the zip under `~/code/cdda-saigon-logs/bug_reports/` instead.

## Severity

| Level | Name | Meaning | Examples |
|---|---|---|---|
| S1 | Blocker | The game crashes, will not load, or loses or corrupts a save. Or a start or scenario cannot be played at all. | crash when the radio is used; the 2009 world will not load; a start places you inside a wall |
| S2 | Major | A feature does not work, or breaks a rule of the mod. | a vehicle cannot be driven; a mission cannot be finished; a firearm on a civilian or in a home; American items in loot; floods never drain |
| S3 | Minor | It works, but wrong or rough. | wrong numbers (prices, melt times, damage); a missing sprite; a broken description; a misplaced piece of furniture |
| S4 | Polish | Wording, spelling, tone, period detail. | a misspelled dish name; a word that is wrong for 2004 Saigon |

When unsure, pick the higher level; the lead can lower it. Frequency matters too: an S3 that happens
every time can matter more than an S2 seen once.

## Template

Copy this into the new file and fill it in. Leave nothing blank: write "n/a" or "not checked".

```markdown
# PT-xx: <one-line summary>

| Field | Value |
|---|---|
| Check | PT-xx (<check name from PLAYTEST.md>) |
| Severity | S1 / S2 / S3 / S4 |
| Frequency | always / often (more than half the tries) / sometimes / once |
| Build | <output of `git rev-parse --short HEAD`> |
| Game | tiles / terminal |
| World | <world name>; mods: dda, saigon_2000s[, saigon_playtest] |
| Scenario / start | Sài Gòn 2004 (Vietmap) or 2009 (real map) / <start location> / <profession> |
| In-game date and time | <e.g. day 6, 14:20, winter> |
| Cheats used | none / playtest remote: <options> / debug menu: <entries> |
| Reporter, date | <name>, <YYYY-MM-DD> |

## Steps to reproduce
1. <from a new game or a named save>
2. <...>
3. <...>

## Expected
<what should happen; quote the "Pass" column of the check when it applies>

## Actual
<what happened instead; copy error popups and messages word for word>

## Screenshots
- <file name, or path on disk>

## Attached files
- Bug report zip: `~/code/cdda-saigon-logs/bug_reports/<folder>.zip`
- Save archive: <yes / no: Esc > Export save archive for github bug report>
- Relevant `debug.log` lines:

    <paste the ERROR or WARNING lines, if any>

## Notes
<anything else: how often you tried, what you tried that did not show the bug, guesses>
```

## For the lead: from report to unit

1. Confirm the bug: reproduce it from the steps, or from the save.
2. Set or adjust the severity in the report and in the index table.
3. Add a ledger row in PROGRESS.md. Name the unit after the report, for example
   `F3-PT22 flood never drains`. Put the report path in the Output or Notes column.
4. Add the unit's commit to the report's index row when it is done. Set the status to **fixed**, or to
   **won't fix** (with a reason), **duplicate of PT-yy**, or **known limit** (an engine limit
   already listed in PROGRESS.md or ENGINE_PATCHES.md).
