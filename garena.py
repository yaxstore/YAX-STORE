# ============================================================
# GARENA DIRECT GENERATOR
# ============================================================
import hmac, hashlib, requests, string, random, json, codecs, secrets, base64
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from config import Config
from rarity import check_rarity
import urllib3
urllib3.disable_warnings()


class ProtoBuilder:
    @staticmethod
    def encode_varint(n: int) -> bytes:
        if n < 0:
            return b''
        result = bytearray()
        while True:
            byte = n & 0x7F
            n >>= 7
            if n:
                byte |= 0x80
            result.append(byte)
            if not n:
                break
        return bytes(result)

    @classmethod
    def create_proto_field(cls, field_num: int, value) -> bytes:
        if isinstance(value, dict):
            nested = cls.build(value)
            header = (field_num << 3) | 2
            return cls.encode_varint(header) + cls.encode_varint(len(nested)) + nested
        elif isinstance(value, int):
            header = (field_num << 3) | 0
            return cls.encode_varint(header) + cls.encode_varint(value)
        elif isinstance(value, (str, bytes)):
            encoded_val = value.encode() if isinstance(value, str) else value
            header = (field_num << 3) | 2
            return cls.encode_varint(header) + cls.encode_varint(len(encoded_val)) + encoded_val
        return b''

    @classmethod
    def build(cls, fields: dict) -> bytes:
        return b''.join(cls.create_proto_field(k, v) for k, v in fields.items())


class SecurityEngine:
    @staticmethod
    def generate_ultra_secure_password() -> str:
        s = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        return f"Yax_{s}"

    @staticmethod
    def encrypt_api_payload(plain_hex: str) -> str:
        cipher = AES.new(Config.AES_KEY, AES.MODE_CBC, Config.AES_IV)
        padded_data = pad(bytes.fromhex(plain_hex), AES.block_size)
        return cipher.encrypt(padded_data).hex()

    @staticmethod
    def generate_signature(payload: str) -> str:
        return hmac.new(Config.API_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


class NetworkService:
    @staticmethod
    def get_session():
        s = requests.Session()
        s.verify = False
        s.headers.update({
            "User-Agent": "GarenaMSDK/4.0.44(25028RN03A ;Android 15;ar;EG;app 1.132.1 2019121229;)"
        })
        return s


class GarenaAPI:
    def __init__(self):
        self.session = NetworkService.get_session()

    def perform_major_login(self, access_token: str, open_id: str, lang: str):
        try:
            payload_parts = [
                b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02',
                lang.encode("ascii"),
                b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118693\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5'
            ]
            raw_payload = b''.join(payload_parts)
            raw_payload = raw_payload.replace(
                b'afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390',
                access_token.encode()
            )
            raw_payload = raw_payload.replace(
                b'1d8ec0240ede109973f3321b9354b44d',
                open_id.encode()
            )
            encrypted_data = bytes.fromhex(SecurityEngine.encrypt_api_payload(raw_payload.hex()))
            headers = {
                'User-Agent': "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
                'Accept-Encoding': "deflate, gzip",
                'X-GA-SV': "1789535859",
                'Authorization': "Bearer",
                'X-GA': "v1 1",
                'ReleaseVersion': "OB55",
                'Content-Type': "application/x-www-form-urlencoded",
                'X-Unity-Version': "2018.4.12f1"
            }
            resp = self.session.post(
                "https://loginbp.ppmainecoonghj.com/MajorLogin",
                headers=headers, data=encrypted_data, verify=False, timeout=20
            )
            if resp.status_code == 200:
                jwt_idx = resp.text.find("eyJ")
                if jwt_idx != -1:
                    token = resp.text[jwt_idx:]
                    dot_idx = token.find(".", token.find(".") + 1)
                    if dot_idx != -1:
                        token = token[:dot_idx + 44]
                        payload_b64 = token.split('.')[1]
                        padding = '=' * (4 - len(payload_b64) % 4)
                        decoded_json = json.loads(base64.urlsafe_b64decode(payload_b64 + padding))
                        acc_id = decoded_json.get('account_id') or decoded_json.get('external_id')
                        if acc_id:
                            return {"account_id": str(acc_id), "jwt_token": token}
        except Exception as e:
            print(f"[LOGIN-ERROR] {type(e).__name__}: {e}", flush=True)
        return None


class AccountGenerator:
    @classmethod
    def execute_creation(cls, region: str, prefix: str = "User", max_retry: int = 5):
        for _ in range(max_retry):
            try:
                api = GarenaAPI()
                password = SecurityEngine.generate_ultra_secure_password()

                reg_payload = json.dumps(
                    {"app_id": 100067, "client_type": 2, "password": password, "source": 2},
                    separators=(',', ':')
                )
                headers_reg = {
                    "User-Agent": "GarenaMSDK/4.0.44(25028RN03A ;Android 15;ar;EG;app 1.132.1 2019121229;)",
                    "Connection": "Keep-Alive",
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "Authorization": f"Signature {SecurityEngine.generate_signature(reg_payload)}",
                    "Content-Type": "application/json; charset=utf-8",
                    "Cookie": "datadome=oYpIhVco_RFvLHe_T9KFd5wuY0gcQuNfrlt4rHJY5QOkwv4TGt8gPMK32MbHuBdzJyfXnXlfzNZT_2tHr2kys8AMYT2~T71QP1S78_7Pdx4JLOXdSrflPT6cOX2vsyJh",
                    "Host": "100067.connect.garena.com",
                }
                resp_reg = api.session.post(
                    "https://100067.connect.garena.com/api/v2/oauth/guest:register",
                    headers=headers_reg, data=reg_payload, timeout=20, verify=False
                )
                if resp_reg.status_code != 200 or resp_reg.json().get("code") != 0:
                    print(f"[REG-FAIL] status={resp_reg.status_code} body={resp_reg.text[:200]}", flush=True)
                    continue
                uid = resp_reg.json()['data']['uid']

                tok_payload = json.dumps({
                    "client_id": 100067,
                    "client_secret": Config.API_HEX_KEY,
                    "client_type": 2,
                    "device_id": "02-344afb0e-593c-40b7-92f2-171972f74807",
                    "password": password,
                    "response_type": "token",
                    "uid": uid,
                }, separators=(',', ':'))

                headers_tok = headers_reg.copy()
                headers_tok["Cookie"] = "datadome=y23Z3X17pgkMHEt5zY8dqxC6BIf7WJMgC0RXNbqifHT7t9zajKe_hegFb1Ie9_7JixXpz7FRGVodOn~mWPk_NrqIIhUOXDYqKOahzoRQcyEy77GWEMcdA9_MqPJeM5qv"

                resp_tok = api.session.post(
                    "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant",
                    headers=headers_tok, data=tok_payload, timeout=20, verify=False
                )
                if resp_tok.status_code != 200 or resp_tok.json().get("code") != 0:
                    print(f"[TOK-FAIL] status={resp_tok.status_code} body={resp_tok.text[:200]}", flush=True)
                    continue

                access_token = resp_tok.json()['data']['access_token']
                open_id = resp_tok.json()['data']['open_id']

                keystream = [0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37,
                             0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30]
                field = codecs.decode(
                    ''.join(chr(ord(open_id[i]) ^ keystream[i % len(keystream)]) for i in range(len(open_id)))
                    .encode('unicode_escape').decode('utf-8'),
                    'unicode_escape'
                ).encode('latin1')

                rand_suffix = ''.join(random.choices(string.ascii_uppercase, k=6))
                name = f"{prefix}{rand_suffix}"
                lang = Config.REGION_LANG.get(region.upper(), "en")

                proto = ProtoBuilder.build({
                    1: name, 2: access_token, 3: open_id, 5: 102000007,
                    6: 4, 7: 1, 13: 1, 14: field, 15: lang, 16: 1, 17: 1
                })
                enc_major = bytes.fromhex(SecurityEngine.encrypt_api_payload(proto.hex()))

                headers_major = {
                    "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
                    "Accept-Encoding": "deflate, gzip",
                    "X-GA-SV": "1789535859",
                    "Authorization": "Bearer",
                    "X-GA": "v1 1",
                    "ReleaseVersion": "OB55",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Unity-Version": "2018.4.12f1",
                    "Host": "loginbp.ppmainecoonghj.com"
                }
                api.session.post(
                    "https://loginbp.ppmainecoonghj.com/MajorRegister",
                    headers=headers_major, data=enc_major, verify=False, timeout=20
                )

                login_data = api.perform_major_login(access_token, open_id, lang)
                if login_data:
                    account_id = login_data["account_id"]
                    rarity, patterns, score, reason = check_rarity(account_id)

                    return {
                        "account_id": str(account_id),
                        "created_at": datetime.utcnow().isoformat(),
                        "jwt_token": login_data.get("jwt_token", ""),
                        "name": name,
                        "password": password,
                        "patterns": patterns,
                        "rarity": rarity,
                        "rarity_reason": reason,
                        "rarity_score": score,
                        "region": region.upper(),
                        "uid": int(uid)
                    }
            except Exception as e:
                print(f"[GARENA-ERROR] {type(e).__name__}: {e}", flush=True)
        return None
