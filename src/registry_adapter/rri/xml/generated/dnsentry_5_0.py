from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://registry.denic.de/dnsentry/5.0"


@dataclass(kw_only=True)
class DnsentryBaseType:
    class Meta:
        name = "dnsentryBaseType"

    owner: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/dnsentry/5.0",
            "required": True,
            "min_length": 1,
            "max_length": 254,
            "pattern": r"([*a-zA-Z0-9\-]+\.)+[*a-zA-Z0-9\-]*|(\.)",
        }
    )


@dataclass(kw_only=True)
class A(DnsentryBaseType):
    rdata: A.Rdata = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/dnsentry/5.0",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Rdata:
        address: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://registry.denic.de/dnsentry/5.0",
                "required": True,
                "min_length": 3,
                "max_length": 39,
            }
        )


@dataclass(kw_only=True)
class Aaaa(DnsentryBaseType):
    class Meta:
        name = "AAAA"

    rdata: Aaaa.Rdata = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/dnsentry/5.0",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Rdata:
        address: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://registry.denic.de/dnsentry/5.0",
                "required": True,
                "min_length": 3,
                "max_length": 39,
            }
        )


@dataclass(kw_only=True)
class Dnskey(DnsentryBaseType):
    class Meta:
        name = "DNSKEY"

    rdata: Dnskey.Rdata = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/dnsentry/5.0",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Rdata:
        flags: int = field(
            metadata={
                "type": "Element",
                "namespace": "http://registry.denic.de/dnsentry/5.0",
                "required": True,
            }
        )
        protocol: int = field(
            metadata={
                "type": "Element",
                "namespace": "http://registry.denic.de/dnsentry/5.0",
                "required": True,
            }
        )
        algorithm: int = field(
            metadata={
                "type": "Element",
                "namespace": "http://registry.denic.de/dnsentry/5.0",
                "required": True,
            }
        )
        public_key: bytes = field(
            metadata={
                "name": "publicKey",
                "type": "Element",
                "namespace": "http://registry.denic.de/dnsentry/5.0",
                "required": True,
                "format": "base64",
            }
        )


@dataclass(kw_only=True)
class Mx(DnsentryBaseType):
    class Meta:
        name = "MX"

    rdata: Mx.Rdata = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/dnsentry/5.0",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Rdata:
        preference: int = field(
            metadata={
                "type": "Element",
                "namespace": "http://registry.denic.de/dnsentry/5.0",
                "required": True,
                "min_inclusive": 0,
                "max_inclusive": 999,
            }
        )
        exchange: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://registry.denic.de/dnsentry/5.0",
                "required": True,
                "min_length": 1,
                "max_length": 254,
                "pattern": r"([*a-zA-Z0-9\-]+\.)+[*a-zA-Z0-9\-]*|(\.)",
            }
        )


@dataclass(kw_only=True)
class Ns(DnsentryBaseType):
    class Meta:
        name = "NS"

    rdata: Ns.Rdata = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/dnsentry/5.0",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Rdata:
        nameserver: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://registry.denic.de/dnsentry/5.0",
                "required": True,
                "min_length": 1,
                "max_length": 254,
                "pattern": r"([*a-zA-Z0-9\-]+\.)+[*a-zA-Z0-9\-]*|(\.)",
            }
        )
        address: list[str] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://registry.denic.de/dnsentry/5.0",
                "min_length": 3,
                "max_length": 39,
            },
        )
        address_v6: list[str] = field(
            default_factory=list,
            metadata={
                "name": "addressV6",
                "type": "Element",
                "namespace": "http://registry.denic.de/dnsentry/5.0",
                "min_length": 3,
                "max_length": 39,
            },
        )


@dataclass(kw_only=True)
class Dnsentry(DnsentryBaseType):
    class Meta:
        name = "dnsentry"
        namespace = "http://registry.denic.de/dnsentry/5.0"
