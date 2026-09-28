# ============================================================
# CONFIG
# ============================================================
import os


class Config:
    API_HEX_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
    API_SECRET_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"

    AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    AES_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

    REGION_LANG = {
        "BD": "bn", "IND": "hi", "PK": "ur", "SG": "en", "ID": "id",
        "ME": "ar", "CIS": "ru", "TH": "th", "EU": "en", "US": "en",
        "SAC": "es", "LK": "en", "BR": "pt", "VN": "vi", "TW": "zh",
        "MY": "ms", "PH": "tl", "KR": "ko", "JP": "ja", "CN": "zh",
        "RU": "ru", "EG": "ar", "SA": "ar", "AE": "ar", "TR": "tr",
        "MX": "es", "CO": "es", "AR": "es", "PE": "es", "CL": "es",
        "NG": "en", "ZA": "en", "KE": "en", "GH": "en", "TZ": "en",
        "AU": "en", "NZ": "en", "GB": "en", "DE": "de", "FR": "fr",
        "IT": "it", "ES": "es", "PT": "pt", "NL": "nl", "PL": "pl",
    }

    API_KEYS = os.environ.get(
        "YAX_API_KEYS",
        "yax-secret-key-1,yax-secret-key-2,yax-secret-key-3"
    ).split(",")

    RATE_LIMIT = 60
    MAX_WORKERS = 10
