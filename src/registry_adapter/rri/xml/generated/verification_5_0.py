from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from xsdata.models.datatype import XmlDateTime

__NAMESPACE__ = "http://registry.denic.de/verification/5.0"


class VerificationResultType(Enum):
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(kw_only=True)
class VerifiedClaimsType:
    class Meta:
        name = "verifiedClaimsType"

    claim: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
            "min_occurs": 1,
        },
    )


@dataclass(kw_only=True)
class VerificationInfoBaseType:
    class Meta:
        name = "verificationInfoBaseType"

    verified_claims: VerifiedClaimsType = field(
        metadata={
            "name": "verifiedClaims",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
            "required": True,
        }
    )
    verification_result: VerificationResultType = field(
        metadata={
            "name": "verificationResult",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class DomainVerificationInformationType(VerificationInfoBaseType):
    class Meta:
        name = "domainVerificationInformationType"

    verification_reference: None | str = field(
        default=None,
        metadata={
            "name": "verificationReference",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
        },
    )
    verification_timestamp: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "verificationTimestamp",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
        },
    )
    verification_evidence: None | str = field(
        default=None,
        metadata={
            "name": "verificationEvidence",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
        },
    )
    verification_method: None | str = field(
        default=None,
        metadata={
            "name": "verificationMethod",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
        },
    )
    trust_framework: None | str = field(
        default=None,
        metadata={
            "name": "trustFramework",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
        },
    )


@dataclass(kw_only=True)
class VerificationInformation(VerificationInfoBaseType):
    class Meta:
        name = "verificationInformation"
        namespace = "http://registry.denic.de/verification/5.0"


@dataclass(kw_only=True)
class VerificationInformationType(VerificationInfoBaseType):
    class Meta:
        name = "verificationInformationType"

    verification_reference: str = field(
        metadata={
            "name": "verificationReference",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
            "required": True,
        }
    )
    verification_timestamp: XmlDateTime = field(
        metadata={
            "name": "verificationTimestamp",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
            "required": True,
        }
    )
    verification_evidence: str = field(
        metadata={
            "name": "verificationEvidence",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
            "required": True,
        }
    )
    verification_method: str = field(
        metadata={
            "name": "verificationMethod",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
            "required": True,
        }
    )
    trust_framework: str = field(
        metadata={
            "name": "trustFramework",
            "type": "Element",
            "namespace": "http://registry.denic.de/verification/5.0",
            "required": True,
        }
    )
