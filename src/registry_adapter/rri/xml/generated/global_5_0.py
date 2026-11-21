from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from registry_adapter.rri.xml.generated.contact_5_0 import (
    Check as ContactCheck,
)
from registry_adapter.rri.xml.generated.contact_5_0 import (
    Create as ContactCreate,
)
from registry_adapter.rri.xml.generated.contact_5_0 import (
    Info as ContactInfo,
)
from registry_adapter.rri.xml.generated.contact_5_0 import (
    Update as ContactUpdate,
)
from registry_adapter.rri.xml.generated.domain_5_0 import (
    Check as DomainCheck,
)
from registry_adapter.rri.xml.generated.domain_5_0 import (
    Chholder,
    Chprov,
    CreateAuthInfo1,
    CreateAuthInfo2,
    DeleteAuthInfo1,
    Restore,
    Transit,
)
from registry_adapter.rri.xml.generated.domain_5_0 import (
    Create as DomainCreate,
)
from registry_adapter.rri.xml.generated.domain_5_0 import (
    Delete as DomainDelete,
)
from registry_adapter.rri.xml.generated.domain_5_0 import (
    Info as DomainInfo,
)
from registry_adapter.rri.xml.generated.domain_5_0 import (
    Update as DomainUpdate,
)
from registry_adapter.rri.xml.generated.message_5_0 import (
    Delete as MessageDelete,
)
from registry_adapter.rri.xml.generated.message_5_0 import (
    QueueRead,
)
from registry_adapter.rri.xml.generated.regacc_5_0 import Info as RegaccInfo
from registry_adapter.rri.xml.generated.transaction_5_0 import Transaction

__NAMESPACE__ = "http://registry.denic.de/global/5.0"


@dataclass(kw_only=True)
class LoginType:
    class Meta:
        name = "loginType"

    user: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/global/5.0",
            "required": True,
        }
    )
    password: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/global/5.0",
            "required": True,
        }
    )


class LogoutType(Enum):
    VALUE = ""


@dataclass(kw_only=True)
class RequestType:
    class Meta:
        name = "requestType"

    login: None | LoginType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/global/5.0",
        },
    )
    logout: None | LogoutType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/global/5.0",
        },
    )
    create: None | ContactCreate = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    update: None | ContactUpdate = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    check: None | ContactCheck = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    info: None | ContactInfo = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    registry_denic_de_domain_5_0_create: None | DomainCreate = field(
        default=None,
        metadata={
            "name": "create",
            "type": "Element",
            "namespace": "http://registry.denic.de/domain/5.0",
        },
    )
    registry_denic_de_domain_5_0_update: None | DomainUpdate = field(
        default=None,
        metadata={
            "name": "update",
            "type": "Element",
            "namespace": "http://registry.denic.de/domain/5.0",
        },
    )
    chholder: None | Chholder = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/domain/5.0",
        },
    )
    delete: None | DomainDelete = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/domain/5.0",
        },
    )
    restore: None | Restore = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/domain/5.0",
        },
    )
    registry_denic_de_domain_5_0_check: None | DomainCheck = field(
        default=None,
        metadata={
            "name": "check",
            "type": "Element",
            "namespace": "http://registry.denic.de/domain/5.0",
        },
    )
    info_1: None | DomainInfo = field(
        default=None,
        metadata={
            "name": "info",
            "type": "Element",
            "namespace": "http://registry.denic.de/domain/5.0",
        },
    )
    chprov: None | Chprov = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/domain/5.0",
        },
    )
    transit: None | Transit = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/domain/5.0",
        },
    )
    create_auth_info1: None | CreateAuthInfo1 = field(
        default=None,
        metadata={
            "name": "createAuthInfo1",
            "type": "Element",
            "namespace": "http://registry.denic.de/domain/5.0",
        },
    )
    delete_auth_info1: None | DeleteAuthInfo1 = field(
        default=None,
        metadata={
            "name": "deleteAuthInfo1",
            "type": "Element",
            "namespace": "http://registry.denic.de/domain/5.0",
        },
    )
    create_auth_info2: None | CreateAuthInfo2 = field(
        default=None,
        metadata={
            "name": "createAuthInfo2",
            "type": "Element",
            "namespace": "http://registry.denic.de/domain/5.0",
        },
    )
    queue_read: None | QueueRead = field(
        default=None,
        metadata={
            "name": "queue-read",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    registry_denic_de_msg_5_0_delete: None | MessageDelete = field(
        default=None,
        metadata={
            "name": "delete",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    info_2: None | RegaccInfo = field(
        default=None,
        metadata={
            "name": "info",
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
        },
    )
    ctid: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/global/5.0",
            "min_length": 3,
            "max_length": 64,
        },
    )


@dataclass(kw_only=True)
class ResponseType:
    class Meta:
        name = "responseType"

    transaction: Transaction = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/transaction/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class RegistryRequest(RequestType):
    class Meta:
        name = "registry-request"
        namespace = "http://registry.denic.de/global/5.0"


@dataclass(kw_only=True)
class RegistryResponse(ResponseType):
    class Meta:
        name = "registry-response"
        namespace = "http://registry.denic.de/global/5.0"
