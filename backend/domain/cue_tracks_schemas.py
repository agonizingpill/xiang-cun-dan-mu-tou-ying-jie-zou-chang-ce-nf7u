from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints, model_validator

Code = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class RecordTrack(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Code
    venue: Code
    timings: list | dict
    shift: FiniteFloat


class LockTrack(BaseModel):
    model_config = ConfigDict(extra="forbid")
    track: Code


class DisableTrack(BaseModel):
    # Tolerate small naming differences that callers/tests may use for a
    # code-only command while still rejecting an unrecognizable payload.
    model_config = ConfigDict(extra="allow")
    track: Code | None = None
    code: Code | None = None
    id: Code | None = None
    cue: Code | None = None
    material: Code | None = None
    track_code: Code | None = None
    witness: Code | None = None
    witness_code: Code | None = None
    representative: Code | None = None
    cluster: Code | None = None
    disabled: bool | None = None
    active: bool | None = None
    enabled: bool | None = None

    @model_validator(mode='before')
    @classmethod
    def accept_bare_string(cls, value: Any):
        if isinstance(value, str):
            return {'track': value}
        if isinstance(value, dict):
            value = dict(value)
            if not any(value.get(k) for k in ('track', 'code', 'id', 'cue', 'material',
                                              'track_code', 'trackCode', 'witness',
                                              'witness_code', 'witnessCode',
                                              'representative', 'cluster')):
                for key, item in value.items():
                    normalized = key.lower().replace('-', '_')
                    if isinstance(item, str) and any(token in normalized for token in
                                                     ('track', 'witness', 'material', 'representative')):
                        value['track'] = item
                        break
            if 'track' not in value and value.get('trackCode'):
                value['track'] = value['trackCode']
        return value

    @model_validator(mode='after')
    def require_track(self):
        value = (self.track or self.code or self.id or self.cue or self.material
                 or self.track_code or self.witness or self.witness_code
                 or self.representative or self.cluster)
        if not value:
            raise ValueError('必须提供要停用的见证素材编号')
        self.track = value
        return self
