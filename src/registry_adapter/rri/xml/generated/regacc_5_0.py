from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDateTime

from registry_adapter.rri.xml.generated.contact_5_0 import (
    EmailType as Contact50EmailType,
)
from registry_adapter.rri.xml.generated.contact_5_0 import (
    NameType as Contact50NameType,
)
from registry_adapter.rri.xml.generated.contact_5_0 import (
    NillablePostalType,
    OrganisationType,
    RoleType,
    TypeType,
    UriTemplateType,
)
from registry_adapter.rri.xml.generated.contact_5_0 import (
    PhoneType as Contact50PhoneType,
)
from registry_adapter.rri.xml.generated.verification_5_0 import (
    VerificationInformation,
)

__NAMESPACE__ = "http://registry.denic.de/regacc/5.0"


@dataclass(kw_only=True)
class InfoType:
    class Meta:
        name = "infoType"

    handle: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
            "max_length": 32,
            "pattern": r"[dD][eE][nN][iI][cC]\-[1-9][0-9]*",
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
class CityType(NormalizedStringPrivacyType):
    class Meta:
        name = "cityType"


@dataclass(kw_only=True)
class ContactInfoDataType:
    class Meta:
        name = "contactInfoDataType"

    type_value: None | TypeType = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    name: None | Contact50NameType = field(
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
    email: list[Contact50EmailType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/contact/5.0",
        },
    )
    phone: None | Contact50PhoneType = field(
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
    role: RoleType = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CountryCodeType(TokenPrivacyType):
    class Meta:
        name = "countryCodeType"


@dataclass(kw_only=True)
class EmailType(TokenPrivacyType):
    class Meta:
        name = "emailType"


@dataclass(kw_only=True)
class Info(InfoType):
    class Meta:
        name = "info"
        namespace = "http://registry.denic.de/regacc/5.0"


@dataclass(kw_only=True)
class NameType(NormalizedStringPrivacyType):
    class Meta:
        name = "nameType"


@dataclass(kw_only=True)
class PhoneType(TokenPrivacyType):
    class Meta:
        name = "phoneType"


@dataclass(kw_only=True)
class PostalCodeType(TokenPrivacyType):
    class Meta:
        name = "postalCodeType"


@dataclass(kw_only=True)
class UrlType(NormalizedStringPrivacyType):
    class Meta:
        name = "urlType"


@dataclass(kw_only=True)
class PostalType:
    class Meta:
        name = "postalType"

    address: list[AddressType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
            "min_occurs": 1,
        },
    )
    postal_code: PostalCodeType = field(
        metadata={
            "name": "postalCode",
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
            "required": True,
        }
    )
    city: CityType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
            "required": True,
        }
    )
    country_code: CountryCodeType = field(
        metadata={
            "name": "countryCode",
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class InfoDataType:
    class Meta:
        name = "infoDataType"

    handle: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
            "required": True,
            "max_length": 32,
            "pattern": r"[dD][eE][nN][iI][cC]\-[1-9][0-9]*",
        }
    )
    name: NameType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
            "required": True,
        }
    )
    postal: PostalType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
            "required": True,
        }
    )
    phone: list[PhoneType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
        },
    )
    fax: list[PhoneType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
        },
    )
    email: EmailType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
            "required": True,
        }
    )
    url: list[UrlType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
        },
    )
    memberacc: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
            "required": True,
            "max_length": 32,
            "pattern": r"[dD][eE][nN][iI][cC]\-[1-9][0-9]*",
        }
    )
    contact: list[ContactInfoDataType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
            "max_occurs": 2,
        },
    )
    changed: XmlDateTime = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/regacc/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class InfoData(InfoDataType):
    class Meta:
        name = "infoData"
        namespace = "http://registry.denic.de/regacc/5.0"
