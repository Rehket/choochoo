from logging import getLogger

from sqlalchemy import text

from ch2.sql.tables.sector import SectorJournal
from ch2.sql.utils import add

log = getLogger(__name__)


HULL_RADIUS = 40


def find_sectors(s, sector_group, ajournal, owner):
    sql = text('''
with srid as (select s.id as sector_id,
                     st_setsrid(s.route, sg.srid) as sector,
                     st_transform(aj.route_t::geometry, sg.srid) as route_t,
                     st_setsrid(s.start, sg.srid) as start,
                     st_setsrid(s.finish, sg.srid) as finish
                from sector as s,
                     activity_journal as aj,
                     sector_group as sg
               where s.sector_group_id = sg.id
                 and sg.id = :sector_group_id
                 and aj.id = :activity_journal_id
                 and s.owner = :owner
                 and st_intersects(st_setsrid(s.hull, sg.srid), st_transform(aj.route_t::geometry, sg.srid))),
     start_point as (select r.sector_id,
                            r.route_t,
                            (st_dump(st_multi(st_intersection(r.start, r.route_t)))).geom as point
                       from srid as r),
     start_fraction as (select p.sector_id,
                               st_linelocatepoint(p.route_t, p.point) as fraction
                          from start_point as p
                         where st_geometrytype(p.point) = 'ST_Point'),  -- small number of cases intersect as lines
     finish_point as (select r.sector_id,
                             r.route_t,
                             (st_dump(st_multi(st_intersection(r.finish, r.route_t)))).geom as point
                        from srid as r),
     finish_fraction as (select p.sector_id,
                                st_linelocatepoint(p.route_t, p.point) as fraction
                           from finish_point as p
                          where st_geometrytype(p.point) = 'ST_Point')
select distinct  -- multiple starts/finishes can lead to duplicates
       r.sector_id,
       s.fraction as start_fraction,
       f.fraction as finish_fraction,
       aj.start + interval '1' second * st_m(st_lineinterpolatepoint(r.route_t, s.fraction)) as start,
       aj.start + interval '1' second * st_m(st_lineinterpolatepoint(r.route_t, f.fraction)) as finish,
       st_length(st_linesubstring(r.route_t, s.fraction, f.fraction)) as distance
  from srid as r,
       start_fraction as s,
       finish_fraction as f,
       activity_journal as aj
 where aj.id = :activity_journal_id
   and s.fraction < f.fraction
   and s.sector_id = f.sector_id
   and s.sector_id = r.sector_id
   and st_length(st_linesubstring(r.route_t, s.fraction, f.fraction)) 
       between 0.95 * st_length(r.sector) and 1.05 * st_length(r.sector)
''')
    log.debug(sql)
    result = s.connection().execute(sql, sector_group_id=sector_group.id, activity_journal_id=ajournal.id,
                                    owner=owner)
    for row in result.fetchall():
        data = {name: value for name, value in zip(result.keys(), row)}
        sjournal = add(s, SectorJournal(activity_journal_id=ajournal.id, activity_group=ajournal.activity_group,
                                        **data))
        s.flush()
        yield sjournal


def add_sector_statistics(s, sjournal, loader):
    # delegate to the sector since that can be subclassed (eg climb)
    sjournal.sector.add_statistics(s, sjournal, loader)


def add_start_finish(s, sector_id):
    # need to take just the final metre at each end of the route and shift to avoid multilines
    # with 'jigsaw' shaped routes (endpoint of multiline is null).
    sql = text('''
with srid as (select st_setsrid(s.route, sg.srid) as route,
                     st_length(st_setsrid(s.route, sg.srid)) as length
                from sector as s,
                     sector_group as sg
               where s.id = :sector_id
                 and sg.id = s.sector_group_id),
     ends as (select st_linesubstring(route, 0, 1/length) as start,
                     st_linesubstring(route, 1-1/length, 1) as finish,
                     route
                from srid),
     offsets as (select st_offsetcurve(start, :radius) as start_left,
                        st_offsetcurve(start, -:radius) as start_right,
                        st_offsetcurve(finish, :radius) as finish_left,
                        st_offsetcurve(finish, -:radius) as finish_right,
                        st_buffer(route, :radius, 'endcap=flat') as hull
                   from ends),
     endcaps as (select st_makeline(st_startpoint(start_left), st_endpoint(start_right)) as start,
                        st_makeline(st_endpoint(finish_left), st_startpoint(finish_right)) as finish,
                        o.hull
                   from offsets as o)
update sector
   set start = e.start,
       finish = e.finish,
       hull = e.hull
  from endcaps as e
 where sector.id = :sector_id
''')
    log.debug(sql)
    s.connection().execute(sql, sector_id=sector_id, radius=HULL_RADIUS)