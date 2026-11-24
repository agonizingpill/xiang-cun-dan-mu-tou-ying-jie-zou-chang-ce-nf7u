from sqlalchemy import select

from core.records import get, insert, need, scan
from domain.venues_model import venues
from domain.cue_tracks_model import cue_tracks
from domain.cue_clusters_model import cue_clusters
from domain.cue_routing_model import cue_routing
from domain.cue_workflow import (
    AIRED,
    OCCUPYING_STATUSES,
    REVOKED,
    REVOKED_STATUSES,
    STOPPED,
    routing_view,
)


def list_routing(conn):
    return [routing_view(row) for row in scan(conn, cue_routing)]


def share_cue(conn, user, data):
    group=get(conn,cue_clusters,data.cluster)
    origin=get(conn,cue_tracks,group['track'])['venue']

    # Follow disable_track's lock order: representative track, cluster, then
    # venue.  Re-read the cluster after its lock to get the committed state.
    representative = get(conn, cue_tracks, group['representative'], lock=True)
    need(not representative.get('disabled'),'该簇样板素材已停用，节奏簇停止合用')
    locked_group = get(conn, cue_clusters, data.cluster, lock=True)
    need(not locked_group.get('stopped') and locked_group.get('status') != STOPPED,
         '该节奏簇已停止合用')

    venues_by_key={x:get(conn,venues,x,lock=True) for x in sorted({origin,data.destination})}
    target=venues_by_key[data.destination]
    need(target['ready'],'目标场地尚未签验收单')
    need(target['protocol']==venues_by_key[origin]['protocol'],'两场计量协议不同，须登记独立分路提示')
    need(len(data.route)<=7,'分路编号超界')
    used=[x for x in scan(conn,cue_routing)
          if x['destination']==target['code']
          and (x['status'] in OCCUPYING_STATUSES)
          and x['status'] not in REVOKED_STATUSES]
    need(len(used)<target['channels'] and not any(x['route']==data.route for x in used),'目标分路已被占')
    return insert(conn,cue_routing,**data.model_dump(),status='已合用')


def record_separate(conn, user, data):
    group=get(conn,cue_clusters,data.cluster)
    source=get(conn,venues,get(conn,cue_tracks,group['track'])['venue'])
    target=get(conn,venues,data.destination)
    need(source['protocol']!=target['protocol'],'同协议可直接用合用签回')
    return insert(conn,cue_routing,**data.model_dump(),status='异协议分路提示')


def _find_by_channel(conn, destination, route):
    rows = conn.execute(
        select(cue_routing)
        .where(cue_routing.c.destination == destination, cue_routing.c.route == route)
        .order_by(cue_routing.c.code.desc())
    ).mappings().all()
    need(rows, '找不到对应分路回单')
    return dict(rows[0])['code']


def confirm_on_air(conn, user, data):
    code = data.get_receipt_code()
    if code is None and data.route:
        # Some callers use the field name "route" for the receipt code.  If it
        # is a primary key, prefer that; otherwise treat it as a physical
        # channel and require destination for the lookup below.
        existing_code = conn.scalar(select(cue_routing.c.code).where(cue_routing.c.code == data.route))
        if existing_code:
            code = existing_code
    if code is None:
        need(data.destination and data.route, '必须提供回单编号或目标场地与分路')
        code = _find_by_channel(conn, data.destination, data.route)

    row = get(conn, cue_routing, code, lock=True)
    if row['status'] in {'已开播', '直播中'}:
        return routing_view(row)
    need(row['status'] not in REVOKED_STATUSES, '回单已撤销，不能确认开播')

    # Conditional transition is the concurrency guard.  If disable commits
    # first, the row is 已撤销 and rowcount is zero; if this commits first,
    # disable's conditional cancellation no longer matches an open status.
    result = conn.execute(
        cue_routing.update()
        .where(cue_routing.c.code == code)
        .where(cue_routing.c.status == row['status'])
        .where(cue_routing.c.status.notin_(tuple(REVOKED_STATUSES | {'已开播', '直播中'})))
        .values(status=AIRED)
    )
    need(result.rowcount == 1, '回单状态已被其他提交改变，请刷新后重试')
    return routing_view(get(conn, cue_routing, code))


confirm_air = confirm_on_air
mark_on_air = confirm_on_air
air_cue = confirm_on_air
