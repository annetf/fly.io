import struct
from typing import Optional

# Custom Company Identifier for BLE advertising (0xFFFF is reserved for testing)
CUSTOM_COMPANY_ID = b'\xff\xff'
CUSTOM_SERVICE_UUID = b'\xff\xff' # 16-bit UUID for custom service (optional)
CUSTOM_INVALID_U16 = 0xFFFF
CUSTOM_INVALID_S16 = -32768  # 0x8000 int16

def parse_custom_payload(payload: bytes) -> dict:
    """Parse custom 19-byte payload."""
    format_version = payload[0]
    (
        temp,
        hum,
        press,
        gas_res,
        iaq,
        co2,
        voc,
        voc_index,
        sgp40_raw
    ) = struct.unpack_from("<hHHHHHHHH", payload, offset=1)
    return {
        "formatVersion": format_version,
        "temperature": None if temp == CUSTOM_INVALID_S16 else temp / 100.0,
        "humidity": None if hum == CUSTOM_INVALID_U16 else hum / 100.0,
        "pressure": None if press == CUSTOM_INVALID_U16 else press,
        "gas_resistance": None if gas_res == CUSTOM_INVALID_U16 else gas_res,
        "iaq": None if iaq == CUSTOM_INVALID_U16 else iaq,
        "co2": None if co2 == CUSTOM_INVALID_U16 else co2,
        "voc": None if voc == CUSTOM_INVALID_U16 else voc / 100.0,
        "sgp40_voc_index": None if voc_index == CUSTOM_INVALID_U16 else voc_index,
        "sgp40_raw": None if sgp40_raw == CUSTOM_INVALID_U16 else sgp40_raw,
    }

def extract_custom_payload(raw_hex: str) -> Optional[bytes]:
    """Extract custom payload from raw hex string."""
    data = bytes.fromhex(raw_hex)
    i = 0
    while i < len(data) - 2:
        length = data[i]
        ad_type = data[i+1]
        if length == 0 or i + 1 + length > len(data):
            break
        if ad_type == 0xFF and length >= 3:
            company_id = data[i+2:i+4]
            if company_id == CUSTOM_COMPANY_ID and length >= 3 + 19:
                return data[i+4:i+4+19]
        if ad_type == 0x16 and length >= 3:
            uuid = data[i+2:i+4]
            if uuid == CUSTOM_SERVICE_UUID and length >= 3 + 19:
                return data[i+4:i+4+19]
        i += 1 + length
    return None

def try_parse_label(raw_hex: str) -> Optional[dict]:
    """Try to parse custom payload from raw hex string."""
    payload = extract_custom_payload(raw_hex)
    if payload and len(payload) == 19:
        return parse_custom_payload(payload)
    return None