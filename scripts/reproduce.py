"""Rebuild tables, audit metrics, figures, dictionary, and paper tables."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pipeline import ROOT,derive,CATEGORIES

def run():
 m=derive(ROOT);s=pd.read_csv(ROOT/'data/derived/phone_sessions.csv');a=pd.read_csv(ROOT/'data/derived/app_segments.csv');d=pd.read_csv(ROOT/'data/derived/daily_summary.csv');figdir=ROOT/'results/figures';figdir.mkdir(exist_ok=True)
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
 def finish(fig,name):
  fig.tight_layout();fig.savefig(figdir/(name+'.png'),dpi=250);fig.savefig(figdir/(name+'.svg'));plt.close(fig)
 fig,ax=plt.subplots(figsize=(7.5,3.6));bins=[0,10,30,60,180,600,1800,3600,np.inf];counts=np.histogram(s.session_duration_sec,bins)[0]/len(s)*100;ax.bar(range(8),counts,color='#326a91');ax.set_xticks(range(8),['<10 s','10–30 s','30–60 s','1–3 min','3–10 min','10–30 min','30–60 min','60+ min'],rotation=20);ax.set_ylabel('Sessions (%)');ax.set_xlabel('Elapsed session duration');ax.set_ylim(0,42)
 for i,v in enumerate(counts):ax.text(i,v+.5,f'{v:.1f}%',ha='center')
 finish(fig,'session_duration')
 cats=a.groupby('activity_category').segment_duration_sec.sum().sort_values();shares=cats/cats.sum()*100
 fig,ax=plt.subplots(figsize=(6.5,4));ax.barh(cats.index.str.replace('_',' ').str.title(),shares,color='#326a91');ax.set_xlabel('Share of clipped category-covered time (%)');ax.set_xlim(0,29)
 for i,v in enumerate(shares):ax.text(v+.2,i,f'{v:.1f}%',va='center')
 finish(fig,'activity_composition')
 xb=pd.cut(d.recorded_session_time_sec/3600,[0,1,2,4,6,np.inf],right=False,labels=['<1 h','1–2 h','2–4 h','4–6 h','6+ h']);yb=pd.cut(d.category_changes_per_hour,[0,8,12,16,np.inf],right=False,labels=['<8','8–12','12–16','16+']);ct=pd.crosstab(yb,xb,dropna=False)
 fig,ax=plt.subplots(figsize=(6.2,3.8));im=ax.imshow(ct.to_numpy(),origin='lower',cmap='Blues');ax.set_xticks(range(5),ct.columns);ax.set_yticks(range(4),ct.index);ax.set_xlabel('Recorded session hours per study day');ax.set_ylabel('Category changes per recorded hour')
 for i in range(4):
  for j in range(5):ax.text(j,i,str(ct.iloc[i,j]),ha='center',va='center',color='white' if ct.iloc[i,j]>13 else '#172c40')
 fig.colorbar(im,ax=ax,label='Participant-days');finish(fig,'daily_variation');ct.to_csv(ROOT/'results/daily_switching_cells.csv')
 title='# Reproduction results\n\nThese are deterministic summaries of the supplied snapshot, not population estimates.\n\n| Measure | Value |\n|---|---:|\n'
 for k,v in m.items():
  if k!='base_checks':title+=f'| {k} | {v:.9f} |\n' if isinstance(v,float) else f'| {k} | {v} |\n'
 (ROOT/'results/SUMMARY.md').write_text(title)
 tex='\\begin{tabular}{lr}\n\\hline\nMeasure & Value \\\\\n\\hline\n'
 for label,value in [('Mixed-category windows',f"{m['mixed_windows']:,} ({m['mixed_windows_percent']:.2f}\\%)"),('Minority category time',f"{m['minority_category_seconds']/3600:.2f} h"),('Suppressed share',f"{m['minority_fraction_percent']:.2f}\\%"),('Original category changes',str(m['original_category_changes'])),('Dominant-label changes',str(m['dominant_window_label_changes'])),('Net change-count reduction',f"{m['net_change_count_reduction_percent']:.2f}\\%")]:tex+=label+' & '+value+' \\\\\n'
 tex+='\\hline\n\\end{tabular}\n';(ROOT/'results/aggregation_table.tex').write_text(tex)
 from dictionary import build
 build(ROOT)
 print(json.dumps({k:v for k,v in m.items() if k!='base_checks'},indent=2))
if __name__=='__main__':run()
