"""Port tests/test_parse_time_spent.py + tests/test_streak.py (Flask) — cùng case."""
from datetime import date, timedelta

import pytest

from common.db import q1, x
from stats.views import parse_time_spent

pytestmark = pytest.mark.django_db


# ── test_parse_time_spent.py (port nguyên văn) ──────────────────────────────

def test_happy_path():
    assert parse_time_spent('2h') == 2.0
    assert parse_time_spent('0.5h') == 0.5
    assert parse_time_spent('24h') == 24.0
    assert parse_time_spent('0') == 0.0


def test_none_and_empty():
    assert parse_time_spent(None) == 0.0
    assert parse_time_spent('') == 0.0
    assert parse_time_spent('   ') == 0.0


def test_negative():
    assert parse_time_spent('-2h') == 0.0
    assert parse_time_spent('-0.1h') == 0.0


def test_overflow():
    assert parse_time_spent('25h') == 25.0
    assert parse_time_spent('9999h') == 500.0


def test_invalid_format():
    assert parse_time_spent('abc') == 0.0
    assert parse_time_spent('2.5.1h') == 0.0


def test_boundary():
    assert parse_time_spent('24.0h') == 24.0


# ── test_streak.py (port — mission mock qua monkeypatch như bản Flask) ──────

def _set_streak(uid, streak, last_study_date):
    x('UPDATE users SET streak=%s, last_study_date=%s WHERE id=%s',
      (streak, last_study_date, uid))


@pytest.fixture
def da_ghi_danh(temp_user):
    """Ghi danh học viên tạm vào khoá HSA — điều kiện để hoàn thành một bài."""
    x("INSERT INTO enrollments (user_id, course_id, progress, completed_lessons, "
      "time_spent, last_lesson, next_lesson) VALUES (%s, %s, 0, 0, '0h', '', '') "
      "ON CONFLICT (user_id, course_id) DO NOTHING", (temp_user, 'hsa_quantitative'))
    return temp_user


def _hoc_xong_mot_bai(client):
    """Đường THẬT làm chuỗi ngày nhúc nhích: hoàn thành một bài học.

    Viết lại 31/08/2026. Sáu phép kiểm chuỗi ngày dưới đây trước kia đi qua
    `/api/mission/complete` và vá vào `stats.views._verify_mission_by_course`.
    Cả endpoint lẫn hàm đó đã bị xoá khi nhiệm vụ chuyển từ "nhiệm vụ SQL của
    pe_test" sang chấm bằng số liệu HSA thật, nên `monkeypatch.setattr` ném
    AttributeError NGAY Ở KHÂU DỰNG — tức chúng chưa từng chạy kể từ lần đổi ấy.
    Và chúng báo "error" chứ không "fail", thứ dễ lướt qua hơn nhiều.

    Nay đi qua `common/streak.py:touch_streak`, chỗ DUY NHẤT viết cột `streak`.
    Nó chỉ được gọi từ hai nơi: hoàn thành bài học và nộp đề thi thử. Nhận
    thưởng nhiệm vụ KHÔNG chạm vào chuỗi ngày — hợp lý, vì nhiệm vụ chỉ đủ điều
    kiện sau khi đã học thật, nên chuỗi đã cộng từ trước đó rồi.
    """
    return client.post('/api/lessons/1/complete',
                       {'courseId': 'hsa_quantitative', 'xpEarned': 10}, format='json')


def test_van_bao_dung_chuoi_ngay(auth_api, temp_user):
    """`streak` vẫn là con số thật và endpoint vẫn phải nói đúng nó."""
    _set_streak(temp_user, 3, date.today())
    res = auth_api.get('/api/streak/review-quiz-status')
    assert res.status_code == 200
    assert res.json()['streak'] == 3


def test_CHUOI_NGAY_khong_con_la_dieu_kien_mo_quiz(auth_api, temp_user):
    """Ba phép kiểm cũ ở đây khẳng định luật `streak >= 5` — một luật KHÔNG được
    thi hành: `GenerateQuizView` gác bằng số CÂU HỎI trong kho, nên chuỗi 9 ngày
    mà chưa xong bài nào thì vẫn không tạo được quiz. Hai chỗ nói hai điều, và
    chỗ được người dùng chạm vào là chỗ kia (L14, 31/08/2026).
    """
    _set_streak(temp_user, 9, date.today())
    d = auth_api.get('/api/streak/review-quiz-status').json()
    assert d['streak'] == 9
    assert d['isUnlocked'] is False, (
        'chuỗi 9 ngày mà chưa xong bài nào vẫn báo đã mở khoá: %s' % d)
    assert d['available'] == 0 and d['questionsNeeded'] == d['minQuestions']


def test_requires_login(api, db):
    res = api.get('/api/streak/review-quiz-status')
    assert res.status_code == 401


def test_streak_increments_on_consecutive_day_khi_hoc_xong_bai(auth_api, da_ghi_danh):
    _set_streak(da_ghi_danh, 4, date.today() - timedelta(days=1))
    data = _hoc_xong_mot_bai(auth_api).json()
    assert data['ok'] is True
    assert data['streak'] == 5
    # Bỏ phần khẳng định "chuỗi 5 ngày ⇒ mở quiz": đó là luật đã bị gỡ. Phép
    # kiểm này kiểm CHUỖI NGÀY, và con số ấy vẫn do `/complete` trả về.


def test_streak_resets_after_missing_a_day(auth_api, da_ghi_danh):
    _set_streak(da_ghi_danh, 5, date.today() - timedelta(days=3))
    data = _hoc_xong_mot_bai(auth_api).json()
    assert data['streak'] == 1


def test_streak_unchanged_when_studying_again_same_day(auth_api, da_ghi_danh):
    _set_streak(da_ghi_danh, 5, date.today())
    data = _hoc_xong_mot_bai(auth_api).json()
    assert data['ok'] is True
    assert data['streak'] == 5


def test_nghi_dung_mot_ngay_con_ve_thi_chuoi_khong_dut(auth_api, da_ghi_danh):
    """Nghỉ đúng một ngày mà còn vé bảo hiểm → tiêu vé, chuỗi vẫn tăng.

    Phép kiểm cũ tên `test_streak_resets_at_exactly_two_days_gap` khẳng định
    chuỗi về 1 ở đây — đó là luật CŨ, trước khi có vé bảo hiểm. Vé sinh ra vì
    "ôn 6 tháng rồi mất sạch chuỗi vì một ngày bận" là điểm bỏ cuộc kinh điển
    (xem `common/streak.py`). Tách làm hai phép kiểm để cả hai nhánh đều có
    người canh: một nhánh còn vé, một nhánh hết vé.
    """
    _set_streak(da_ghi_danh, 5, date.today() - timedelta(days=2))
    x('UPDATE users SET streak_freezes=1 WHERE id=%s', (da_ghi_danh,))
    data = _hoc_xong_mot_bai(auth_api).json()
    assert data['streak'] == 6
    assert data['usedStreakFreeze'] is True
    assert q1('SELECT streak_freezes AS n FROM users WHERE id=%s',
              (da_ghi_danh,))['n'] == 0   # đã tiêu đúng một vé


def test_nghi_mot_ngay_ma_HET_ve_thi_chuoi_ve_1(auth_api, da_ghi_danh):
    _set_streak(da_ghi_danh, 5, date.today() - timedelta(days=2))
    x('UPDATE users SET streak_freezes=0 WHERE id=%s', (da_ghi_danh,))
    data = _hoc_xong_mot_bai(auth_api).json()
    assert data['streak'] == 1
    assert data['usedStreakFreeze'] is False


def test_streak_starts_at_one_for_first_time_user(auth_api, da_ghi_danh):
    # fixture tạo tài khoản với last_study_date=NULL
    assert _hoc_xong_mot_bai(auth_api).json()['streak'] == 1


def test_stats_streak_active_true_when_studied_today(auth_api, temp_user):
    _set_streak(temp_user, 3, date.today())
    res = auth_api.get('/api/stats')
    assert res.status_code == 200
    assert res.json()['streakActive'] is True


def test_stats_streak_active_false_when_not_studied_today(auth_api, temp_user):
    _set_streak(temp_user, 3, date.today() - timedelta(days=1))
    assert auth_api.get('/api/stats').json()['streakActive'] is False


def test_stats_streak_active_false_when_never_studied(auth_api):
    assert auth_api.get('/api/stats').json()['streakActive'] is False


def test_hoc_xong_bai_thi_streak_active_bat_len(auth_api, da_ghi_danh):
    """Nghỉ 5 ngày rồi học lại: chuỗi về 1, và /api/stats phải nói "đang hoạt động".

    Bản cũ khẳng định phản hồi có trường `streak_active` hardcode True — di sản
    Flask, và trường đó đã không còn. Viết lại để đo thứ NGƯỜI DÙNG thấy: sau
    khi học xong một bài thì màn hình chuỗi ngày phải sáng lên trong hôm nay,
    chứ không phải một khoá JSON có tồn tại hay không.
    """
    _set_streak(da_ghi_danh, 5, date.today() - timedelta(days=5))
    assert auth_api.get('/api/stats').json()['streakActive'] is False
    data = _hoc_xong_mot_bai(auth_api).json()
    assert data['streak'] == 1
    assert auth_api.get('/api/stats').json()['streakActive'] is True


# ── memory-plan T4.3: /api/stats không được 500 khi enrollment.progress = NULL ──
def test_stats_avg_progress_handles_null_progress(auth_api, temp_user):
    """Cột enrollments.progress nullable → dữ liệu thật có thể NULL. StatsView tính
    sum(progress)/len phải bỏ qua NULL, không được ném TypeError (500)."""
    x("INSERT INTO courses (id, title) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
      ('mp_t43_course', 'T43 Course'))
    x("INSERT INTO enrollments (user_id, course_id, progress) VALUES (%s, %s, NULL) "
      "ON CONFLICT (user_id, course_id) DO UPDATE SET progress = NULL",
      (temp_user, 'mp_t43_course'))
    res = auth_api.get('/api/stats')
    assert res.status_code == 200
    assert res.json()['avgProgress'] == 0  # NULL coi như 0


# ── L9 · đếm hoạt động theo CẶP (ref_type, ref_id) ─────────────────────────

def _su_kien(uid, kind, ref_type, ref_id, course_id, topic, diem=50):
    from common.clock import local_today
    x('''INSERT INTO learning_events
             (user_id, kind, dedup_key, occurred_at, event_date, course_id, topic,
              ref_type, ref_id, score, max_score)
         VALUES (%s,%s,%s, now(), %s, %s, %s, %s, %s, %s, 100)''',
      (uid, kind, '%s:%s:%s' % (kind, ref_type, ref_id), local_today(),
       course_id, topic, ref_type, ref_id, diem))


@pytest.mark.django_db
def test_bai_hoc_2_va_quiz_2_la_HAI_hoat_dong_khac_nhau():
    """Mỗi loại tham chiếu có KHÔNG GIAN ID RIÊNG. Đếm bằng `ref_id` trần thì
    bài học #2 và quiz ôn tập #2 gộp thành một, và ô chủ đề tụt xuống dưới
    ngưỡng `MIN_ACTIVITIES` → hiện "chưa đủ dữ liệu" thay vì con số có thật.

    Đo 31/08/2026 trên dữ liệu thật: chủ đề "Số học" của em id 9 đi từ
    `mastery=None, confidence=1` sang `mastery=22, confidence=2` sau khi vá.
    """
    from stats.competency import compute
    r = q1("INSERT INTO users (name, email, password, streak) "
           "VALUES ('HV L9','hv_l9_tmp@example.com','x',0) RETURNING id")
    uid = r['id']
    bai = q1("SELECT course_id, module FROM lessons "
             "WHERE module IS NOT NULL AND module <> '' LIMIT 1")
    _su_kien(uid, 'lesson', 'lesson', '2', bai['course_id'], bai['module'])
    _su_kien(uid, 'review_quiz', 'quiz', '2', bai['course_id'], bai['module'])

    o = next(t for t in compute(uid)['topics']
             if t['course'] == bai['course_id'] and t['topic'] == bai['module'])
    assert o['confidence'] == 2, (
        'hai hoạt động khác loại trùng số thứ tự bị đếm thành %s' % o['confidence'])
    assert o['status'] == 'ok' and o['mastery'] is not None


@pytest.mark.django_db
def test_bai_hoc_va_phong_luyen_cung_bai_VAN_la_mot_hoat_dong():
    """Chỗ CỐ Ý gộp phải giữ nguyên: một bài học sinh ra hai sự kiện (kiểm tra
    + phòng luyện) nhưng vẫn chỉ là một lần chạm vào chủ đề."""
    from stats.competency import compute
    r = q1("INSERT INTO users (name, email, password, streak) "
           "VALUES ('HV L9b','hv_l9b_tmp@example.com','x',0) RETURNING id")
    uid = r['id']
    bai = q1("SELECT course_id, module FROM lessons "
             "WHERE module IS NOT NULL AND module <> '' LIMIT 1")
    _su_kien(uid, 'lesson', 'lesson', '7', bai['course_id'], bai['module'])
    _su_kien(uid, 'drill', 'lesson', '7', bai['course_id'], bai['module'])

    o = next(t for t in compute(uid)['topics']
             if t['course'] == bai['course_id'] and t['topic'] == bai['module'])
    assert o['confidence'] == 1, o['confidence']


# ── L10 · ngày thi HÔM NAY (`days = 0`) không được coi là "chưa đặt mốc" ────

@pytest.mark.django_db
@pytest.mark.parametrize('con_lai,tuan_toi_da', [(0, 1), (1, 1), (13, 2)])
def test_ngay_thi_HOM_NAY_van_la_mot_moc_thi(db, con_lai, tuan_toi_da):
    """`days = 0` là falsy trong Python. Bản cũ dùng `if days`, nên đúng cái
    ngày cần siết nhất thì hệ NỚI RA: còn 1 ngày → kế hoạch 1 tuần; còn 0 ngày →
    kế hoạch trải 12 tuần như thể chưa đặt mốc thi.

    Đi qua đường THẬT (`stats.plan.generate`) chứ không kiểm lại một biểu thức
    tự viết trong phép kiểm — RULES §19.
    """
    import json as _json
    from datetime import date, timedelta
    from stats import plan
    r = q1("INSERT INTO users (name, email, password, streak) "
           "VALUES ('HV L10','hv_l10_tmp@example.com','x',0) RETURNING id")
    uid = r['id']
    x("INSERT INTO surveys (user_id, data_json, created_at) VALUES (%s, %s::jsonb, now())",
      (uid, _json.dumps({'target_score': 100, 'exam_timing': 'Trong 1 tháng',
                         'exam_date': (date.today() + timedelta(days=con_lai)).isoformat(),
                         'study_time': '2h'})))

    tom_tat, loi = plan.generate(uid)
    assert not loi, loi
    so_tuan = tom_tat.get('weeksTotal') if isinstance(tom_tat, dict) else None
    assert so_tuan == tuan_toi_da, (
        'còn %d ngày mà kế hoạch dựng %s tuần' % (con_lai, so_tuan))


# ── L8 · điểm đề thi thử GIỮ trong số hiện, TÁCH khỏi quyết định xếp lịch ────

@pytest.mark.django_db
def test_diem_de_thi_thu_khong_con_keo_chu_de_xuong_duoi_nguong(db):
    """Đề thi thử chỉ chia theo HỢP PHẦN, không biết câu nào thuộc chủ đề nào —
    nên nó bị rải đều 25% vào MỌI ô chủ đề của khoá.

    Đo 31/08/2026 trên dữ liệu thật: Đại số của em id 9 là 62 theo bằng chứng
    chủ đề nhưng hiện 42 sau khi trộn — dưới ngưỡng 60 nên hệ xếp lịch ôn lại.
    Anh Sơn chốt "giữ nhưng tách hiển thị": `mastery` giữ nguyên để HIỆN,
    `masteryTopic` chỉ từ bằng chứng chủ đề, và QUYẾT ĐỊNH dùng con số sau.
    """
    from stats import plan
    from stats.competency import compute
    r = q1("INSERT INTO users (name, email, password, streak) "
           "VALUES ('HV L8','hv_l8_tmp@example.com','x',0) RETURNING id")
    uid = r['id']
    bai = q1("SELECT course_id, module FROM lessons "
             "WHERE module IS NOT NULL AND module <> '' LIMIT 1")

    # Chủ đề làm rất tốt…
    _su_kien(uid, 'lesson', 'lesson', '11', bai['course_id'], bai['module'], diem=85)
    _su_kien(uid, 'review_quiz', 'quiz', '11', bai['course_id'], bai['module'], diem=85)
    # …nhưng đề thi thử của cả khoá thì kém.
    _su_kien(uid, 'mock_section', 'mock_attempt', '11', bai['course_id'], None, diem=0)

    o = next(t for t in compute(uid)['topics']
             if t['course'] == bai['course_id'] and t['topic'] == bai['module'])

    # HỆ QUẢ trước, con số sau: thứ thật sự hại học viên là buổi ôn bị xếp thừa.
    yeu = [t['topic'] for t in plan._weak_topics(compute(uid))]
    assert bai['module'] not in yeu, (
        'chủ đề làm 85%% vẫn bị xếp lịch ôn vì điểm đề kéo xuống: %s' % yeu)

    assert o.get('masteryTopic') == 85, o
    assert o['mastery'] < o['masteryTopic'], (
        'số hiện phải VẪN gộp điểm đề (anh chốt "giữ"): %s' % o)
    assert o['mastery'] < plan.REVIEW_BELOW <= o['masteryTopic'], (
        'phép kiểm chỉ có nghĩa khi hai con số nằm hai bên ngưỡng: %s' % o)


# ── L12 · mục kế hoạch chỉ được tick bởi đúng việc, và sau khi kế hoạch có ──

def _ke_hoach(uid, tuan_dau, sinh_luc, muc):
    """Dựng một kế hoạch tối giản. `muc` là list (kind, course_id, lesson_no, topic)."""
    pid = q1("INSERT INTO study_plans (user_id, is_active, generated_at, basis) "
             "VALUES (%s, TRUE, %s, '{}'::jsonb) RETURNING id", (uid, sinh_luc))['id']
    for i, (kind, cid, no, topic) in enumerate(muc, 1):
        x("INSERT INTO study_plan_items (plan_id, week_start, sort_order, kind, "
          "course_id, lesson_no, topic, title, reason, status) "
          "VALUES (%s,%s,%s,%s,%s,%s,%s,'x','y','todo')",
          (pid, tuan_dau, i, kind, cid, no, topic))
    return pid


@pytest.mark.django_db
def test_viec_lam_TRUOC_khi_co_ke_hoach_khong_tick_muc_nao(db):
    """Kế hoạch sinh hôm nay nhưng bắt đầu từ thứ Hai cùng tuần: hai ngày đầu
    tuần nằm TRƯỚC lúc nó tồn tại. Bản cũ lấy mốc sàn là TUẦN ĐẦU nên vẫn cho
    chúng tick — kế hoạch vừa lập ra đã có sẵn mục "đã xong".
    """
    from datetime import timedelta
    from stats import plan
    from common.clock import local_now, local_today
    r = q1("INSERT INTO users (name, email, password, streak) "
           "VALUES ('HV L12','hv_l12_tmp@example.com','x',0) RETURNING id")
    uid = r['id']
    # Mốc dựng TƯỜNG MINH, không phụ thuộc hôm nay là thứ mấy: kế hoạch bắt đầu
    # từ 3 ngày trước nhưng chỉ được SINH ra hôm nay.
    ngay_lam = local_today() - timedelta(days=3)
    _su_kien(uid, 'mock', 'mock_attempt', '901', None, None, diem=50)
    x("UPDATE learning_events SET event_date=%s WHERE user_id=%s AND kind='mock'",
      (ngay_lam, uid))
    _ke_hoach(uid, ngay_lam, local_now(), [('mock', None, None, None)])

    ra = plan.read(uid, all_weeks=True)
    assert ra['totals']['done'] == 0, (
        'việc làm trước khi kế hoạch tồn tại vẫn tick xong một mục: %s' % ra['totals'])


@pytest.mark.django_db
def test_hoc_bai_moi_KHONG_tick_muc_ON_LAI_chu_de(db):
    """Học một bài mới trong chủ đề X không phải là ôn lại chủ đề X — và học
    viên cũng không hề làm hai việc. Bản cũ để chung một rổ nên MỘT lần hoàn
    thành bài tick xong HAI mục kế hoạch."""
    from datetime import timedelta
    from stats import plan
    from common.clock import local_now, local_today
    r = q1("INSERT INTO users (name, email, password, streak) "
           "VALUES ('HV L12b','hv_l12b_tmp@example.com','x',0) RETURNING id")
    uid = r['id']
    bai = q1("SELECT course_id, module FROM lessons "
             "WHERE module IS NOT NULL AND module <> '' LIMIT 1")
    thu_hai = local_today() - timedelta(days=local_today().weekday())
    _ke_hoach(uid, thu_hai, local_now() - timedelta(days=7),
              [('review', bai['course_id'], None, bai['module'])])
    # Hôm nay em học một BÀI MỚI thuộc chủ đề ấy.
    _su_kien(uid, 'lesson', 'lesson', '55', bai['course_id'], bai['module'])

    ra = plan.read(uid, all_weeks=True)
    assert ra['totals']['done'] == 0, (
        'học bài mới đã tick xong một buổi ÔN LẠI: %s' % ra['totals'])


@pytest.mark.django_db
def test_quiz_on_tap_VAN_tick_duoc_muc_on_lai(db):
    """Siết mà siết luôn cả việc ôn thật thì kế hoạch không bao giờ xong."""
    from datetime import timedelta
    from stats import plan
    from common.clock import local_now, local_today
    r = q1("INSERT INTO users (name, email, password, streak) "
           "VALUES ('HV L12c','hv_l12c_tmp@example.com','x',0) RETURNING id")
    uid = r['id']
    bai = q1("SELECT course_id, module FROM lessons "
             "WHERE module IS NOT NULL AND module <> '' LIMIT 1")
    thu_hai = local_today() - timedelta(days=local_today().weekday())
    _ke_hoach(uid, thu_hai, local_now() - timedelta(days=7),
              [('review', bai['course_id'], None, bai['module'])])
    _su_kien(uid, 'review_quiz', 'quiz', '55', bai['course_id'], bai['module'])

    ra = plan.read(uid, all_weeks=True)
    assert ra['totals']['done'] == 1, ra['totals']


@pytest.mark.django_db
def test_moc_san_ke_hoach_chinh_xac_toi_GIO(db):
    """Mốc sàn cắt về `date` thì kế hoạch sinh lúc 00:30 vẫn bị tick bởi việc
    làm lúc 00:10 CÙNG NGÀY — tức 20 phút TRƯỚC khi nó tồn tại."""
    from datetime import timedelta
    from stats import plan
    from common.clock import local_now, local_today
    r = q1("INSERT INTO users (name, email, password, streak) "
           "VALUES ('HV B16','hv_b16_tmp@example.com','x',0) RETURNING id")
    uid = r['id']
    hom_nay = local_today()
    sinh_luc = local_now().replace(hour=12, minute=30, second=0, microsecond=0)

    _su_kien(uid, 'mock', 'mock_attempt', '902', None, None, diem=50)
    # Cùng NGÀY nhưng SỚM HƠN hai tiếng so với lúc kế hoạch được sinh.
    x("UPDATE learning_events SET event_date=%s, occurred_at=%s "
      "WHERE user_id=%s AND kind='mock'",
      (hom_nay, sinh_luc - timedelta(hours=2), uid))
    _ke_hoach(uid, hom_nay, sinh_luc, [('mock', None, None, None)])

    ra = plan.read(uid, all_weeks=True)
    assert ra['totals']['done'] == 0, (
        'việc làm 2 tiếng TRƯỚC khi kế hoạch tồn tại vẫn tick: %s' % ra['totals'])


@pytest.mark.django_db
def test_viec_lam_SAU_khi_sinh_ke_hoach_van_tick_binh_thuong(db):
    """Siết mà siết luôn việc làm thật thì kế hoạch không bao giờ xong."""
    from datetime import timedelta
    from stats import plan
    from common.clock import local_now, local_today
    r = q1("INSERT INTO users (name, email, password, streak) "
           "VALUES ('HV B16b','hv_b16b_tmp@example.com','x',0) RETURNING id")
    uid = r['id']
    hom_nay = local_today()
    sinh_luc = local_now().replace(hour=8, minute=0, second=0, microsecond=0)

    _su_kien(uid, 'mock', 'mock_attempt', '903', None, None, diem=50)
    x("UPDATE learning_events SET event_date=%s, occurred_at=%s "
      "WHERE user_id=%s AND kind='mock'",
      (hom_nay, sinh_luc + timedelta(hours=3), uid))
    _ke_hoach(uid, hom_nay, sinh_luc, [('mock', None, None, None)])

    ra = plan.read(uid, all_weeks=True)
    assert ra['totals']['done'] == 1, ra['totals']
