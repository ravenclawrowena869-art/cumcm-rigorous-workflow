from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

@dataclass(frozen=True)
class PricePoint:
    target_ts: str
    decision_time: str
    decision_price: float
    settlement_price: float
    known_at: str
    source: str
    mode: str
    slot: int

class Q4PriceProvider:
    """Frozen Q4 R1 price-information provider.

    Causal future price: same delivery slot's realized price 7 days earlier.
    Oracle: true future realized target price, diagnostic only.
    Settlement: true realized target-slot price in both modes.
    """
    def __init__(self, lag7_csv: str | Path, stage_csv: str | Path | None = None):
        self.df = pd.read_csv(lag7_csv)
        req = {'date','slot','target_ts','price_realized','price_forecast_lag7','source_realized_ts'}
        miss = req - set(self.df.columns)
        if miss:
            raise ValueError(f'MISSING_PRICE_COLUMNS:{sorted(miss)}')
        self.df['date'] = self.df['date'].astype(str)
        self.df['slot'] = self.df['slot'].astype(int)
        self.df['target_ts_dt'] = pd.to_datetime(self.df['target_ts'])
        self.df['source_realized_ts_dt'] = pd.to_datetime(self.df['source_realized_ts'])
        self.by_date = {d:g.sort_values('slot').copy() for d,g in self.df.groupby('date')}
        self.stage = None
        if stage_csv is not None:
            self.stage = pd.read_csv(stage_csv)
            self.stage['date']=self.stage['date'].astype(str)
            self.stage['stage_hour']=self.stage['stage_hour'].astype(int)
            self.stage['slot']=self.stage['slot'].astype(int)
            self.stage['decision_time_dt']=pd.to_datetime(self.stage['decision_time'])
            self.stage['target_ts_dt']=pd.to_datetime(self.stage['target_ts'])
            self.stage['source_realized_ts_dt']=pd.to_datetime(self.stage['source_realized_ts'])

    @staticmethod
    def _day_start(date: str) -> datetime:
        return datetime.fromisoformat(date+'T00:00:00')

    def _day(self,date: str) -> pd.DataFrame:
        if date not in self.by_date:
            raise KeyError(f'PRICE_DATE_NOT_FOUND:{date}')
        g=self.by_date[date]
        if len(g)!=144 or g['slot'].tolist()!=list(range(1,145)):
            raise ValueError(f'PRICE_SLOT_IDENTITY:{date}')
        return g

    def q4_2_day_ahead(self,date: str,mode: str='CAUSAL_LAG7') -> list[PricePoint]:
        g=self._day(date); decision=self._day_start(date)
        out=[]
        for r in g.itertuples(index=False):
            if mode=='CAUSAL_LAG7':
                price=float(r.price_forecast_lag7); known=r.source_realized_ts_dt
                source='LAG7_REALIZED'
                if known>decision:
                    raise ValueError('FUTURE_PRICE_LEAKAGE')
            elif mode=='ORACLE_DIAGNOSTIC':
                price=float(r.price_realized); known=r.target_ts_dt; source='ORACLE_REALIZED_DIAGNOSTIC'
            else: raise ValueError('UNKNOWN_PRICE_MODE')
            out.append(PricePoint(r.target_ts,decision.isoformat(),price,float(r.price_realized),known.isoformat(),source,mode,int(r.slot)))
        return out

    def q4_2_intraday(self,date: str,current_slot: int,mode: str='CAUSAL_LAG7') -> list[PricePoint]:
        if not 1<=current_slot<=144: raise ValueError('CURRENT_SLOT_RANGE')
        g=self._day(date); decision=self._day_start(date)+timedelta(minutes=10*current_slot)
        out=[]
        for r in g[g['slot']>=current_slot].itertuples(index=False):
            if mode=='CAUSAL_LAG7':
                if int(r.slot)==current_slot:
                    price=float(r.price_realized); known=r.target_ts_dt; source='CURRENT_REALIZED'
                    if known>decision: raise ValueError('CURRENT_PRICE_NOT_YET_KNOWN')
                else:
                    price=float(r.price_forecast_lag7); known=r.source_realized_ts_dt; source='LAG7_REALIZED'
                    if known>decision: raise ValueError('FUTURE_PRICE_LEAKAGE')
            elif mode=='ORACLE_DIAGNOSTIC':
                price=float(r.price_realized); known=r.target_ts_dt; source='ORACLE_REALIZED_DIAGNOSTIC'
            else: raise ValueError('UNKNOWN_PRICE_MODE')
            out.append(PricePoint(r.target_ts,decision.isoformat(),price,float(r.price_realized),known.isoformat(),source,mode,int(r.slot)))
        return out

    def q4_3_stage(self,date: str,stage_hour: int,mode: str='CAUSAL_LAG7') -> list[PricePoint]:
        if stage_hour not in (0,6,12,18): raise ValueError('STAGE_HOUR')
        decision=self._day_start(date)+timedelta(hours=stage_hour)
        first={0:1,6:37,12:73,18:109}[stage_hour]
        g=self._day(date)
        out=[]
        for r in g[g['slot']>=first].itertuples(index=False):
            if mode=='CAUSAL_LAG7':
                price=float(r.price_forecast_lag7); known=r.source_realized_ts_dt; source='LAG7_REALIZED'
                if known>decision: raise ValueError('FUTURE_PRICE_LEAKAGE')
            elif mode=='ORACLE_DIAGNOSTIC':
                price=float(r.price_realized); known=r.target_ts_dt; source='ORACLE_REALIZED_DIAGNOSTIC'
            else: raise ValueError('UNKNOWN_PRICE_MODE')
            out.append(PricePoint(r.target_ts,decision.isoformat(),price,float(r.price_realized),known.isoformat(),source,mode,int(r.slot)))
        return out
