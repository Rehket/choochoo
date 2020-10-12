from logging import getLogger

import pandas as pd
from sqlalchemy import text, select

from .utils import ProcessCalculator, ActivityJournalCalculatorMixin, DataFrameCalculatorMixin
from ..pipeline import LoaderMixin
from ...common.geo import utm_srid
from ...common.math import is_nan
from ...data import Statistics
from ...data.elevation import smooth_elevation
from ...data.frame import present
from ...names import N, T, U
from ...sql import StatisticJournalType, ActivityJournal

log = getLogger(__name__)


class ElevationCalculator(LoaderMixin, ActivityJournalCalculatorMixin, DataFrameCalculatorMixin, ProcessCalculator):

    def __init__(self, *args, smooth=3, **kargs):
        self.smooth = smooth
        super().__init__(*args, **kargs)

    def _startup(self, s):
        super()._startup(s)
        self._provides(s, T.ELEVATION, StatisticJournalType.FLOAT, U.M, None,
                       'An estimate of elevation (may come from various sources).')
        self._provides(s, T.GRADE, StatisticJournalType.FLOAT, U.PC, None,
                       'The gradient of the smoothed SRTM1 elevation.')

    def _read_dataframe(self, s, ajournal):
        from ..owners import SegmentReader
        try:
            return Statistics(s, activity_journal=ajournal, with_timespan=True). \
                by_name(SegmentReader, N.LATITUDE, N.LONGITUDE, N.DISTANCE, N.ELAPSED_TIME,
                        N.RAW_ELEVATION, N.ELEVATION, N.ALTITUDE).df
        except Exception as e:
            log.warning(f'Failed to generate statistics for elevation: {e}')
            raise

    def _calculate_stats(self, s, ajournal, df):
        if not present(df, N.ELEVATION):
            if present(df, N.RAW_ELEVATION):
                df = smooth_elevation(df, smooth=self.smooth)
            elif present(df, N.ALTITUDE):
                log.warning(f'Using {N.ALTITUDE} as {N.ELEVATION}')
                df[N.ELEVATION] = df[N.ALTITUDE]
            return df
        else:
            return None

    def _copy_results(self, s, ajournal, loader, df):
        for time, row in df.iterrows():
            if N.ELEVATION in row and not is_nan(row[N.ELEVATION]):
                loader.add_data(N.ELEVATION, ajournal, row[N.ELEVATION], time)
            if N.GRADE in row and not is_nan(row[N.GRADE]):
                loader.add_data(N.GRADE, ajournal, row[N.GRADE], time)
        self.__create_postgis(s, ajournal, df)

    def __create_postgis(self, s, ajournal, df):
        # this includes things that could have been created earlier, but if we build them from SQL
        # queries then it's significantly slower
        if self.__create_route(s, ajournal, df, 'route_d', N.DISTANCE):
            self.__create_centre(s, ajournal)
            self.__create_utm_srid(s, ajournal)
        self.__create_route(s, ajournal, df, 'route_t', N.ELAPSED_TIME)
        self.__create_route_z(s, ajournal, df, 'route_ed', N.DISTANCE)
        self.__create_route_z(s, ajournal, df, 'route_et', N.ELAPSED_TIME)
        compress_distance_time(df)
        self.__create_route(s, ajournal, df, 'route_dt', N.DISTANCE_TIME)
        self.__create_route_z(s, ajournal, df, 'route_edt', N.DISTANCE_TIME)

    def __create_route_z(self, s, ajournal, df, name, m):
        log.debug(f'Setting {name}')
        xyzm = list(self.__xyzm(df, m))
        if xyzm:
            points = [f'ST_MakePoint({x}, {y}, {z}, {m})' for x, y, z, m in xyzm]
            line = f'ST_MakeLine(ARRAY[{", ".join(points)}])'
        else:
            log.warning(f'Empty {name}')
            line = "'LINESTRINGZM EMPTY'::geography"
        table = ajournal.__table__
        update = table.update().values(**{name: text(line)}).where(table.c.id == ajournal.id)
        # log.debug(update)
        s.execute(update)

    def __xyzm(self, df, m):
        if N.ELEVATION in df:
            for _, row in df.dropna().iterrows():
                yield row[N.LONGITUDE], row[N.LATITUDE], row[N.ELEVATION], row[m]

    def __create_route(self, s, ajournal, df, name, m):
        log.debug(f'Setting {name}')
        xym = list(self.__xym(df, m))
        if xym:
            points = [f'ST_MakePointM({x}, {y}, {m})' for x, y, m in xym]
            line = f'ST_MakeLine(ARRAY[{", ".join(points)}])'
        else:
            log.warning(f'Empty {name}')
            line = "'LINESTRINGM EMPTY'::geography"
        table = ajournal.__table__
        update = table.update().values(**{name: text(line)}).where(table.c.id == ajournal.id)
        # log.debug(update)
        s.execute(update)
        return bool(xym)

    def __xym(self, df, m):
        for _, row in df.dropna().iterrows():
            yield row[N.LONGITUDE], row[N.LATITUDE], row[m]

    def __create_utm_srid(self, s, ajournal):
        table = ActivityJournal.__table__
        query = select([text(f'ST_X({table.c.centre}::geometry)'), text(f'ST_Y({table.c.centre}::geometry)')]). \
            where(table.c.id == ajournal.id)
        log.debug(query)
        row = s.execute(query).fetchone()
        lon, lat = row[0], row[1]
        srid = utm_srid(lat, lon)
        update = table.update().values(utm_srid=srid).where(table.c.id == ajournal.id)
        log.debug(update)
        s.execute(update)

    def __create_centre(self, s, ajournal):
        table = ActivityJournal.__table__
        centre = f'ST_Centroid({table.c.route_d})'
        update = table.update().values(centre=text(centre)).where(table.c.id == ajournal.id)
        log.debug(update)
        s.execute(update)


def elapsed_time_to_time(df, t0):
    df[N.TIME] = pd.to_timedelta(df[N.ELAPSED_TIME], 'seconds') + t0
    return df


def compress_distance_time(df):
    # convert to m and round both to 1dp
    df[N.DISTANCE_TIME] = (df[N.DISTANCE] * 1e3 * 10 + 0.5).astype(int) * 1e7 / 10 + \
                          (df[N.ELAPSED_TIME] * 10 + 0.5).astype(int) / 10
    return df


def expand_distance_time(df):
    df[N.DISTANCE] = (df[N.DISTANCE_TIME] / 1e7).round(1)
    df[N.ELAPSED_TIME] = (df[N.DISTANCE_TIME] - df[N.DISTANCE] * 1e7).round(1)
    df[N.DISTANCE] /= 1000   # convert back to km
    return df
