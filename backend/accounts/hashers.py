"""
Password hasher tương thích werkzeug — user hiện hữu đăng nhập được ngay,
KHÔNG reset mật khẩu (DB có hash dạng 'scrypt:32768:8:1$salt$hex' và
'pbkdf2:sha256:600000$salt$hex' do werkzeug.security tạo).

Django lưu nguyên chuỗi werkzeug trong cột password; encode() cũng sinh đúng
định dạng werkzeug để bản Flask cũ (nếu còn chạy song song) verify được.
"""
import hashlib
import hmac
import secrets

from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.crypto import constant_time_compare


class WerkzeugScryptHasher(BasePasswordHasher):
    """werkzeug 'scrypt:N:r:p$salt$hexhash' (mặc định từ werkzeug 2.3)."""
    algorithm = 'scrypt'  # match chuỗi bắt đầu 'scrypt:'

    def salt(self):
        return secrets.token_hex(8)

    def _split(self, encoded):
        method, salt, hashval = encoded.split('$', 2)
        _, n, r, p = method.split(':')
        return int(n), int(r), int(p), salt, hashval

    def encode(self, password, salt=None):
        salt = salt or self.salt()
        n, r, p = 32768, 8, 1  # default của werkzeug
        derived = hashlib.scrypt(password.encode(), salt=salt.encode(),
                                 n=n, r=r, p=p, maxmem=132 * n * r * p, dklen=64)
        return f'scrypt:{n}:{r}:{p}${salt}${derived.hex()}'

    def verify(self, password, encoded):
        n, r, p, salt, hashval = self._split(encoded)
        derived = hashlib.scrypt(password.encode(), salt=salt.encode(),
                                 n=n, r=r, p=p, maxmem=132 * n * r * p, dklen=64)
        return constant_time_compare(derived.hex(), hashval)

    def safe_summary(self, encoded):
        n, r, p, salt, hashval = self._split(encoded)
        return {'algorithm': 'werkzeug-scrypt', 'n': n, 'r': r, 'p': p,
                'salt': salt[:4] + '…', 'hash': hashval[:8] + '…'}

    def must_update(self, encoded):
        return False

    # Django gọi identify qua thuật toán prefix trước '$'; chuỗi werkzeug scrypt
    # có dạng 'scrypt:32768:8:1$...' nên algorithm-match cần custom:
    @classmethod
    def matches(cls, encoded):
        return encoded.startswith('scrypt:')


class WerkzeugPBKDF2Hasher(BasePasswordHasher):
    """werkzeug 'pbkdf2:sha256:iterations$salt$hexhash'."""
    algorithm = 'pbkdf2'

    def salt(self):
        return secrets.token_hex(8)

    def _split(self, encoded):
        method, salt, hashval = encoded.split('$', 2)
        parts = method.split(':')  # ['pbkdf2', 'sha256', '600000'] (iterations có thể vắng)
        digest = parts[1] if len(parts) > 1 else 'sha256'
        iterations = int(parts[2]) if len(parts) > 2 else 260000
        return digest, iterations, salt, hashval

    def encode(self, password, salt=None):
        salt = salt or self.salt()
        iterations = 600000
        derived = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
        return f'pbkdf2:sha256:{iterations}${salt}${derived.hex()}'

    def verify(self, password, encoded):
        digest, iterations, salt, hashval = self._split(encoded)
        derived = hashlib.pbkdf2_hmac(digest, password.encode(), salt.encode(), iterations)
        return constant_time_compare(derived.hex(), hashval)

    def safe_summary(self, encoded):
        digest, iterations, salt, hashval = self._split(encoded)
        return {'algorithm': 'werkzeug-pbkdf2', 'digest': digest,
                'iterations': iterations, 'salt': salt[:4] + '…', 'hash': hashval[:8] + '…'}

    def must_update(self, encoded):
        return False

    @classmethod
    def matches(cls, encoded):
        return encoded.startswith('pbkdf2:')


def check_werkzeug_password(stored: str, password: str) -> bool:
    """Verify trực tiếp (dùng trong view login — như check_password_hash cũ)."""
    if not stored:
        return False
    if stored.startswith('scrypt:'):
        return WerkzeugScryptHasher().verify(password, stored)
    if stored.startswith('pbkdf2:'):
        return WerkzeugPBKDF2Hasher().verify(password, stored)
    return False


def make_werkzeug_password(password: str) -> str:
    """generate_password_hash tương đương (scrypt mặc định như werkzeug hiện tại)."""
    return WerkzeugScryptHasher().encode(password)
