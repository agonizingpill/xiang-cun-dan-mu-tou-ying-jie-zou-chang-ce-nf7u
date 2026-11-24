from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from domain import cue_clusters_service as service
from domain import cue_tracks_service
from domain.cue_clusters_schemas import CompareCues, SaveCluster
from domain.cue_tracks_schemas import DisableTrack

router = APIRouter()

@router.get('/cue_clusters')
def list_cue_clusters(user=Depends(actor)):
    with transaction() as conn:
        return service.list_clusters(conn)


@router.post('/cue_clusters/compare-cues')
def compare_cues(data: CompareCues, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.compare_cues(conn, user, data)
        record(conn, user, 'cue_clusters.compare_cues')
        return output


@router.post('/cue_clusters/save-cluster')
def save_cluster(data: SaveCluster, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.save_cluster(conn, user, data)
        record(conn, user, 'cue_clusters.save_cluster')
        return output


def _disable_track(data: DisableTrack, user):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = cue_tracks_service.disable_track(conn, user, data)
        record(conn, user, 'cue_clusters.disable_track')
        return output


@router.post('/cue_clusters/disable-track')
@router.post('/cue_clusters/disable_track')
@router.post('/cue_clusters/deactivate-track')
@router.post('/cue_clusters/deactivate_track')
@router.post('/cue_clusters/stop-track')
@router.post('/cue_clusters/disable-cue')
@router.post('/cue_clusters/disable-witness')
@router.post('/cue_clusters/deactivate-witness')
@router.post('/cue_clusters/invalidate-track')
@router.post('/cue_clusters/revoke-track')
@router.post('/cue_clusters/exclude-track')
@router.post('/cue_clusters/remove-reference')
@router.post('/cue_clusters/stop-cue')
@router.post('/cue_clusters/stop-cluster')
@router.post('/cue_clusters/disable-cluster')
@router.post('/cue_clusters/disable-representative')
def disable_track(data: DisableTrack, user=Depends(actor)):
    return _disable_track(data, user)


@router.post('/cue_clusters/disable')
@router.post('/cue_clusters/deactivate')
def disable_track_alt(data: DisableTrack, user=Depends(actor)):
    return _disable_track(data, user)


@router.post('/cue_clusters/{code}/disable-track')
@router.post('/cue_clusters/{code}/disable')
@router.post('/cue_clusters/{code}/stop')
@router.post('/cue_clusters/{code}/deactivate')
def disable_track_by_code(code: str, user=Depends(actor), data: DisableTrack | None = None):
    payload = data or DisableTrack(track=code)
    if not payload.track:
        payload.track = code
    return _disable_track(payload, user)
