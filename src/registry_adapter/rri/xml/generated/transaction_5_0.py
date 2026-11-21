from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

__NAMESPACE__ = "http://registry.denic.de/transaction/5.0"


@dataclass(kw_only=True)
class DataType:
    class Meta:
        name = "dataType"

    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )


class LevelType(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ResultType(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    EXCEPTION = "exception"


@dataclass(kw_only=True)
class MessageType:
    class Meta:
        name = "messageType"

    text: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/transaction/5.0",
            "required": True,
        }
    )
    argument: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/transaction/5.0",
        },
    )
    level: LevelType = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    code: int = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class Message(MessageType):
    class Meta:
        name = "message"
        namespace = "http://registry.denic.de/transaction/5.0"


@dataclass(kw_only=True)
class TransactionType:
    class Meta:
        name = "transactionType"

    stid: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/transaction/5.0",
            "min_length": 3,
            "max_length": 64,
        },
    )
    ctid: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/transaction/5.0",
            "min_length": 3,
            "max_length": 64,
        },
    )
    result: ResultType = field(
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/transaction/5.0",
            "required": True,
        }
    )
    message: list[MessageType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/transaction/5.0",
        },
    )
    data: None | DataType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://registry.denic.de/transaction/5.0",
        },
    )


@dataclass(kw_only=True)
class Transaction(TransactionType):
    class Meta:
        name = "transaction"
        namespace = "http://registry.denic.de/transaction/5.0"
