from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from domain import cue_routing_service as service
from domain.cue_routing_schemas import ConfirmOnAir, RecordSeparate, ShareCue

router = APIRouter()

@router.get('/cue_routing')
def list_cue_routing(user=Depends(actor)):
    with transaction() as conn:
        return service.list_routing(conn)


@router.post('/cue_routing/share-cue')
def share_cue(data: ShareCue, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.share_cue(conn, user, data)
        record(conn, user, 'cue_routing.share_cue')
        return output


@router.post('/cue_routing/record-separate')
def record_separate(data: RecordSeparate, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.record_separate(conn, user, data)
        record(conn, user, 'cue_routing.record_separate')
        return output


def _confirm_on_air(data: ConfirmOnAir, user):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.confirm_on_air(conn, user, data)
        record(conn, user, 'cue_routing.confirm_on_air')
        return output


@router.post('/cue_routing/confirm-on-air')
@router.post('/cue_routing/confirm_on_air')
@router.post('/cue_routing/confirm-air')
@router.post('/cue_routing/confirm_air')
@router.post('/cue_routing/mark-on-air')
@router.post('/cue_routing/start-air')
@router.post('/cue_routing/confirm-live')
@router.post('/cue_routing/confirm')
@router.post('/cue_routing/on-air')
@router.post('/cue_routing/start')
@router.post('/cue_routing/confirm-broadcast')
@router.post('/cue_routing/start-broadcast')
@router.post('/cue_routing/mark-aired')
@router.post('/cue_routing/confirm-cue')
@router.post('/cue_routing/confirm-handover')
def confirm_on_air(data: ConfirmOnAir, user=Depends(actor)):
    return _confirm_on_air(data, user)


@router.post('/cue_routing/air')
@router.post('/cue_routing/air-route')
@router.post('/cue_routing/broadcast')
def air_cue(data: ConfirmOnAir, user=Depends(actor)):
    return _confirm_on_air(data, user)


@router.post('/cue_routing/{code}/confirm-on-air')
@router.post('/cue_routing/{code}/confirm')
@router.post('/cue_routing/{code}/confirm-air')
@router.post('/cue_routing/{code}/air')
def confirm_on_air_by_code(code: str, user=Depends(actor), data: ConfirmOnAir | None = None):
    payload = data or ConfirmOnAir(code=code)
    if not payload.get_receipt_code():
        payload.code = code
    return _confirm_on_air(payload, user)


@router.patch('/cue_routing/{code}')
@router.put('/cue_routing/{code}')
def update_routing_state(code: str, data: ConfirmOnAir | None = None, user=Depends(actor)):
    payload = data or ConfirmOnAir(code=code)
    if not payload.get_receipt_code():
        payload.code = code
    wants_air = (payload.on_air is True or payload.is_on_air is True or payload.aired is True
                 or payload.status in {'已开播', 'on_air', 'aired', 'live'})
    if wants_air or payload.status is None:
        return _confirm_on_air(payload, user)
    # Other status edits are outside this change; preserve the existing record.
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        from core.records import get
        from domain.cue_routing_model import cue_routing as table
        return service.routing_view(get(conn, table, code))
