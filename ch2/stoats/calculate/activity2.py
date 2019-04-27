
import re
from json import loads
from logging import getLogger

from . import ActivityJournalCalculatorMixin, DataFrameCalculatorMixin, MultiProcCalculator
from ..names import ELEVATION, DISTANCE, M, POWER_ESTIMATE, HEART_RATE, ACTIVE_DISTANCE, MSR, SUM, CNT, MAX, summaries, \
    ACTIVE_SPEED, ACTIVE_TIME, AVG, S, KMH, MIN_KM_TIME_ANY, MIN, MED_KM_TIME_ANY, PERCENT_IN_Z_ANY, PC, \
    TIME_IN_Z_ANY, MAX_MED_HR_M_ANY, W, BPM, MAX_MEAN_EP_M_ANY, CLIMB_ELEVATION, CLIMB_DISTANCE, CLIMB_TIME, \
    CLIMB_GRADIENT, TOTAL_CLIMB, HR_ZONE, TIME
from ...data.activity import active_stats, times_for_distance, hrz_stats, max_med_stats, max_mean_stats
from ...data.climb2 import find_climbs, Climb
from ...data.frame import activity_statistics, present
from ...squeal import StatisticJournalFloat, Constant

log = getLogger(__name__)


class ActivityCalculator(ActivityJournalCalculatorMixin, DataFrameCalculatorMixin, MultiProcCalculator):

    def __init__(self, *args, cost_calc=20, cost_write=1, climb=None, **kargs):
        self.climb_ref = climb
        super().__init__(*args, cost_calc=cost_calc, cost_write=cost_write, **kargs)

    def _read_dataframe(self, s, ajournal):
        try:
            return activity_statistics(s, DISTANCE, ELEVATION, HEART_RATE, HR_ZONE, POWER_ESTIMATE,
                                       activity_journal=ajournal, with_timespan=True)
        except Exception as e:
            log.warning(f'Failed to generate statistics for activity: {e}')
            raise

    def _calculate_stats(self, s, ajournal, df):
        stats, climbs = {}, None
        stats.update(active_stats(df))
        stats.update(times_for_distance(df))
        stats.update(hrz_stats(df))
        stats.update(max_med_stats(df))
        stats.update(max_mean_stats(df))
        if present(df, ELEVATION):
            params = Climb(**loads(Constant.get(s, self.climb_ref).at(s).value))
            climbs = list(find_climbs(df, params=params))
        return df, stats, climbs

    def _copy_results(self, s, ajournal, loader, data):
        df, stats, climbs = data
        self.__copy(ajournal, loader, stats, ACTIVE_DISTANCE, M, summaries(MAX, CNT, SUM, MSR), ajournal.start)
        self.__copy(ajournal, loader, stats, ACTIVE_TIME, S, summaries(MAX, SUM, MSR), ajournal.start)
        self.__copy(ajournal, loader, stats, ACTIVE_SPEED, KMH, summaries(MAX, AVG, MSR), ajournal.start)
        self.__copy_all(ajournal, loader, stats, MIN_KM_TIME_ANY, S, summaries(MIN, MSR), ajournal.start)
        self.__copy_all(ajournal, loader, stats, MED_KM_TIME_ANY, S, summaries(MIN, MSR), ajournal.start)
        self.__copy_all(ajournal, loader, stats, PERCENT_IN_Z_ANY, PC, None, ajournal.start)
        self.__copy_all(ajournal, loader, stats, TIME_IN_Z_ANY, S, None, ajournal.start)
        self.__copy_all(ajournal, loader, stats, MAX_MED_HR_M_ANY, BPM, summaries(MAX, MSR), ajournal.start)
        self.__copy_all(ajournal, loader, stats, MAX_MEAN_EP_M_ANY, W, summaries(MAX, MSR), ajournal.start)
        if climbs:
            loader.add(TOTAL_CLIMB, M, summaries(MAX, SUM, MSR), ajournal.activity_group, ajournal,
                       sum(climb[CLIMB_ELEVATION] for climb in climbs), ajournal.start, StatisticJournalFloat)
            for climb in sorted(climbs, key=lambda climb: climb[TIME]):
                self.__copy(ajournal, loader, climb, CLIMB_ELEVATION, M, summaries(MAX, SUM, MSR), climb[TIME])
                self.__copy(ajournal, loader, climb, CLIMB_DISTANCE, M, summaries(MAX, SUM, MSR), climb[TIME])
                self.__copy(ajournal, loader, climb, CLIMB_TIME, S, summaries(MAX, SUM, MSR), climb[TIME])
                self.__copy(ajournal, loader, climb, CLIMB_GRADIENT, PC, summaries(MAX, SUM, MSR), climb[TIME])

    def __copy_all(self, ajournal, loader, stats, pattern, units, summary, time):
        matcher = re.compile(re.sub('%', '.+', pattern))
        for name in stats:
            if matcher.match(name):
                self.__copy(ajournal, loader, stats, name, units, summary, time)

    def __copy(self, ajournal, loader, stats, name, units, summary, time):
        loader.add(name, units, summary, ajournal.activity_group, ajournal, stats[name], time, StatisticJournalFloat)