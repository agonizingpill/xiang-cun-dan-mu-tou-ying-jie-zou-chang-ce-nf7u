from sqlalchemy import Boolean, Column, Float, ForeignKey, JSON, String, Table, false

from core.db import metadata


cue_tracks = Table('cue_tracks', metadata,
    Column('code', String(64), primary_key=True),
    Column('venue', String(160), ForeignKey('venues.code'), nullable=False),
    Column('timings', JSON, nullable=False),
    Column('shift', Float, nullable=False),
    Column('locked', Boolean, nullable=False),
    Column('disabled', Boolean, nullable=False, server_default=false()),
)
