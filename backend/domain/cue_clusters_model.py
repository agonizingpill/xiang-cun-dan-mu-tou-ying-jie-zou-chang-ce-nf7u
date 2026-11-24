from sqlalchemy import Boolean, Column, Float, ForeignKey, JSON, String, Table, false

from core.db import metadata


cue_clusters = Table('cue_clusters', metadata,
    Column('code', String(64), primary_key=True),
    Column('track', String(160), ForeignKey('cue_tracks.code'), nullable=False),
    Column('representative', String(160), ForeignKey('cue_tracks.code'), nullable=False),
    Column('distance', Float, nullable=False),
    Column('members', JSON, nullable=False),
    Column('token', String(64), nullable=False, unique=True),
    Column('stopped', Boolean, nullable=False, server_default=false()),
    Column('status', String(32), nullable=False, server_default='合用中'),
)
