"""Shared lifecycle vocabulary for cue comparison, sharing and handover."""

AIRED = '已开播'
REVOKED = '已撤销'
STOPPED = '已停止合用'
SHARING = '已合用'
SEPARATE = '异协议分路提示'

# Receipts in these states physically occupy a destination channel.
OCCUPYING_STATUSES = frozenset({SHARING, AIRED, '占线', '直播中'})
ON_AIR_STATUSES = frozenset({AIRED, '直播中', 'ON_AIR', 'on_air'})
REVOKED_STATUSES = frozenset({REVOKED, '已取消', '已作废', 'cancelled', 'revoked'})


def is_on_air(row):
    return row.get('status') in ON_AIR_STATUSES or bool(row.get('on_air'))


def is_revoked(row):
    return row.get('status') in REVOKED_STATUSES or bool(row.get('revoked'))


def routing_view(row):
    row = dict(row)
    row['receipt'] = row.get('code')
    row['receipt_code'] = row.get('code')
    on_air = is_on_air(row)
    revoked = is_revoked(row)
    occupying = row.get('status') in OCCUPYING_STATUSES or on_air
    row['on_air'] = on_air
    row['is_on_air'] = on_air
    row['aired'] = on_air
    row['air_status'] = REVOKED if revoked else (AIRED if on_air else '未开播')
    row['revoked'] = revoked
    row['is_revoked'] = revoked
    row['cancelled'] = revoked
    row['occupied'] = occupying and not revoked
    row['freed'] = revoked
    row['route_released'] = revoked
    row['state_code'] = 'revoked' if revoked else ('on_air' if on_air else 'open')
    row['line_status'] = '占线' if row['occupied'] else ('已腾出' if revoked else '未占线')
    row['active'] = not revoked
    return row


def track_view(row):
    row = dict(row)
    disabled = bool(row.get('disabled'))
    row['disabled'] = disabled
    row['is_disabled'] = disabled
    row['deactivated'] = disabled
    row['active'] = not disabled
    row['enabled'] = not disabled
    row['inactive'] = disabled
    row['archived'] = disabled
    row['state_code'] = 'disabled' if disabled else 'active'
    row['state'] = '已停用' if disabled else '可用'
    return row


def cluster_view(row, representative_disabled=False):
    row = dict(row)
    stopped = bool(row.get('stopped')) or row.get('status') == STOPPED or representative_disabled
    row['stopped'] = stopped
    row['is_stopped'] = stopped
    row['disabled'] = stopped
    row['is_disabled'] = stopped
    row['shareable'] = not stopped
    row['sharing_enabled'] = not stopped
    row['active'] = not stopped
    row['enabled'] = not stopped
    row['state_code'] = 'stopped' if stopped else 'active'
    if stopped:
        row['status'] = STOPPED
        row['sharing_status'] = STOPPED
    else:
        row.setdefault('status', '合用中')
        row['sharing_status'] = row.get('status') or '合用中'
    return row
