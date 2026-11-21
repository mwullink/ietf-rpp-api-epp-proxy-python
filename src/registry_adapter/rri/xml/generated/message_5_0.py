from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from xsdata.models.datatype import XmlDateTime

from registry_adapter.rri.xml.generated.domain_5_0 import StatusType
from registry_adapter.rri.xml.generated.transaction_5_0 import (
    MessageType as Transaction50MessageType,
)

__NAMESPACE__ = "http://registry.denic.de/msg/5.0"


@dataclass(kw_only=True)
class ContactType:
    class Meta:
        name = "contactType"

    handle: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
            "max_length": 32,
            "pattern": r"[dD][eE][nN][iI][cC]\-[1-9][0-9]*\-[\-\.a-zA-Z0-9]+",
        }
    )


@dataclass(kw_only=True)
class ContactsType:
    class Meta:
        name = "contactsType"

    handle: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "min_occurs": 1,
            "max_occurs": 100,
            "max_length": 32,
            "pattern": r"[dD][eE][nN][iI][cC]\-[1-9][0-9]*\-[\-\.a-zA-Z0-9]+",
        },
    )


@dataclass(kw_only=True)
class DomainType:
    class Meta:
        name = "domainType"

    handle: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
            "min_length": 4,
            "max_length": 66,
            "pattern": r"[\p{IsBasicLatin}\p{IsLatin-1Supplement}\p{IsLatinExtended-A}]*",
        }
    )
    ace: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
            "min_length": 1,
            "max_length": 254,
            "pattern": r"[0-9a-zA-Z][0-9a-zA-Z\-]{0,62}\.[dD][eE]",
        }
    )


@dataclass(kw_only=True)
class DomainWithExpireType:
    class Meta:
        name = "domainWithExpireType"

    handle: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
            "min_length": 4,
            "max_length": 66,
            "pattern": r"[\p{IsBasicLatin}\p{IsLatin-1Supplement}\p{IsLatinExtended-A}]*",
        }
    )
    ace: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
            "min_length": 1,
            "max_length": 254,
            "pattern": r"[0-9a-zA-Z][0-9a-zA-Z\-]{0,62}\.[dD][eE]",
        }
    )
    expire: XmlDateTime = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )


class EmptyType(Enum):
    VALUE = ""


class MsgTypeType(Enum):
    EXPIRE_WARNING = "expireWarning"
    EXPIRE = "expire"
    AUTH_INFO_EXPIRE = "authInfoExpire"
    AUTH_INFO2_NOTIFY = "authInfo2Notify"
    CHPROV_AUTH_INFO = "chprovAuthInfo"
    DOMAIN_DELETE = "domainDelete"
    AUTH_INFO2_DELETE = "authInfo2Delete"
    LOCK_CREATE = "lockCreate"
    LOCK_DELETE = "lockDelete"
    DOMAIN_UPDATE = "domainUpdate"
    DOMAIN_TRANSIT = "domainTransit"
    CONTACT_UPDATE = "contactUpdate"
    CONTACT_DELETE = "contactDelete"
    DOMAIN_STATUS_UPDATE = "domainStatusUpdate"
    CONTACT_VERIFICATION_REQUIRED = "contactVerificationRequired"


@dataclass(kw_only=True)
class VerifiedClaimsType:
    class Meta:
        name = "verifiedClaimsType"

    claim: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "min_occurs": 1,
        },
    )


@dataclass(kw_only=True)
class AuthInfo2DeleteType:
    class Meta:
        name = "authInfo2DeleteType"

    domain: DomainType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    message: list[Transaction50MessageType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "min_occurs": 1,
        },
    )


@dataclass(kw_only=True)
class AuthInfo2NotifyType:
    class Meta:
        name = "authInfo2NotifyType"

    domain: DomainType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class AuthInfoExpireType:
    class Meta:
        name = "authInfoExpireType"

    domain: DomainType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    authinfoexpire: XmlDateTime = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class ChprovAuthInfoType:
    class Meta:
        name = "chprovAuthInfoType"

    domain: DomainType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    new: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    old: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class ContactUpdateType:
    class Meta:
        name = "contactUpdateType"

    contact: ContactType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    message: list[Transaction50MessageType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "min_occurs": 1,
        },
    )


@dataclass(kw_only=True)
class ContactsDeleteType:
    class Meta:
        name = "contactsDeleteType"

    handles: ContactsType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class DeleteType:
    class Meta:
        name = "deleteType"

    value: EmptyType = field(
        metadata={
            "required": True,
        }
    )
    msgid: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "min_length": 3,
            "max_length": 64,
        }
    )
    msg_type: None | MsgTypeType = field(
        default=None,
        metadata={
            "name": "msgType",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class DomainDeleteType:
    class Meta:
        name = "domainDeleteType"

    domain: DomainType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    message: list[Transaction50MessageType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "min_occurs": 1,
        },
    )


@dataclass(kw_only=True)
class DomainStatusUpdateType:
    class Meta:
        name = "domainStatusUpdateType"

    domain: DomainType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    holders: ContactsType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    status: StatusType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    verification_deadline_before_dedelegation: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "verificationDeadlineBeforeDedelegation",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    verification_deadline_before_deletion: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "verificationDeadlineBeforeDeletion",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    message: list[Transaction50MessageType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )


@dataclass(kw_only=True)
class DomainTransitType:
    class Meta:
        name = "domainTransitType"

    domain: DomainType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    message: list[Transaction50MessageType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "min_occurs": 1,
        },
    )


@dataclass(kw_only=True)
class DomainUpdateType:
    class Meta:
        name = "domainUpdateType"

    domain: DomainType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    message: list[Transaction50MessageType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "min_occurs": 1,
        },
    )


@dataclass(kw_only=True)
class DomainWithExpireListType:
    class Meta:
        name = "domainWithExpireListType"

    domain: list[DomainWithExpireType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "min_occurs": 1,
        },
    )


@dataclass(kw_only=True)
class EarliestDomainBeforeDedelegationType:
    class Meta:
        name = "earliestDomainBeforeDedelegationType"

    domain: DomainType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    verification_deadline: XmlDateTime = field(
        metadata={
            "name": "verificationDeadline",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class EarliestDomainBeforeDeletionType:
    class Meta:
        name = "earliestDomainBeforeDeletionType"

    domain: DomainType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    verification_deadline: XmlDateTime = field(
        metadata={
            "name": "verificationDeadline",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class LockCreateType:
    class Meta:
        name = "lockCreateType"

    domain: DomainType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    message: list[Transaction50MessageType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "min_occurs": 1,
        },
    )


@dataclass(kw_only=True)
class LockDeleteType:
    class Meta:
        name = "lockDeleteType"

    domain: DomainType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    message: list[Transaction50MessageType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "min_occurs": 1,
        },
    )


@dataclass(kw_only=True)
class ReadType:
    class Meta:
        name = "readType"

    value: EmptyType = field(
        metadata={
            "required": True,
        }
    )
    msg_type: None | MsgTypeType = field(
        default=None,
        metadata={
            "name": "msgType",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class ContactDelete(ContactsDeleteType):
    class Meta:
        name = "contactDelete"
        namespace = "http://registry.denic.de/msg/5.0"


@dataclass(kw_only=True)
class ContactVerificationRequiredType:
    class Meta:
        name = "contactVerificationRequiredType"

    handle: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
            "max_length": 32,
            "pattern": r"[dD][eE][nN][iI][cC]\-[1-9][0-9]*\-[\-\.a-zA-Z0-9]+",
        }
    )
    verification_claims: VerifiedClaimsType = field(
        metadata={
            "name": "verificationClaims",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    number_of_referenced_domains_total: int = field(
        metadata={
            "name": "numberOfReferencedDomainsTotal",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    earliest_domain_for_dedelegation: (
        None | EarliestDomainBeforeDedelegationType
    ) = field(
        default=None,
        metadata={
            "name": "earliestDomainForDedelegation",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    earliest_domain_for_deletion: EarliestDomainBeforeDeletionType = field(
        metadata={
            "name": "earliestDomainForDeletion",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "required": True,
        }
    )
    message: list[Transaction50MessageType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
            "min_occurs": 1,
        },
    )


@dataclass(kw_only=True)
class Delete(DeleteType):
    class Meta:
        name = "delete"
        namespace = "http://registry.denic.de/msg/5.0"


@dataclass(kw_only=True)
class QueueRead(ReadType):
    class Meta:
        name = "queue-read"
        namespace = "http://registry.denic.de/msg/5.0"


@dataclass(kw_only=True)
class MessageType:
    class Meta:
        name = "messageType"

    expire_warning: None | DomainWithExpireListType = field(
        default=None,
        metadata={
            "name": "expireWarning",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    expire: None | DomainWithExpireListType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    auth_info_expire: None | AuthInfoExpireType = field(
        default=None,
        metadata={
            "name": "authInfoExpire",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    auth_info2_notify: None | AuthInfo2NotifyType = field(
        default=None,
        metadata={
            "name": "authInfo2Notify",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    chprov_auth_info: None | ChprovAuthInfoType = field(
        default=None,
        metadata={
            "name": "chprovAuthInfo",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    domain_delete: None | DomainDeleteType = field(
        default=None,
        metadata={
            "name": "domainDelete",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    auth_info2_delete: None | AuthInfo2DeleteType = field(
        default=None,
        metadata={
            "name": "authInfo2Delete",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    lock_create: None | LockCreateType = field(
        default=None,
        metadata={
            "name": "lockCreate",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    lock_delete: None | LockDeleteType = field(
        default=None,
        metadata={
            "name": "lockDelete",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    domain_update: None | DomainUpdateType = field(
        default=None,
        metadata={
            "name": "domainUpdate",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    domain_transit: None | DomainTransitType = field(
        default=None,
        metadata={
            "name": "domainTransit",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    contact_update: None | ContactUpdateType = field(
        default=None,
        metadata={
            "name": "contactUpdate",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    contact_delete: None | ContactsDeleteType = field(
        default=None,
        metadata={
            "name": "contactDelete",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    domain_status_update: None | DomainStatusUpdateType = field(
        default=None,
        metadata={
            "name": "domainStatusUpdate",
            "type": "Element",
            "namespace": "http://registry.denic.de/msg/5.0",
        },
    )
    contact_verification_required: None | ContactVerificationRequiredType = (
        field(
            default=None,
            metadata={
                "name": "contactVerificationRequired",
                "type": "Element",
                "namespace": "http://registry.denic.de/msg/5.0",
            },
        )
    )
    msgid: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "min_length": 3,
            "max_length": 64,
        }
    )
    msgcnt: None | int = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    msgtime: XmlDateTime = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class Message(MessageType):
    class Meta:
        name = "message"
        namespace = "http://registry.denic.de/msg/5.0"
