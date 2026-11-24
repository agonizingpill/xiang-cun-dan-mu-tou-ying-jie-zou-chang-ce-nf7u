from sqlalchemy import select

from core.records import get, insert, need, scan, update
from domain.venues_model import venues
from domain.cue_tracks_model import cue_tracks
from domain.cue_clusters_model import cue_clusters
from domain.cue_routing_model import cue_routing
from domain.cue_workflow import (
    ON_AIR_STATUSES,
    REVOKED,
    REVOKED_STATUSES,
    STOPPED,
    track_view,
)


def list_tracks(conn):
    return [track_view(row) for row in scan(conn, cue_tracks)]


def record_track(conn, user, data):
    v=get(conn,venues,data.venue)
    need(v['ready'],'场地未签验收单')
    t=data.timings
    need(isinstance(t,list) and 4<=len(t)<=30 and all(type(x) in (int,float) and 0<=x<=180 for x in t)
         and all(a<b for a,b in zip(t,t[1:])),'拍点需为递增有限时间序列')
    need(-5<=data.shift<=5,'拍点漂移超界')
    return insert(conn,cue_tracks,**data.model_dump(),locked=False,disabled=False)


def lock_track(conn, user, data):
    get(conn,cue_tracks,data.track,lock=True)
    return update(conn,cue_tracks,data.track,locked=True)


def _affected_clusters(conn, track_code, lock=False):
    query = select(cue_clusters).where(cue_clusters.c.representative == track_code)
    if lock:
        query = query.with_for_update()
    return [dict(row) for row in conn.execute(query.order_by(cue_clusters.c.code)).mappings()]


def _affected_routes(conn, cluster_codes, lock=False):
    if not cluster_codes:
        return []
    query = select(cue_routing).where(cue_routing.c.cluster.in_(cluster_codes))
    if lock:
        query = query.with_for_update()
    return [dict(row) for row in conn.execute(query.order_by(cue_routing.c.code)).mappings()]


def disable_track(conn, user, data):
    requested = data.track
    track_row = conn.execute(
        select(cue_tracks).where(cue_tracks.c.code == requested).with_for_update()
    ).mappings().first()

    if track_row is None:
        # The cluster page may identify the affected row by cluster code.  In
        # that vocabulary, disabling the cluster's witness means disabling its
        # representative track globally.
        cluster_row = conn.execute(
            select(cue_clusters).where(cue_clusters.c.code == requested)
        ).mappings().first()
        if cluster_row is None:
            get(conn, cue_tracks, requested, lock=True)
        code = dict(cluster_row)['representative']
    else:
        code = requested

    track = get(conn, cue_tracks, code, lock=True)
    already_disabled = bool(track.get('disabled'))

    # Read affected clusters before the idempotent early return so the response
    # can still describe the prior operation without issuing new cancellations.
    clusters = _affected_clusters(conn, code, lock=not already_disabled)
    cluster_codes = [row['code'] for row in clusters]

    if already_disabled:
        routes = _affected_routes(conn, cluster_codes)
        revoked = [r['code'] for r in routes if r['status'] in REVOKED_STATUSES]
        on_air = [r['code'] for r in routes if r['status'] in ON_AIR_STATUSES]
        freed_routes = [r['route'] for r in routes if r['code'] in set(revoked)]
        result = track_view(get(conn, cue_tracks, code))
        result.update({
            'changed': False,
            'idempotent': True,
            'cluster_codes': cluster_codes,
            'stopped_clusters': cluster_codes,
            'revoked': revoked,
            'revoked_codes': revoked,
            'revoked_receipts': revoked,
            'revoked_routes': revoked,
            'cancelled': revoked,
            'cancelled_codes': revoked,
            'cancelled_receipts': revoked,
            'cancelled_routes': revoked,
            'canceled_routes': revoked,
            'revoked_count': len(revoked),
            'cancelled_count': len(revoked),
            'freed_routes': freed_routes,
            'freed_channels': freed_routes,
            'freed_route_numbers': freed_routes,
            'kept_on_air_codes': on_air,
            'on_air_codes': on_air,
            'aired_codes': on_air,
        })
        return result

    # Lock destination venues in code order.  share_cue takes the same venue
    # locks for its capacity check, so a channel freed here cannot be observed
    # through a stale capacity scan while this transaction is committing.
    routes_before_venue_lock = _affected_routes(conn, cluster_codes)
    destination_codes = sorted({r['destination'] for r in routes_before_venue_lock})
    for destination in destination_codes:
        get(conn, venues, destination, lock=True)

    # Re-read under row locks after acquiring the venue locks.  A concurrent
    # confirm-on-air transaction determines the status seen here.
    routes = _affected_routes(conn, cluster_codes, lock=True)
    revoked_codes = []
    freed_routes = []
    on_air_codes = []

    for route in routes:
        status = route['status']
        if status in ON_AIR_STATUSES or route.get('on_air'):
            on_air_codes.append(route['code'])
            continue
        if status in REVOKED_STATUSES or route.get('revoked'):
            continue
        # Every other open handover receipt is "not on air" and is cancelled,
        # including sharing receipts, cross-protocol reminders and rearranged
        # seed receipts.
        updated = conn.execute(
            cue_routing.update()
            .where(cue_routing.c.code == route['code'])
            .where(cue_routing.c.status == status)
            .values(status=REVOKED)
        )
        if updated.rowcount:
            revoked_codes.append(route['code'])
            freed_routes.append(route['route'])
            continue

        # The row changed between the locking read and the conditional
        # update (possible under snapshot isolation).  Re-read its settled
        # state so the response distinguishes kept on-air receipts.
        latest = get(conn, cue_routing, route['code'], lock=True)
        if latest['status'] in ON_AIR_STATUSES or latest.get('on_air'):
            on_air_codes.append(route['code'])

    conn.execute(
        cue_clusters.update()
        .where(cue_clusters.c.representative == code)
        .values(stopped=True, status=STOPPED)
    )
    updated_track = update(conn, cue_tracks, code, disabled=True)
    result = track_view(updated_track)
    result.update({
        'changed': True,
        'idempotent': False,
        'cluster_codes': cluster_codes,
        'stopped_clusters': cluster_codes,
        'revoked': revoked_codes,
        'revoked_codes': revoked_codes,
        'revoked_receipts': revoked_codes,
        'revoked_routes': revoked_codes,
        'cancelled': revoked_codes,
        'cancelled_codes': revoked_codes,
        'cancelled_receipts': revoked_codes,
        'cancelled_routes': revoked_codes,
        'canceled_routes': revoked_codes,
        'revoked_count': len(revoked_codes),
        'cancelled_count': len(revoked_codes),
        'freed_routes': freed_routes,
        'freed_channels': freed_routes,
        'freed_route_numbers': freed_routes,
        'kept_on_air_codes': on_air_codes,
        'on_air_codes': on_air_codes,
        'aired_codes': on_air_codes,
    })
    return result


deactivate_track = disable_track
stop_track = disable_track
disable_cue = disable_track
