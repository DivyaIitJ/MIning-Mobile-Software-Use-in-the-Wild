# Data processing methods

## Record representation

The six base CSVs contain participant and study-day records, session bounds, activity intervals, timestamped events, and device-context samples. Relative timestamps use seconds from the midnight preceding each participant's first recorded session. This removes calendar dates while preserving time-of-day and within-participant order. Supplied participant-day labels are retained even where they cross a midnight boundary.

## Deriving analytical views

1. Validate unique identifiers, parent references, known categories, positive time intervals, and absence of overlapping sessions or source segments. The program stops on structural violations.
2. Intersect each source activity interval with its parent session. Store the original bounds and a boundary-adjustment flag; recalculate clipped duration and within-session category changes.
3. Calculate session duration, order, preceding gap, category composition, number of category changes, and recent recorded use over 30-minute, 1-hour, 2-hour, and 6-hour horizons.
4. Divide each session into consecutive half-open 60-second windows, retaining any shorter final window. Assign the category with the largest total overlap; break exact ties alphabetically. Leave windows without category coverage `UNLABELLED`.
5. Summarize context values within each window using nonmissing arithmetic means. These means are not time-weighted integrals, interpolated data, or sensor calibration checks.
6. Link consecutive sessions by participant, marking transitions across study-day labels. Aggregate recorded session duration, activity composition, and category changes at participant-day level.

The 60-second windows are bounded by sessions, not aligned to wall-clock minutes. Trailing-history variables describe *recorded sessions*; missing prior observation time is not known inactivity. Use only information available at the intended prediction timestamp to avoid leakage.

## Aggregation analysis

For each window, the minority-category duration is category-covered time minus the duration of the dominant category. Its reported percentage divides the minority time summed across windows by the total category-covered time, not by all elapsed session time. A category change in the window view is counted between consecutive windows in the same session only if both have a defined dominant label. The reduction in counts is a representation-level comparison, not event-level recall.

Source-order tie-breaking would produce a slightly different dominant-window change count. The accompanying results consistently use alphabetical tie-breaking.

