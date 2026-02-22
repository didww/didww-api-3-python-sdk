from enum import Enum, IntEnum


def enum_value(value):
    if isinstance(value, Enum):
        return value.value
    return value


def enum_value_list(values):
    if values is None:
        return None
    return [enum_value(v) for v in values]


def to_enum(enum_cls, value):
    if value is None or isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except ValueError:
        return value


def to_enum_list(enum_cls, values):
    if values is None:
        return None
    return [to_enum(enum_cls, value) for value in values]


class CallbackMethod(str, Enum):
    POST = "POST"
    GET = "GET"


class AddressVerificationStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class ExportType(str, Enum):
    CDR_IN = "cdr_in"
    CDR_OUT = "cdr_out"


class ExportStatus(str, Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"


class IdentityType(str, Enum):
    PERSONAL = "Personal"
    BUSINESS = "Business"
    ANY = "Any"


class OrderStatus(str, Enum):
    PENDING = "Pending"
    CANCELED = "Canceled"
    COMPLETED = "Completed"


class OnCliMismatchAction(str, Enum):
    SEND_ORIGINAL_CLI = "send_original_cli"
    REJECT_CALL = "reject_call"
    REPLACE_CLI = "replace_cli"


class MediaEncryptionMode(str, Enum):
    DISABLED = "disabled"
    SRTP_SDES = "srtp_sdes"
    SRTP_DTLS = "srtp_dtls"
    ZRTP = "zrtp"


class DefaultDstAction(str, Enum):
    ALLOW_ALL = "allow_all"
    REJECT_ALL = "reject_all"


class VoiceOutTrunkStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"


class CliFormat(str, Enum):
    RAW = "raw"
    E164 = "e164"
    LOCAL = "local"


class AreaLevel(str, Enum):
    WORLDWIDE = "WorldWide"
    COUNTRY = "Country"
    AREA = "Area"
    CITY = "City"


class Feature(str, Enum):
    VOICE_IN = "voice_in"
    VOICE_OUT = "voice_out"
    T38 = "t38"
    SMS_IN = "sms_in"
    SMS_OUT = "sms_out"


class StirShakenMode(str, Enum):
    DISABLED = "disabled"
    ORIGINAL = "original"
    PAI = "pai"
    ORIGINAL_PAI = "original_pai"
    VERSTAT = "verstat"


class TransportProtocol(IntEnum):
    UDP = 1
    TCP = 2
    TLS = 3


class RxDtmfFormat(IntEnum):
    RFC_2833 = 1
    SIP_INFO = 2
    RFC_2833_OR_SIP_INFO = 3


class TxDtmfFormat(IntEnum):
    DISABLED = 1
    RFC_2833 = 2
    SIP_INFO_RELAY = 3
    SIP_INFO_DTMF = 4


class SstRefreshMethod(IntEnum):
    INVITE = 1
    UPDATE = 2
    UPDATE_FALLBACK_INVITE = 3


class Codec(IntEnum):
    TELEPHONE_EVENT = 6
    G723 = 7
    G729 = 8
    PCMU = 9
    PCMA = 10
    SPEEX = 12
    GSM = 13
    G726_32 = 14
    G721 = 15
    G726_24 = 16
    G726_40 = 17
    G726_16 = 18
    L16 = 19
