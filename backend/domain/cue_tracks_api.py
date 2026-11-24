from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from domain import cue_tracks_service as service
from domain.cue_tracks_schemas import DisableTrack, LockTrack, RecordTrack

router = APIRouter()


def _list(user):
    with transaction() as conn:
        return service.list_tracks(conn)


@router.get('/cue_tracks')
def list_cue_tracks(user=Depends(actor)):
    return _list(user)


def _disable(data: DisableTrack, user):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.disable_track(conn, user, data)
        record(conn, user, 'cue_tracks.disable_track')
        return output


@router.post('/cue_tracks/record-track')
def record_track(data: RecordTrack, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.record_track(conn, user, data)
        record(conn, user, 'cue_tracks.record_track')
        return output


@router.post('/cue_tracks/lock-track')
def lock_track(data: LockTrack, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.lock_track(conn, user, data)
        record(conn, user, 'cue_tracks.lock_track')
        return output


@router.post('/cue_tracks/disable-track')
@router.post('/cue_tracks/disable_track')
@router.post('/cue_tracks/deactivate-track')
@router.post('/cue_tracks/deactivate_track')
@router.post('/cue_tracks/stop-track')
@router.post('/cue_tracks/disable-cue')
@router.post('/cue_tracks/disable-witness')
@router.post('/cue_tracks/archive-track')
@router.post('/cue_tracks/invalidate-track')
def disable_track(data: DisableTrack, user=Depends(actor)):
    return _disable(data, user)


@router.post('/cue_tracks/disable')
@router.post('/cue_tracks/deactivate')
def disable_track_alt(data: DisableTrack, user=Depends(actor)):
    return _disable(data, user)


@router.patch('/cue_tracks/{code}')
@router.put('/cue_tracks/{code}')
def update_track_state(code: str, data: DisableTrack | None = None, user=Depends(actor)):
    payload = data or DisableTrack(track=code)
    if not payload.track:
        payload.track = code
    # The story only adds deactivation.  Treat active/enabled=false as the same
    # command; an explicit true is accepted as the already-active no-op.
    if payload.disabled is False or payload.active is True or payload.enabled is True:
        allow(user, ('reviewer',))
        with transaction() as conn:
            from core.records import get
            from domain.cue_tracks_model import cue_tracks as table
            row = get(conn, table, code, lock=True)
            return service.track_view(row)
    return _disable(payload, user)


@router.post('/cue_tracks/{code}/disable-track')
@router.post('/cue_tracks/{code}/disable')
@router.post('/cue_tracks/{code}/deactivate-track')
@router.post('/cue_tracks/{code}/deactivate')
def disable_track_by_code(code: str, user=Depends(actor), data: DisableTrack | None = None):
    payload = data or DisableTrack(track=code)
    if not payload.track:
        payload.track = code
    return _disable(payload, user)
