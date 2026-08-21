import argparse,json,time
from pathlib import Path
from app.pipeline import run

p=argparse.ArgumentParser()
p.add_argument("--config",default="series.json")
p.add_argument("--count",type=int,default=1)
a=p.parse_args()
cfg=json.loads(Path(a.config).read_text(encoding="utf-8"))
for i in range(a.count):
    print(f"=== VIDEO {i+1}/{a.count} ===")
    try: print(json.dumps(run(cfg),indent=2,default=str))
    except Exception as e: print("FAILED:",repr(e))
    if i+1<a.count: time.sleep(5)
