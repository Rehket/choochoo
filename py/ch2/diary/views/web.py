
from ..model import DB
from ...sql import StatisticJournal, Source


def str_or_int_or_none(x):
    return x is None or isinstance(x, (str, int))


def rewrite_db(model):
    if isinstance(model, list):
        return [rewrite_db(m) for m in model]
    if DB in model:
        db = model[DB]
        if hasattr(db, 'id'):
            model[DB] = db.id
        elif isinstance(db, (str, int)):  # images have urls (no they don't - is this still used?)
            model[DB] = db
        else:  # links have tuples
            model[DB] = [x if str_or_int_or_none(x) else x.id for x in db]
    return model
