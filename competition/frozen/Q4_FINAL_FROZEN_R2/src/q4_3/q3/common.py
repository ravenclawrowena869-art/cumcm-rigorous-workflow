import hashlib
import json
import math
from datetime import datetime,timedelta,timezone

TZ=timezone(timedelta(hours=8))
def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def instant(value):
    d=datetime.fromisoformat(value) if isinstance(value,str) else value
    if not isinstance(d,datetime) or d.utcoffset() is None:raise ValueError('TIMEZONE_REQUIRED')
    return d
def start(date):return datetime.fromisoformat(date).replace(tzinfo=TZ)
def numeric(value,low=0.,high=math.inf):
    if type(value) not in (float,int) or not math.isfinite(value) or not low<=value<=high:raise ValueError('INVALID_NUMBER')
    return float(value)
