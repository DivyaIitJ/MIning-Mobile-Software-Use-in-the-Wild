"""Build validated temporal views from the released base tables."""
from pathlib import Path
import argparse, hashlib,json
import numpy as np
import pandas as pd

TOL=1e-6
ROOT=Path(__file__).resolve().parents[1]
CATEGORIES=['BROWSER_SEARCH','CAMERA_MEDIA','GAMING','MAP_NAVIGATION','MESSAGING','MUSIC_AUDIO','OTHER','PRODUCTIVITY','READING_NEWS','SHOPPING','SOCIAL_FEED','VIDEO']

def cumulative(t,starts,ends):
    starts=np.asarray(starts,dtype=float);ends=np.asarray(ends,dtype=float);t=np.asarray(t,dtype=float)
    if not len(starts):return np.zeros_like(t)
    prefix=np.r_[0.,np.cumsum(ends-starts)];i=np.searchsorted(starts,t,side='right')-1;j=np.maximum(i,0)
    return np.where(i<0,0.,prefix[j]+np.clip(t-starts[j],0,ends[j]-starts[j]))

def recent(t,starts,ends,horizon):return cumulative(t,starts,ends)-cumulative(np.asarray(t)-horizon,starts,ends)

def composition(a,b,starts,ends,cats):
    ov=np.maximum(0,np.minimum(b,ends)-np.maximum(a,starts));totals={}
    for cat,v in zip(cats,ov):
        if v>TOL:totals[cat]=totals.get(cat,0.)+float(v)
    covered=sum(totals.values());dom=min(totals,key=lambda k:(-totals[k],k)) if totals else 'UNLABELLED'
    dominant=totals.get(dom,0.)
    return {'dominant_activity_category':dom,'category_covered_sec':covered,'unlabelled_sec':max(0,b-a-covered),'n_categories':len(totals),'dominant_overlap_sec':dominant,'dominant_fraction':dominant/(b-a),'minority_category_sec':covered-dominant}

def save(df,path):df.to_csv(path,index=False,float_format='%.9f')

def load(root):return {n:pd.read_csv(root/'data/base'/f'{n}.csv') for n in ['participants','study_days','phone_sessions','app_segments','phone_events','context_samples']}

def validate_base(b):
    s=b['phone_sessions'];a=b['app_segments'];p=b['participants'];errors=[];checks={}
    def check(name,number):
        checks[name]=int(number)
        if number:errors.append(name)
    for n,key in [('participants',['participant_id']),('study_days',['participant_id','study_day']),('phone_sessions',['session_id']),('app_segments',['segment_id']),('phone_events',['event_id']),('context_samples',['context_id'])]:check(n+'_duplicate_keys',b[n].duplicated(key).sum())
    idx=s.set_index('session_id')
    for n,d in b.items():
        check(n+'_unknown_participant',(~d.participant_id.isin(p.participant_id)).sum())
        if 'session_id' in d:
            check(n+'_orphan_session',(~d.session_id.isin(idx.index)).sum())
            check(n+'_wrong_participant',d.participant_id.ne(d.session_id.map(idx.participant_id)).sum())
            check(n+'_wrong_study_day',d.study_day.ne(d.session_id.map(idx.study_day)).sum())
    for name,d,start,end,group in [('sessions',s,'session_start_sec','session_end_sec','participant_id'),('segments',a,'segment_start_sec','segment_end_sec','session_id')]:
        check(name+'_missing_times',d[[start,end]].isna().sum().sum());check(name+'_nonpositive',(d[end]<=d[start]).sum())
        ds=d.sort_values([group,start]);check(name+'_overlaps',(ds[start]<ds.groupby(group)[end].shift()-TOL).sum())
    check('unknown_categories',(~a.activity_category.isin(CATEGORIES)).sum())
    known_days=pd.MultiIndex.from_frame(b['study_days'][['participant_id','study_day']]);check('session_missing_study_day',(~pd.MultiIndex.from_frame(s[['participant_id','study_day']]).isin(known_days)).sum())
    for n in ['phone_events','context_samples']:
        d=b[n];check(n+'_outside_session',((d.time_sec<d.session_id.map(idx.session_start_sec)-TOL)|(d.time_sec>d.session_id.map(idx.session_end_sec)+TOL)).sum())
    if errors:raise ValueError('Base validation failed: '+', '.join(errors))
    return checks

def derive(root=ROOT):
    root=Path(root);out=root/'data/derived';out.mkdir(parents=True,exist_ok=True);res=root/'results';res.mkdir(exist_ok=True)
    b=load(root);checks=validate_base(b);s=b['phone_sessions'].sort_values(['participant_id','session_start_sec']).copy();a=b['app_segments'].sort_values(['session_id','segment_start_sec','segment_order']).copy();idx=s.set_index('session_id')
    a['source_segment_start_sec']=a.segment_start_sec;a['source_segment_end_sec']=a.segment_end_sec
    a['segment_start_sec']=np.maximum(a.segment_start_sec,a.session_id.map(idx.session_start_sec));a['segment_end_sec']=np.minimum(a.segment_end_sec,a.session_id.map(idx.session_end_sec))
    a['boundary_adjusted']=(np.abs(a.segment_start_sec-a.source_segment_start_sec)>TOL)|(np.abs(a.segment_end_sec-a.source_segment_end_sec)>TOL)
    a['segment_duration_sec']=a.segment_end_sec-a.segment_start_sec
    if (a.segment_duration_sec<=0).any():raise ValueError('Clipping produces nonpositive segments; manual source reconciliation needed.')
    a['is_category_change']=a.groupby('session_id').activity_category.shift().notna()&a.activity_category.ne(a.groupby('session_id').activity_category.shift())
    a['segment_order']=a.groupby('session_id').cumcount()+1
    s['session_duration_sec']=s.session_end_sec-s.session_start_sec;s['session_order_today']=s.groupby(['participant_id','study_day']).cumcount()+1
    s['previous_session_id']=s.groupby('participant_id').session_id.shift();s['break_before_sec']=s.session_start_sec-s.groupby('participant_id').session_end_sec.shift()
    s['previous_study_day']=s.groupby('participant_id').study_day.shift();s['cross_day_before']=s.previous_study_day.notna()&s.study_day.ne(s.previous_study_day)
    s['number_segments']=s.session_id.map(a.groupby('session_id').size());s['number_category_changes']=s.session_id.map(a.groupby('session_id').is_category_change.sum());s['unique_categories']=s.session_id.map(a.groupby('session_id').activity_category.nunique())
    ag={k:g for k,g in a.groupby('session_id',sort=False)}
    windows=[]
    for r in s.itertuples():
        g=ag[r.session_id]
        for k in range(int(np.ceil(r.session_duration_sec/60))):
            start=r.session_start_sec+60*k;end=min(start+60,r.session_end_sec);comp=composition(start,end,g.segment_start_sec.to_numpy(),g.segment_end_sec.to_numpy(),g.activity_category.to_numpy())
            windows.append(dict(participant_id=r.participant_id,study_day=r.study_day,session_id=r.session_id,window_id=f'{r.session_id}-W{k:04d}',window_idx=k,window_start_sec=start,window_end_sec=end,window_actual_duration_sec=end-start,**comp))
    w=pd.DataFrame(windows)
    for pid,g in s.groupby('participant_id',sort=False):
        starts,ends=g.session_start_sec.to_numpy(),g.session_end_sec.to_numpy();wg=w[w.participant_id.eq(pid)]
        for h,label in [(1800,'30min'),(3600,'1h'),(7200,'2h'),(21600,'6h')]:
            s.loc[g.index,'recent_use_'+label+'_before_sec']=recent(starts,starts,ends,h)
            w.loc[wg.index,'rolling_use_'+label+'_sec']=recent(wg.window_start_sec.to_numpy(),starts,ends,h)
        s.loc[g.index,'history_since_first_session_sec']=starts-starts.min()
    for _,g in s.groupby(['participant_id','study_day'],sort=False):
        s.loc[g.index,'cumulative_daily_use_before_sec']=g.session_duration_sec.cumsum()-g.session_duration_sec
        wg=w[w.session_id.isin(g.session_id)]
        w.loc[wg.index,'cumulative_daily_use_sec']=cumulative(wg.window_start_sec.to_numpy(),g.session_start_sec.to_numpy(),g.session_end_sec.to_numpy())
    session_comp={sid:composition(float(idx.loc[sid].session_start_sec),float(idx.loc[sid].session_end_sec),g.segment_start_sec.to_numpy(),g.segment_end_sec.to_numpy(),g.activity_category.to_numpy()) for sid,g in ag.items()}
    s['category_covered_sec']=s.session_id.map({k:v['category_covered_sec'] for k,v in session_comp.items()});s['unlabelled_sec']=s.session_duration_sec-s.category_covered_sec;s['dominant_category']=s.session_id.map({k:v['dominant_activity_category'] for k,v in session_comp.items()})
    # Assign context samples to half-open windows without interpolation.
    c=b['context_samples'].copy();pos=np.floor((c.time_sec-c.session_id.map(idx.session_start_sec))/60).astype(int);c['window_idx']=pos
    measures=['ambient_light_lux','screen_brightness','accelerometer_magnitude','gyroscope_magnitude'];cx=c.groupby(['session_id','window_idx'])[measures].mean().add_prefix('mean_');cn=c.groupby(['session_id','window_idx']).size().rename('context_sample_count')
    w=w.merge(cx.join(cn).reset_index(),on=['session_id','window_idx'],how='left',validate='one_to_one');w['context_sample_count']=w.context_sample_count.fillna(0).astype(int)
    for col in measures:
        counts=c.groupby(['session_id','window_idx'])[col].count();w['n_'+col]=[int(counts.get((sid,k),0)) for sid,k in zip(w.session_id,w.window_idx)]
    tr=s[s.previous_session_id.notna()][['participant_id','previous_session_id','session_id','previous_study_day','study_day','break_before_sec','cross_day_before']].copy().rename(columns={'session_id':'next_session_id','study_day':'next_study_day','break_before_sec':'gap_sec','cross_day_before':'cross_study_day'})
    daily=s.groupby(['participant_id','study_day']).agg(recorded_session_time_sec=('session_duration_sec','sum'),session_count=('session_id','size'),median_session_duration_sec=('session_duration_sec','median'),max_session_duration_sec=('session_duration_sec','max'),category_changes=('number_category_changes','sum'),unlabelled_sec=('unlabelled_sec','sum')).reset_index();daily['category_changes_per_hour']=daily.category_changes/daily.recorded_session_time_sec*3600
    for cat in CATEGORIES:
        totals=a[a.activity_category.eq(cat)].groupby(['participant_id','study_day']).segment_duration_sec.sum();daily['activity_seconds_'+cat]=[totals.get((p,d),0.) for p,d in zip(daily.participant_id,daily.study_day)]
    retained=0
    for _,g in w.groupby('session_id',sort=False):
        x=g.sort_values('window_idx').dominant_activity_category.to_numpy();retained+=sum(x[i]!=x[i-1] and x[i]!='UNLABELLED' and x[i-1]!='UNLABELLED' for i in range(1,len(x)))
    original=int(a.is_category_change.sum());signed=float((b['app_segments'].segment_end_sec-b['app_segments'].segment_start_sec).sum()-s.session_duration_sec.sum())
    metrics={'participants':len(b['participants']),'participant_days':len(b['study_days']),'sessions':len(s),'segments':len(a),'events':len(b['phone_events']),'context_samples':len(c),'recorded_session_hours':s.session_duration_sec.sum()/3600,'windows':len(w),'full_windows':int((w.window_actual_duration_sec>=60-TOL).sum()),'partial_windows':int((w.window_actual_duration_sec<60-TOL).sum()),'unlabelled_windows':int(w.n_categories.eq(0).sum()),'within_day_transitions':int((~tr.cross_study_day).sum()),'cross_day_transitions':int(tr.cross_study_day.sum()),'adjusted_segment_endpoints':int(a.boundary_adjusted.sum()),'source_segment_minus_session_seconds':signed,'unlabelled_session_seconds':float(s.unlabelled_sec.sum()),'mixed_windows':int((w.n_categories>1).sum()),'mixed_windows_percent':float((w.n_categories>1).mean()*100),'minority_category_seconds':float(w.minority_category_sec.sum()),'minority_fraction_percent':float(w.minority_category_sec.sum()/w.category_covered_sec.sum()*100),'original_category_changes':original,'dominant_window_label_changes':int(retained),'net_change_count_reduction_percent':float((1-retained/original)*100) if original else None,'median_sessions_per_day':float(daily.session_count.median()),'median_daily_hours':float(daily.recorded_session_time_sec.median()/3600),'median_session_seconds':float(s.session_duration_sec.median()),'sessions_with_category_change_percent':float((s.number_category_changes>0).mean()*100),'base_checks':checks}
    for name,d in [('phone_sessions',s),('app_segments',a),('windows_60s',w),('between_session_transitions',tr),('daily_summary',daily)]:save(d,out/f'{name}.csv')
    (res/'metrics.json').write_text(json.dumps(metrics,indent=2,allow_nan=False)+'\n')
    # Fail on arithmetic, containment, or window coverage errors.
    wi=w.session_id.map(s.set_index('session_id').session_end_sec);assert (w.window_end_sec<=wi+TOL).all()
    assert np.allclose(w.groupby('session_id').window_actual_duration_sec.sum().reindex(s.session_id),s.session_duration_sec,atol=1e-5,rtol=0)
    assert np.allclose(s.category_covered_sec+s.unlabelled_sec,s.session_duration_sec,atol=1e-5,rtol=0)
    assert (w.category_covered_sec<=w.window_actual_duration_sec+1e-5).all()
    assert len(tr)==len(s)-s.participant_id.nunique()
    assert all(w['rolling_use_'+n+'_sec'].between(-TOL,h+TOL).all() for n,h in [('30min',1800),('1h',3600),('2h',7200),('6h',21600)])
    manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'data').rglob('*.csv'))};(res/'data_checksums.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return metrics

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT);args=parser.parse_args();print(json.dumps(derive(args.root),indent=2))
