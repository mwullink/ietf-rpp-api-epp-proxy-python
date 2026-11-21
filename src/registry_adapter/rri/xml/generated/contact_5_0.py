from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from xsdata.models.datatype import XmlDateTime

from registry_adapter.rri.xml.generated.verification_5_0 import (
    VerificationInformation,
)

__NAMESPACE__ = "http://registry.denic.de/contact/5.0"


@dataclass(kw_only=True)
class CheckInfoType:
    class Meta:
        name = "checkInfoType"

    handle: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "max_length": 32,
            "pattern": r"[dD][eE][nN][iI][cC]\-[1-9][0-9]*\-[\-\.a-zA-Z0-9]+",
        },
    )


@dataclass(kw_only=True)
class Handle:
    class Meta:
        name = "handle"
        namespace = "http://registry.denic.de/contact/5.0"

    value: str = field(
        default="",
        metadata={
            "required": True,
            "max_length": 32,
            "pattern": r"[dD][eE][nN][iI][cC]\-[1-9][0-9]*\-[\-\.a-zA-Z0-9]+",
        },
    )


@dataclass(kw_only=True)
class NormalizedStringPrivacyType:
    class Meta:
        name = "normalizedStringPrivacyType"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )


class RoleType(Enum):
    HOLDER = "holder"
    GENERALREQUEST = "generalrequest"
    ABUSECONTACT = "abusecontact"


class StatusType(Enum):
    FREE = "free"
    EXIST = "exist"
    INVALID = "invalid"


@dataclass(kw_only=True)
class TokenPrivacyType:
    class Meta:
        name = "tokenPrivacyType"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )


@dataclass(kw_only=True)
class AddressType(NormalizedStringPrivacyType):
    class Meta:
        name = "addressType"


@dataclass(kw_only=True)
class Check(CheckInfoType):
    class Meta:
        name = "check"
        namespace = "http://registry.denic.de/contact/5.0"


@dataclass(kw_only=True)
class CheckDataType:
    class Meta:
        name = "checkDataType"

    handle: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
            "max_length": 32,
            "pattern": r"[dD][eE][nN][iI][cC]\-[1-9][0-9]*\-[\-\.a-zA-Z0-9]+",
        }
    )
    status: StatusType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CityType(NormalizedStringPrivacyType):
    class Meta:
        name = "cityType"


@dataclass(kw_only=True)
class CountryCodeType(TokenPrivacyType):
    class Meta:
        name = "countryCodeType"


@dataclass(kw_only=True)
class EmailType(TokenPrivacyType):
    class Meta:
        name = "emailType"


@dataclass(kw_only=True)
class Info(CheckInfoType):
    class Meta:
        name = "info"
        namespace = "http://registry.denic.de/contact/5.0"


@dataclass(kw_only=True)
class NameType(NormalizedStringPrivacyType):
    class Meta:
        name = "nameType"


@dataclass(kw_only=True)
class OrganisationType(NormalizedStringPrivacyType):
    class Meta:
        name = "organisationType"


@dataclass(kw_only=True)
class PhoneType(NormalizedStringPrivacyType):
    class Meta:
        name = "phoneType"


@dataclass(kw_only=True)
class PostalCodeType(TokenPrivacyType):
    class Meta:
        name = "postalCodeType"


@dataclass(kw_only=True)
class TypeType(TokenPrivacyType):
    class Meta:
        name = "typeType"


@dataclass(kw_only=True)
class UriTemplateType(NormalizedStringPrivacyType):
    class Meta:
        name = "uriTemplateType"


@dataclass(kw_only=True)
class CheckData(CheckDataType):
    class Meta:
        name = "checkData"
        namespace = "http://registry.denic.de/contact/5.0"


@dataclass(kw_only=True)
class NillablePostalType:
    class Meta:
        name = "nillablePostalType"

    address: list[AddressType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "min_occurs": 1,
        },
    )
    postal_code: PostalCodeType = field(
        metadata={
            "name": "postalCode",
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
        }
    )
    city: CityType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
        }
    )
    country_code: CountryCodeType = field(
        metadata={
            "name": "countryCode",
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class PostalType:
    class Meta:
        name = "postalType"

    address: list[AddressType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "min_occurs": 1,
        },
    )
    postal_code: PostalCodeType = field(
        metadata={
            "name": "postalCode",
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
        }
    )
    city: CityType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
        }
    )
    country_code: CountryCodeType = field(
        metadata={
            "name": "countryCode",
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CreateType:
    class Meta:
        name = "createType"

    handle: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
            "max_length": 32,
            "pattern": r"[dD][eE][nN][iI][cC]\-[1-9][0-9]*\-[\-\.a-zA-Z0-9]+",
        }
    )
    type_value: TypeType = field(
        metadata={
            "name": "type",
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
        }
    )
    name: None | NameType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    organisation: list[OrganisationType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    postal: None | PostalType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    email: list[EmailType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    phone: None | PhoneType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    uri_template: None | UriTemplateType = field(
        default=None,
        metadata={
            "name": "uri-template",
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    verification_information: list[VerificationInformation] = field(
        default_factory=list,
        metadata={
            "name": "verificationInformation",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
            "max_occurs": 5,
        },
    )


@dataclass(kw_only=True)
class InfoDataType:
    class Meta:
        name = "infoDataType"

    handle: Handle = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
        }
    )
    type_value: TypeType = field(
        metadata={
            "name": "type",
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
        }
    )
    name: None | NameType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    organisation: list[OrganisationType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    postal: None | NillablePostalType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    email: list[EmailType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    phone: None | PhoneType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    dispute_reference: None | bool = field(
        default=None,
        metadata={
            "name": "disputeReference",
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    uri_template: None | UriTemplateType = field(
        default=None,
        metadata={
            "name": "uri-template",
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    changed: None | XmlDateTime = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    verification_information: list[VerificationInformation] = field(
        default_factory=list,
        metadata={
            "name": "verificationInformation",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
            "max_occurs": 5,
        },
    )


@dataclass(kw_only=True)
class UpdateType:
    class Meta:
        name = "updateType"

    handle: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
            "max_length": 32,
            "pattern": r"[dD][eE][nN][iI][cC]\-[1-9][0-9]*\-[\-\.a-zA-Z0-9]+",
        }
    )
    type_value: TypeType = field(
        metadata={
            "name": "type",
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
            "required": True,
        }
    )
    name: None | NameType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    organisation: list[OrganisationType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    postal: None | PostalType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    email: list[EmailType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    phone: None | PhoneType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    uri_template: None | UriTemplateType = field(
        default=None,
        metadata={
            "name": "uri-template",
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    verification_information: list[VerificationInformation] = field(
        default_factory=list,
        metadata={
            "name": "verificationInformation",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
            "max_occurs": 5,
        },
    )


@dataclass(kw_only=True)
class Create(CreateType):
    class Meta:
        name = "create"
        namespace = "http://registry.denic.de/contact/5.0"


@dataclass(kw_only=True)
class InfoData(InfoDataType):
    class Meta:
        name = "infoData"
        namespace = "http://registry.denic.de/contact/5.0"


@dataclass(kw_only=True)
class Update(UpdateType):
    class Meta:
        name = "update"
        namespace = "http://registry.denic.de/contact/5.0"
