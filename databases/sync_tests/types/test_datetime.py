import datetime
from dirty_equals import IsPartialDict
from prisma import Prisma
from prisma.models import Types
from prisma._compat import PYDANTIC_V2, model_json_schema

from lib.testing import assert_similar_time


def test_filtering(client: Prisma) -> None:
    """Finding records by a DateTime value"""
    now = datetime.datetime.now(datetime.timezone.utc)
    with client.batch_() as batcher:
        for i in range(10):
            batcher.types.create(
                {'datetime_': now + datetime.timedelta(hours=i)}
            )

    total = client.types.count(
        where={'datetime_': {'gte': now + datetime.timedelta(hours=5)}}
    )
    assert total == 5

    found = client.types.find_first(
        where={
            'datetime_': {
                'equals': now,
            },
        },
    )
    assert found is not None
    assert_similar_time(found.datetime_, now)

    results = client.types.find_many(
        where={
            'datetime_': {
                'in': [
                    now + datetime.timedelta(hours=1),
                    now + datetime.timedelta(hours=4),
                    now + datetime.timedelta(hours=10),
                ],
            },
        },
        order={
            'datetime_': 'asc',
        },
    )
    assert len(results) == 2
    assert_similar_time(
        results[0].datetime_, now + datetime.timedelta(hours=1)
    )
    assert_similar_time(
        results[1].datetime_, now + datetime.timedelta(hours=4)
    )

    found = client.types.find_first(
        where={
            'datetime_': {
                'not_in': [
                    now,
                    now + datetime.timedelta(hours=1),
                    now + datetime.timedelta(hours=2),
                ],
            },
        },
        order={
            'datetime_': 'asc',
        },
    )
    assert found is not None
    assert_similar_time(found.datetime_, now + datetime.timedelta(hours=3))

    found = client.types.find_first(
        where={
            'datetime_': {
                'lt': now + datetime.timedelta(hours=1),
            },
        },
        order={
            'datetime_': 'desc',
        },
    )
    assert found is not None
    assert_similar_time(found.datetime_, now)

    found = client.types.find_first(
        where={
            'datetime_': {
                'lte': now + datetime.timedelta(hours=1),
            },
        },
        order={
            'datetime_': 'desc',
        },
    )
    assert found is not None
    assert_similar_time(found.datetime_, now + datetime.timedelta(hours=1))

    found = client.types.find_first(
        where={
            'datetime_': {
                'gt': now,
            },
        },
        order={
            'datetime_': 'asc',
        },
    )
    assert found is not None
    assert_similar_time(found.datetime_, now + datetime.timedelta(hours=1))

    found = client.types.find_first(
        where={
            'datetime_': {
                'gte': now,
            },
        },
        order={
            'datetime_': 'asc',
        },
    )
    assert found is not None
    assert_similar_time(found.datetime_, now)

    found = client.types.find_first(
        where={
            'datetime_': {
                'not': now,
            },
        },
        order={
            'datetime_': 'asc',
        },
    )
    assert found is not None
    assert_similar_time(found.datetime_, now + datetime.timedelta(hours=1))

    found = client.types.find_first(
        where={
            'datetime_': {
                'not': {
                    'equals': now,
                },
            },
        },
        order={
            'datetime_': 'asc',
        },
    )
    assert found is not None
    assert_similar_time(now + datetime.timedelta(hours=1), found.datetime_)


def test_finds(client: Prisma) -> None:
    """Adding 1 second timedelta finds the record"""
    record = client.types.create(data={})
    found = client.types.find_first(
        where={
            'datetime_': {
                'lt': record.datetime_ + datetime.timedelta(seconds=1),
            },
        },
    )
    assert found is not None
    assert found.id == record.id


def test_tz_aware(client: Prisma) -> None:
    """Modifying timezone still finds the record"""
    record = client.types.create(data={})
    found = client.types.find_first(
        where={
            'datetime_': {
                'lt': (
                    record.datetime_ + datetime.timedelta(hours=1)
                ).astimezone(datetime.timezone.max)
            }
        }
    )
    assert found is not None
    assert found.id == record.id


def test_filtering_nulls(client: Prisma) -> None:
    """None is a valid filter for nullable DateTime fields"""
    now = datetime.datetime.now(datetime.timezone.utc)
    client.types.create(
        {
            'string': 'a',
            'optional_datetime': None,
        },
    )
    client.types.create(
        {
            'string': 'b',
            'optional_datetime': now,
        },
    )
    client.types.create(
        {
            'string': 'c',
            'optional_datetime': now + datetime.timedelta(days=1),
        },
    )

    found = client.types.find_first(
        where={
            'NOT': [
                {
                    'optional_datetime': None,
                },
            ],
        },
        order={
            'string': 'asc',
        },
    )
    assert found is not None
    assert found.string == 'b'
    assert found.optional_datetime is not None
    assert_similar_time(now, found.optional_datetime)

    count = client.types.count(
        where={
            'optional_datetime': None,
        },
    )
    assert count == 1

    count = client.types.count(
        where={
            'NOT': [
                {
                    'optional_datetime': None,
                },
            ],
        },
    )
    assert count == 2


def test_precision_loss(client: Prisma) -> None:
    """https://github.com/RobertCraigie/prisma-client-py/issues/129"""
    date = datetime.datetime.utcnow()
    post = client.post.create(
        data={
            'title': 'My first post',
            'published': False,
            'created_at': date,
        },
    )
    found = client.post.find_first(
        where={
            'created_at': date,
        },
    )
    assert found is not None

    found = client.post.find_first(
        where={
            'created_at': post.created_at,
        },
    )
    assert found is not None


def test_json_schema() -> None:
    """Ensure a JSON Schema definition can be created"""
    if PYDANTIC_V2:
        assert model_json_schema(Types) == IsPartialDict(
            properties=IsPartialDict(
                {
                    'datetime_': {
                        'title': 'Datetime ',
                        'type': 'string',
                        'format': 'date-time',
                    },
                    'optional_datetime': {
                        'title': 'Optional Datetime',
                        'anyOf': [
                            {'format': 'date-time', 'type': 'string'},
                            {'type': 'null'},
                        ],
                        'default': None,
                    },
                }
            )
        )
    else:
        assert model_json_schema(Types) == IsPartialDict(
            properties=IsPartialDict(
                {
                    'datetime_': {
                        'title': 'Datetime ',
                        'type': 'string',
                        'format': 'date-time',
                    },
                    'optional_datetime': {
                        'title': 'Optional Datetime',
                        'type': 'string',
                        'format': 'date-time',
                    },
                }
            )
        )
