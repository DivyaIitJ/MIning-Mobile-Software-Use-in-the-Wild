# Mobile software-use dataset

Linked event, activity-segment, session, transition, and fixed-window records for research on smartphone software use.

The dataset accompanies *Mining Mobile Software Use in the Wild: A Dataset of Events, Sessions, and Activity Transitions* by Divya Prakash Pandey, Pradeep Dwivedi, and Arpit Arvind Khandelwal. Records are organized by pseudonymous participant and session identifiers. 

## Contents

| File or group | Records | Description |
|---|---:|---|
| `data/base/participants.csv` | 36 | Pseudonymous participant IDs |
| `data/base/study_days.csv` | 108 | Participant-day indices and relative offsets |
| `data/base/phone_events.csv` | 40,998 | Event timestamps and event types |
| `data/base/app_segments.csv` | 9,910 | Ordered activity-category intervals |
| `data/base/phone_sessions.csv` | 5,634 | Session start and end times |
| `data/base/context_samples.csv` | 238,764 | Released ambient-light, brightness, and motion measurements |
| `data/derived/` | Five CSV tables | Cleaned segments and sessions, 60-second windows, session transitions, and daily summaries |

The analysis includes 328.57 hours of elapsed session time, 22,931 session-bounded windows, and 5,598 consecutive-session links (5,526 within-day and 72 cross-day). The paper reports 238,764 context records in the original study snapshot; 238,764 are present in this release. 

## Reproduce the analysis

Use Python 3.11 or later.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/reproduce.py
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1` instead of `source`.

The reproduction script builds the five derived CSVs, checks table and interval consistency, regenerates the field dictionary and schema, and writes analysis metrics and figures to `results/`. Data are bundled with the repository; no Android device, network service, or credentials are required to run these analyses. The collector excerpts in `collector_reference/` are not a complete Android project.

## Example: activity transitions

```python
import pandas as pd

segments = pd.read_csv("data/derived/app_segments.csv")
sequence = segments.sort_values(["session_id", "segment_order"])
transitions = sequence.loc[sequence["is_category_change"]]
print(transitions[["participant_id", "session_id", "activity_category"]].head())
```

Join sessions and segments by `session_id`; use both `participant_id` and `study_day` for day-level joins. Field definitions and missing counts are in [`docs/data_dictionary.csv`](docs/data_dictionary.csv), with a machine-readable version in [`docs/schema.json`](docs/schema.json).

## Findings reproduced by the scripts

Of the 22,931 session-bounded 60-second windows, 3,840 (16.75%) include more than one activity category. Assigning one dominant category per window omits 60,341.97 seconds of minority-category activity (5.10% of category-covered time). There are 4,276 category changes in the interval representation, compared with 3,429 changes between adjacent, labeled dominant windows—a 19.81% net reduction in the number of changes.

The scripts also generate three figures showing session durations, category composition, and participant-day activity-change rates. See [`docs/METHODS.md`](docs/METHODS.md) for the precise interval and tie-breaking conventions.

## Data interpretation and privacy

Times are seconds relative to the midnight preceding each participant's first recorded session. This preserves within-participant time-of-day patterns without releasing calendar dates. Raw application identifiers and direct personal identifiers are not provided. Do not attempt to re-identify participants or combine the data with external personal records.

The base tables are curated input records and processing code independently reproduces derived tables from these inputs; it does not verify collector uptime or sensor calibration. Segment boundaries are clipped to their parent sessions where needed. 

## License and citation

The dataset is offered under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). The analysis scripts and tests are under the MIT License (`LICENSE`). Android source excerpts in `collector_reference/` retain their original rights and are **not** covered by the MIT software license.

Public release of participant-derived traces depends on the underlying consent and institutional permissions; these cannot be established from the exported tables alone.
