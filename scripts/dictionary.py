"""Generate the complete field dictionary and machine-readable schema from curated tables."""
import json
import pandas as pd

def meaning(c):
 exact={
 'participant_id':('identifier','Pseudonymous source participant identifier; stable across all tables.'),
 'study_day':('index','Supplied observation-day index; preserved, not inferred from midnight.'),
 'day_offset':('days','Source observation date minus the participant-specific first-session midnight; original date removed.'),
 'age':('years','Age supplied by the study owner; not inferred from device classes.'),
 'age_group':('category','Supplied age band; descriptive participant metadata.'),
 'session_id':('identifier','Stable supplied session identifier; not reconstructed from event rows in this release.'),
 'segment_id':('identifier','Stable supplied category interval identifier.'),
 'event_id':('identifier','Deterministic source-row index assigned during import; not an original Android event ID.'),
 'context_id':('identifier','Deterministic source-row index assigned during import.'),
 'event_type':('category','Supplied event type; may include canonical export events not produced directly by the reference collector.'),
 'activity_category':('category','One of the 12 documented software-activity categories.'),
 'screen_state':('category','Supplied screen-state label; not independent evidence of active attention.'),
 'lock_state':('category','Supplied lock-state label; not used to reconstruct sessions in this package.'),
 'ambient_light_lux':('source-declared lux','Supplied context light value; physical calibration not independently verified.'),
 'screen_brightness':('source scale unspecified','Supplied numeric brightness; not interpreted as percent or converted to Android 0–255 scale.'),
 'accelerometer_magnitude':('source scale unspecified','Supplied acceleration magnitude; reference collector computes Euclidean norm of three axes.'),
 'gyroscope_magnitude':('source scale unspecified','Supplied angular-velocity magnitude; reference collector computes Euclidean norm of three axes.'),
 'segment_order':('index','One-based within-session interval order; recomputed in cleaned data.'),
 'boundary_adjusted':('boolean','Interval start or end changed by clipping to its parent session.'),
 'is_category_change':('boolean','True for a noninitial segment whose category differs from the preceding segment in the same session.'),
 'session_order_today':('index','One-based chronological session order within supplied participant/study-day group.'),
 'previous_session_id':('identifier','Previous recorded session for the same participant; missing for first session.'),
 'previous_study_day':('index','Study day of previous recorded session; missing for first session.'),
 'cross_day_before':('boolean','Previous recorded session exists and has a different study-day label.'),
 'number_segments':('count','Number of linked cleaned segments.'),
 'number_category_changes':('count','Actual within-session category changes; not assumed equal to segment count minus one.'),
 'unique_categories':('count','Number of distinct segment categories within a session.'),
 'dominant_category':('category','Largest total clipped category duration in the session; alphabetical exact-tie break.'),
 'window_id':('identifier','Session identifier plus a zero-based four-digit window index.'),
 'window_idx':('index','Zero-based index of consecutive 60-second session-relative windows.'),
 'dominant_activity_category':('category','Largest category-overlap duration in the window; alphabetical exact-tie break; UNLABELLED when no coverage.'),
 'dominant_fraction':('fraction','Dominant category overlap divided by actual window duration (including unlabelled time).'),
 'n_categories':('count','Distinct categories with positive overlap above numerical tolerance in a window.'),
 'context_sample_count':('count','Context samples assigned by half-open session-relative time; no interpolation.'),
 'next_session_id':('identifier','Next recorded session in a consecutive pair.'),
 'next_study_day':('index','Study-day label of next session.'),
 'cross_study_day':('boolean','Pair crosses study-day labels; gap is not verified continuously observed idle time.'),
 'recorded_session_time_sec':('seconds','Sum of elapsed session durations including any gaps already merged upstream.'),
 'session_count':('count','Recorded sessions in participant/study-day group.'),
 'category_changes':('count','Actual within-session category changes in the day.'),
 'category_changes_per_hour':('changes/hour','Within-session category changes divided by elapsed recorded session hours.'),
 }
 if c in exact:return exact[c]
 if c.startswith('mean_'):return ('source scale; see base field','Arithmetic mean of nonmissing direct context samples in window: '+c[5:]+'. Not time-weighted or interpolated.')
 if c.startswith('n_'):return ('count','Number of nonmissing direct context samples for '+c[2:]+'.')
 if c.startswith('activity_seconds_'):return ('seconds','Total clipped segment duration for category '+c[17:]+'.')
 if c.startswith(('rolling_use_','recent_use_')):return ('seconds','Intersection duration of recorded participant sessions and trailing horizon at window/session start. Can span study days; unavailable history is not observed inactivity.')
 if c in ['session_start_sec','session_end_sec','segment_start_sec','segment_end_sec','source_segment_start_sec','source_segment_end_sec','time_sec','window_start_sec','window_end_sec']:return ('relative seconds','Time from participant-specific source midnight of first recorded session; calendar origin removed; interval convention [start,end). Source_segment fields preserve pre-clipping values.')
 special={
 'session_duration_sec':'Elapsed interval end minus start, including any brief gaps merged in supplied sessions.',
 'segment_duration_sec':'Cleaned segment end minus start.',
 'break_before_sec':'Current start minus previous recorded session end, across study-day boundaries; first session missing.',
 'history_since_first_session_sec':'Elapsed time since first recorded session; not a measure of logger uptime.',
 'cumulative_daily_use_before_sec':'Sum of preceding session durations within supplied study day.',
 'cumulative_daily_use_sec':'Recorded duration within supplied study day before window start.',
 'category_covered_sec':'Sum of clipped category interval overlaps.',
 'unlabelled_sec':'Session/window duration with no category interval support; never imputed.',
 'window_actual_duration_sec':'Window end minus start; partial terminal windows retained.',
 'dominant_overlap_sec':'Largest category-overlap duration within window.',
 'minority_category_sec':'Category-covered duration minus dominant category duration.',
 'gap_sec':'Next start minus previous end; unknown logger uptime prevents interpreting it as observed inactivity.',
 'median_session_duration_sec':'Median session duration within supplied observation day.',
 'max_session_duration_sec':'Maximum session duration within supplied observation day.'}
 if c in special:return ('seconds',special[c])
 raise ValueError('Undocumented field: '+c)

def build(root):
 rows=[];schemas={}
 keys={'participants':['participant_id'],'study_days':['participant_id','study_day'],'phone_events':['event_id'],'context_samples':['context_id'],'phone_sessions':['session_id'],'app_segments':['segment_id'],'windows_60s':['window_id'],'between_session_transitions':['previous_session_id','next_session_id'],'daily_summary':['participant_id','study_day']}
 for p in sorted((root/'data').rglob('*.csv')):
  d=pd.read_csv(p);name=str(p.relative_to(root));fields=[]
  for c in d:
   unit,description=meaning(c);row={'file':name,'column':c,'type':str(d[c].dtype),'unit':unit,'missing_count':int(d[c].isna().sum()),'description':description};rows.append(row);fields.append(row)
  schemas[name]={'rows':len(d),'primary_key':keys[p.stem],'fields':fields}
 pd.DataFrame(rows).to_csv(root/'docs/data_dictionary.csv',index=False);(root/'docs/schema.json').write_text(json.dumps(schemas,indent=2)+'\n')
