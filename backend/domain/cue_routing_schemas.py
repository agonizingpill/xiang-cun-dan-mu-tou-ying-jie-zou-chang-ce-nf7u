from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

Code = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]

class ShareCue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Code
    cluster: Code
    destination: Code
    route: Code


class RecordSeparate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Code
    cluster: Code
    destination: Code
    route: Code


class ConfirmOnAir(BaseModel):
    model_config = ConfigDict(extra="allow")
    code: Code | None = None
    receipt: Code | None = None
    id: Code | None = None
    routing: Code | None = None
    route_code: Code | None = None
    receipt_code: Code | None = None
    # Allows a caller to identify a receipt by destination/channel if that is
    # the vocabulary used by the handover screen.
    route: Code | None = None
    destination: Code | None = None
    status: str | None = None
    on_air: bool | None = None
    is_on_air: bool | None = None
    aired: bool | None = None

    @model_validator(mode='before')
    @classmethod
    def accept_bare_string(cls, value: Any):
        if isinstance(value, str):
            return {'code': value}
        if isinstance(value, dict):
            value = dict(value)
            if 'code' not in value:
                for source, target in (('receiptCode', 'receipt_code'), ('routeCode', 'route_code')):
                    if source in value:
                        value[target] = value[source]
            if not any(value.get(k) for k in ('code', 'receipt', 'id', 'routing',
                                              'route_code', 'receipt_code')):
                for key, item in value.items():
                    normalized = key.lower().replace('-', '_')
                    if isinstance(item, str) and ('receipt' in normalized or normalized == 'routing_code'):
                        value['receipt'] = item
                        break
        return value

    def get_receipt_code(self):
        return (self.code or self.receipt or self.id or self.routing
                or self.route_code or self.receipt_code)


class ConfirmAir(ConfirmOnAir):
    pass


class ConfirmReceipt(ConfirmOnAir):
    pass
