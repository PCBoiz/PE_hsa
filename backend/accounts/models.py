"""
Model map 1:1 với bảng có sẵn trên Neon (db/schema.py Flask). managed=False:
Django KHÔNG BAO GIỜ sinh DDL cho các bảng legacy — an toàn tuyệt đối với DB chung.
"""
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

from accounts.hashers import check_werkzeug_password, make_werkzeug_password


class UserManager(BaseUserManager):
    use_in_migrations = False

    def create_user(self, email, password=None, **extra):
        user = self.model(email=self.normalize_email(email), **extra)
        if password:
            user.password = make_werkzeug_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('role', 'admin')
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser):
    # bảng users không có cột last_login — gỡ field kế thừa từ AbstractBaseUser
    last_login = None

    id = models.AutoField(primary_key=True)
    name = models.TextField(null=True)
    email = models.TextField(unique=True, null=True)
    phone = models.TextField(default='', null=True)
    birthday = models.TextField(default='', null=True)
    role = models.TextField(default='Học viên', null=True)
    password = models.TextField(null=True)  # hash werkzeug scrypt:/pbkdf2:
    streak = models.IntegerField(default=0, null=True)
    certificates = models.IntegerField(default=0, null=True)
    gems = models.IntegerField(default=0, null=True)
    xp = models.IntegerField(default=0, null=True)
    questionnaire_completed = models.IntegerField(default=0, null=True)
    last_study_date = models.DateField(null=True)
    oauth_provider = models.TextField(null=True)
    oauth_provider_id = models.TextField(null=True)
    avatar = models.TextField(default='', null=True)
    is_verified = models.BooleanField(default=False, null=True)
    created_at = models.DateTimeField(null=True)
    # Vòng đời tài khoản (schema §31). 'active' | 'suspended'.
    status = models.TextField(default='active')
    must_change_password = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        managed = False

    # ── Tương thích hệ auth Django/allauth (bảng không có các cột này) ──
    @property
    def is_active(self):
        """Tài khoản bị trung tâm khoá thì coi như không hoạt động.

        ĐÂY LÀ CHỖ DUY NHẤT cần chặn, và cố ý đặt ở đây chứ không rải kiểm tra
        ở từng endpoint: SimpleJWT gọi ``is_active`` ở CẢ hai cửa —
        ``JWTAuthentication.get_user`` (mọi lời gọi API) và bộ làm mới token
        (``CHECK_USER_IS_ACTIVE`` mặc định True). Nhờ vậy khoá một tài khoản là
        cắt hiệu lực NGAY cả với token đã cấp trước đó, không phải chờ nó hết
        hạn. Rải kiểm tra ở từng endpoint thì chỉ cần quên một chỗ là hở.
        """
        return (self.status or 'active') == 'active'

    @property
    def is_staff(self):
        return self.role == 'admin'

    @property
    def is_superuser(self):
        return self.role == 'admin'

    def has_perm(self, perm, obj=None):
        return self.role == 'admin'

    def has_module_perms(self, app_label):
        return self.role == 'admin'

    # ── Password: định dạng werkzeug để Flask cũ vẫn verify được ──
    def set_password(self, raw_password):
        self.password = make_werkzeug_password(raw_password)

    def check_password(self, raw_password):
        return check_werkzeug_password(self.password or '', raw_password)


class Survey(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(null=True)
    data_json = models.JSONField(null=True)
    created_at = models.TextField(null=True)  # TEXT trong schema gốc — giữ nguyên

    class Meta:
        db_table = 'surveys'
        managed = False


class UserFollow(models.Model):
    pk = models.CompositePrimaryKey('follower_id', 'followee_id')
    follower_id = models.IntegerField()
    followee_id = models.IntegerField()
    created_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'user_follows'
        managed = False
