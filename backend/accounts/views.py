"""
Port routes/auth.py + routes/user.py (Flask) — giữ nguyên body/status từng response.
Khác biệt DUY NHẤT (có chủ đích, MIGRATION_NOTES §Auth): login/register trả thêm
cặp JWT access/refresh thay vì set session cookie (frontend ở domain khác).
"""
import json
from datetime import datetime

from django.db import transaction
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.hashers import check_werkzeug_password, make_werkzeug_password
from accounts.validators import (validate_email_field, validate_name_field,
                                 validate_password_field, validate_phone_field)
from common.db import q, q1, x
from common.throttling import LoginThrottle, RegisterThrottle


def _tokens_for(user_id):
    """Cấp cặp JWT cho user id (SimpleJWT)."""
    from accounts.models import User
    refresh = RefreshToken.for_user(User(id=user_id))
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


# ─────────────────────────── /auth/* ───────────────────────────

class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]   # 5 per minute (Flask @limiter.limit)

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        identifier = (data.get('email') or data.get('phone') or '').strip()
        password = data.get('password', '')
        errors = {}
        if not identifier:
            errors['email'] = 'Email hoặc số điện thoại không được để trống'
        elif '@' in identifier:
            if err := validate_email_field(identifier):
                errors['email'] = err
        else:
            if err := validate_phone_field(identifier):
                errors['email'] = err
        if not password:
            errors['password'] = 'Mật khẩu không được để trống'
        if errors:
            return Response({'errors': errors}, status=400)

        if '@' in identifier:
            user = q1('SELECT * FROM users WHERE email=%s', (identifier,))
        else:
            user = q1('SELECT * FROM users WHERE phone=%s', (identifier,))
        if not user:
            return Response({'error': 'Email/số điện thoại hoặc mật khẩu không đúng'}, status=401)

        stored = user['password']
        if not stored:
            return Response({'error': 'Email/số điện thoại hoặc mật khẩu không đúng'}, status=401)
        is_hashed = stored.startswith(('pbkdf2:', 'scrypt:'))
        if is_hashed:
            ok = check_werkzeug_password(stored, password)
        else:
            # Legacy plaintext (nếu còn sót): so trực tiếp rồi nâng cấp lên hash
            ok = (stored == password)
            if ok:
                x('UPDATE users SET password=%s WHERE id=%s',
                  (make_werkzeug_password(password), user['id']))

        if not ok:
            return Response({'error': 'Email/số điện thoại hoặc mật khẩu không đúng'}, status=401)
        needs_questionnaire = not bool(user['questionnaire_completed'])
        return Response({
            'ok': True,
            'name': user['name'],
            'needs_questionnaire': needs_questionnaire,
            **_tokens_for(user['id']),
        })


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]   # 3 per minute

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        phone = (data.get('phone') or '').strip()
        password = data.get('password', '')

        errors = {}
        if err := validate_name_field(name):
            errors['name'] = err
        if not email and not phone:
            msg = 'Vui lòng nhập email hoặc số điện thoại'
            errors['email'] = msg
            errors['phone'] = msg
        else:
            if email:
                if err := validate_email_field(email):
                    errors['email'] = err
            if phone:
                if err := validate_phone_field(phone):
                    errors['phone'] = err
        if err := validate_password_field(password):
            errors['password'] = err
        if errors:
            return Response({'errors': errors}, status=400)

        if email and q1('SELECT id FROM users WHERE email=%s', (email,)):
            return Response({'errors': {'email': 'Email đã được sử dụng'}}, status=400)
        if phone and q1('SELECT id FROM users WHERE phone=%s', (phone,)):
            return Response({'errors': {'phone': 'Số điện thoại đã được sử dụng'}}, status=400)

        try:
            user = q1(
                'INSERT INTO users (name, email, phone, password, role) '
                'VALUES (%s, %s, %s, %s, %s) RETURNING id, questionnaire_completed',
                (name, email if email else None, phone if phone else None,
                 make_werkzeug_password(password), 'Học viên'))
        except Exception as e:
            return Response({'error': f'Lỗi hệ thống khi đăng ký: {str(e)}'}, status=500)

        needs_questionnaire = not bool(user['questionnaire_completed'])
        return Response({'ok': True, 'needs_questionnaire': needs_questionnaire,
                         **_tokens_for(user['id'])})


class LogoutView(APIView):
    """GET /auth/logout — bản JWT: blacklist refresh token nếu client gửi kèm.

    Flask cũ clear session rồi redirect '/'; với JWT client tự xoá token là chính,
    endpoint này để thu hồi refresh token (POST body {'refresh': ...} tùy chọn).
    """
    permission_classes = [AllowAny]

    def _logout(self, request):
        token = None
        if isinstance(request.data, dict):
            token = request.data.get('refresh')
        if token:
            try:
                RefreshToken(token).blacklist()
            except Exception:
                pass
        return Response({'ok': True})

    def get(self, request):
        return self._logout(request)

    def post(self, request):
        return self._logout(request)


# ─────────────────────────── /api/user ───────────────────────────

class UserView(APIView):
    def get(self, request):
        user = q1('SELECT * FROM users WHERE id=%s', (request.user.id,))
        if not user:
            return Response({}, status=404)
        user['is_new_user'] = not bool(user.get('questionnaire_completed'))
        user['first_login'] = user['is_new_user']
        user.pop('password', None)  # không trả hash ra ngoài (bản Flask trả cả hash — vá có chủ đích, ghi MIGRATION_NOTES)
        return Response(user)

    def put(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        phone = (data.get('phone') or '').strip()
        birthday = (data.get('birthday') or '').strip()

        errors = {}
        if err := validate_name_field(name):
            errors['name'] = err
        if err := validate_email_field(email):
            errors['email'] = err
        if err := validate_phone_field(phone):
            errors['phone'] = err
        if errors:
            return Response({'errors': errors}, status=400)

        x('UPDATE users SET name=%s, email=%s, phone=%s, birthday=%s WHERE id=%s',
          (name, email, phone, birthday, request.user.id))
        return Response({'ok': True})


class PasswordView(APIView):
    def put(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        current = data.get('current', '')
        new_pw = data.get('new', '')
        errors = {}
        if err := validate_password_field(new_pw, label='Mật khẩu mới'):
            errors['new'] = err
        if errors:
            return Response({'errors': errors}, status=400)
        user = q1('SELECT password FROM users WHERE id=%s', (request.user.id,))
        stored = user['password'] if user else None
        if not stored:
            return Response({'error': 'Mật khẩu hiện tại không đúng'}, status=401)
        is_hashed = stored.startswith(('pbkdf2:', 'scrypt:'))
        pw_ok = check_werkzeug_password(stored, current) if is_hashed else (stored == current)
        if not pw_ok:
            return Response({'error': 'Mật khẩu hiện tại không đúng'}, status=401)
        x('UPDATE users SET password=%s WHERE id=%s',
          (make_werkzeug_password(new_pw), request.user.id))
        return Response({'ok': True})


# ─────────────── Follow (nguồn thật cho leaderboard "friends") ───────────────

class FollowView(APIView):
    def post(self, request, user_id):
        uid = request.user.id
        if user_id == uid:
            return Response({'error': 'Không thể tự follow chính mình'}, status=400)
        target = q1('SELECT id FROM users WHERE id=%s', (user_id,))
        if not target:
            return Response({'error': 'Không tìm thấy người dùng'}, status=404)
        x('INSERT INTO user_follows (follower_id, followee_id) '
          'VALUES (%s, %s) ON CONFLICT DO NOTHING', (uid, user_id))
        return Response({'ok': True, 'following': True})

    def delete(self, request, user_id):
        x('DELETE FROM user_follows WHERE follower_id=%s AND followee_id=%s',
          (request.user.id, user_id))
        return Response({'ok': True, 'following': False})


class FollowingView(APIView):
    def get(self, request, user_id):
        rows = q('''SELECT u.id, u.name, u.xp, u.streak, f.created_at
                    FROM user_follows f
                    JOIN users u ON u.id = f.followee_id
                    WHERE f.follower_id = %s
                    ORDER BY f.created_at DESC''', (user_id,))
        result = []
        for d in rows:
            created_at = d.pop('created_at')
            d['followedAt'] = created_at.isoformat() if created_at else None
            result.append(d)
        return Response({'following': result})


# ─────────────────────────── /api/survey ───────────────────────────

def _pick_roadmap_template(data):
    """Chọn template lộ trình phù hợp nhất từ câu trả lời khảo sát. (routes/user.py)"""
    career = (data.get('career_target') or '').lower()
    langs = (data.get('language') or '').lower()
    domain = (data.get('domain') or '').lower()

    if 'frontend' in career:
        return 'frontend'
    if 'backend' in career or 'devops' in career or 'sre' in career:
        return 'backend'
    if 'ai' in career or 'ml' in career or 'data' in career:
        return 'python'
    if 'fullstack' in career:
        return 'frontend'

    if 'c/c++' in langs or 'c++' in langs:
        return 'cpp'
    if 'python' in langs:
        return 'python'
    if 'javascript' in langs:
        return 'frontend'
    if 'java' in langs:
        return 'backend'

    if 'ai' in domain or 'machine learning' in domain or 'data' in domain:
        return 'python'
    if 'embedded' in domain or 'iot' in domain:
        return 'cpp'
    if 'web' in domain:
        return 'frontend'

    return 'frontend'


def _generate_user_roadmap(uid, survey_id, data):
    """Sao chép template khớp khảo sát thành lộ trình cá nhân (source='generated').
    Idempotent theo id 'u<uid>_generated'."""
    tmpl_id = _pick_roadmap_template(data)
    tmpl = q1('SELECT title, icon, color, nodes_json, edges_json, mermaid_def '
              'FROM roadmaps WHERE id=%s AND user_id IS NULL', (tmpl_id,))
    if not tmpl:
        return
    rid = f'u{uid}_generated'
    x('''INSERT INTO roadmaps
             (id, user_id, source, generated_from_survey_id,
              title, icon, color, nodes_json, edges_json, mermaid_def, updated_at)
         VALUES (%s, %s, 'generated', %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, now())
         ON CONFLICT (id) DO UPDATE SET
             generated_from_survey_id = EXCLUDED.generated_from_survey_id,
             title       = EXCLUDED.title,
             icon        = EXCLUDED.icon,
             color       = EXCLUDED.color,
             nodes_json  = EXCLUDED.nodes_json,
             edges_json  = EXCLUDED.edges_json,
             mermaid_def = EXCLUDED.mermaid_def,
             updated_at  = now()''',
      (rid, uid, survey_id, tmpl['title'], tmpl['icon'], tmpl['color'],
       json.dumps(tmpl['nodes_json']), json.dumps(tmpl['edges_json']),
       tmpl['mermaid_def']))


class SurveyView(APIView):
    def post(self, request):
        data = request.data
        if not isinstance(data, dict):
            return Response({'error': 'Dữ liệu khảo sát không hợp lệ'}, status=400)
        uid = request.user.id
        with transaction.atomic():
            survey = q1(
                'INSERT INTO surveys (user_id, data_json, created_at) '
                'VALUES (%s,%s,%s) RETURNING id',
                (uid, json.dumps(data, ensure_ascii=False), datetime.utcnow().isoformat()))
            x('UPDATE users SET questionnaire_completed=1 WHERE id=%s', (uid,))
            _generate_user_roadmap(uid, survey['id'], data)
        return Response({'ok': True})
