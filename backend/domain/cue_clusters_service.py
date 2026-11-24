from core.queueing import result, submit
from core.records import get, insert, need, scan
from domain import cue_tracks_service
from domain.cue_tracks_model import cue_tracks
from domain.cue_clusters_model import cue_clusters
from domain.cue_workflow import STOPPED, cluster_view


def list_clusters(conn):
    tracks = {row['code']: row for row in scan(conn, cue_tracks)}
    rows = []
    for row in scan(conn, cue_clusters):
        representative = tracks.get(row['representative'], {})
        rows.append(cluster_view(row, bool(representative.get('disabled'))))
    return rows


def compare_cues(conn, user, data):
    q=get(conn,cue_tracks,data.track)
    need(not q.get('disabled'),'该见证素材已停用，不能发起新比较')
    ref=[x for x in scan(conn,cue_tracks)
         if x['locked'] and not x.get('disabled') and x['code']!=data.track]
    need(8<=len(ref)<=200,'需要已确认素材及足够参考片段')
    return submit(user,{'track':q,'references':ref})


def save_cluster(conn, user, data):
    run=result(user,data.token); stats=run['result']
    representative = stats['representative']
    # Lock the representative before checking disabled state.  This pairs with
    # disable_track's track -> cluster lock order and makes simultaneous
    # sign/disable submissions settle in commit order.
    rep = get(conn, cue_tracks, representative, lock=True)
    need(not rep.get('disabled'),'该结果以已停用素材为样板，不能签认')
    return insert(conn,cue_clusters,code=data.code,track=run['input']['track']['code'],
      representative=representative,distance=stats['distance'],members=stats['members'],token=data.token,
      stopped=False,status='合用中')


def disable_track(conn, user, data):
    return cue_tracks_service.disable_track(conn, user, data)


deactivate_track = disable_track
disable_cue = disable_track
deactivate_cue = disable_track
