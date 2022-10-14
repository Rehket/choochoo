
from logging import getLogger

from sqlalchemy import or_

from .utils import Displayer
from ..calculate.summary import SummaryCalculator
from ...diary.database import interval_column
from ...diary.model import text, from_field, optional_text, value, trim_no_stats
from ...sql import DiaryTopicJournal, DiaryTopic, StatisticJournal, Interval

log = getLogger(__name__)


class DiaryDisplayer(Displayer):

    @optional_text('Diary')
    def _read_date(self, s, date):
        journal = DiaryTopicJournal.get_or_add(s, date)
        for topic in s.query(DiaryTopic).filter(DiaryTopic.parent is None, or_(DiaryTopic.start <= date, DiaryTopic.start is None), or_(DiaryTopic.finish >= date, DiaryTopic.finish is None)).order_by(DiaryTopic.sort).all():
            if topic.schedule.at_location(date):
                yield list(self.__read_date_diary_topic(s, date, journal.cache(s), topic))

    def __read_date_diary_topic(self, s, date, cache, topic):
        yield text(topic.title)
        if topic.description: yield text(topic.description)
        log.debug(f'topic id {topic.id}; fields {topic.fields}')
        for field in topic.fields:
            if field.schedule.at_location(date):
                yield from_field(field, cache[field])
        for child in topic.children:
            if child.schedule.at_location(date):
                if content := list(
                    self.__read_date_diary_topic(s, date, cache, child)
                ):
                    # single entries are just text fields
                    if len(content) == 1:
                        yield content[0]
                    else:
                        yield content

    @optional_text('Diary')
    @trim_no_stats
    def _read_schedule(self, s, date, schedule):
        if (
            interval := s.query(Interval)
            .filter(
                Interval.schedule == schedule,
                Interval.start == date,
                Interval.activity_group is None,
            )
            .one_or_none()
        ):
            for topic in s.query(DiaryTopic).filter(DiaryTopic.parent is None, or_(DiaryTopic.start < interval.finish, DiaryTopic.start is None), or_(DiaryTopic.finish >= date, DiaryTopic.finish is None)).order_by(DiaryTopic.sort).all():
                yield list(self.__read_interval_topic(s, interval, topic))

    def __read_interval_topic(self, s, interval, topic):
        yield text(topic.title)
        if topic.description: yield text(topic.description)
        for field in topic.fields:
            if column := list(
                interval_column(
                    s, interval, field.statistic_name.name, SummaryCalculator
                )
            ):
                yield column
        for child in topic.children:
            if (child.start is None or child.start < interval.finish) and \
                        (child.finish is None or child.finish > interval.start):
                if content := list(self.__read_interval_topic(s, interval, child)):
                    yield content
