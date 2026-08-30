"""Port tests/test_review_quiz.py (Flask) — FE-06 generate + submit + chấm điểm."""
import json

import pytest

from common.db import q1

pytestmark = pytest.mark.django_db

COURSE_ID = 'hsa_quantitative'   # CSDL HSA khong con khoa 'db_design' cua ProgrammingEdu


def _make_step2(idx):
    """Bài 1 dạng spec cũ {question, options}; bài khác dạng thật {mcq: [...]}."""
    options = [
        {'id': 'a', 'text': 'Sai A', 'correct': False, 'explanation': 'Sai vì A'},
        {'id': 'b', 'text': f'Đúng {idx}', 'correct': True, 'explanation': 'Chuẩn luôn'},
        {'id': 'c', 'text': 'Sai C', 'correct': False, 'explanation': 'Sai vì C'},
    ]
    if idx == 1:
        return {'step_2': {'question': f'Câu hỏi test số {idx}?', 'options': options}}
    return {'step_2': {'mcq': [
        {'question': f'Câu hỏi test số {idx}?', 'options': options},
        {'question': f'Câu hỏi phụ số {idx}?', 'options': options},
    ]}}


@pytest.fixture
def quiz_user(temp_user):
    """User tạm + 6 lesson tạm có step_2 đã completed (rollback tự dọn)."""
    lesson_ids = []
    for i in range(1, 7):
        row = q1('''INSERT INTO lessons (course_id, title, sort_order, lesson_code, content_json)
                    VALUES (%s, %s, %s, %s, %s::jsonb) RETURNING id''',
                 (COURSE_ID, f'QZTEST bài {i}', 9000 + i, f'qztest_dj_{i}',
                  json.dumps(_make_step2(i), ensure_ascii=False)))
        lesson_ids.append(row['id'])
        q1('''INSERT INTO lesson_progress (user_id, lesson_id, course_id, status, completed_at)
              VALUES (%s, %s, %s, 'completed', now()) RETURNING user_id''',
           (temp_user, row['id'], COURSE_ID))
    return temp_user, lesson_ids


@pytest.fixture
def other_api(db):
    # APIClient RIÊNG (không dùng chung fixture `api` với auth_api)
    from accounts.models import User
    from rest_framework.test import APIClient
    from common.db import q1 as _q1
    row = _q1("INSERT INTO users (name, email, password) VALUES (%s, %s, %s) RETURNING id",
              ('Quiz Other', 'quiz_other_dj@example.com', 'x'))
    client = APIClient()
    client.force_authenticate(user=User.objects.get(id=row['id']))
    return client


def _generate(client, num=None):
    body = {} if num is None else {'num_questions': num}
    return client.post(f'/api/courses/{COURSE_ID}/quiz/generate', body, format='json')


def test_generate_requires_min_5_completed(other_api):
    res = _generate(other_api)
    assert res.status_code == 400
    assert 'ít nhất 5 bài' in res.json()['error']


def test_generate_hides_correct_field(auth_api, quiz_user):
    res = _generate(auth_api, num=5)
    assert res.status_code == 200
    data = res.json()
    assert data['total'] == 5
    assert len(data['questions']) == 5
    for qq in data['questions']:
        for o in qq['options']:
            assert 'correct' not in o


def test_submit_all_correct(auth_api, quiz_user):
    quiz = _generate(auth_api, num=5).json()
    answers = [{'question_no': qq['question_no'], 'selected': 'b'} for qq in quiz['questions']]
    res = auth_api.post(f"/api/quizzes/{quiz['quiz_id']}/submit", {'answers': answers}, format='json')
    assert res.status_code == 200
    data = res.json()
    assert data['score'] == data['total'] == 5
    assert data['percentage'] == 100


def test_submit_one_wrong(auth_api, quiz_user):
    quiz = _generate(auth_api, num=5).json()
    answers = [{'question_no': qq['question_no'], 'selected': 'b'} for qq in quiz['questions']]
    answers[0]['selected'] = 'a'
    data = auth_api.post(f"/api/quizzes/{quiz['quiz_id']}/submit", {'answers': answers}, format='json').json()
    assert data['score'] == data['total'] - 1
    wrong = [r for r in data['review'] if not r['is_correct']]
    assert len(wrong) == 1
    assert wrong[0]['question_no'] == answers[0]['question_no']
    assert wrong[0]['correct_answer'] == 'b'
    assert wrong[0]['explanation'] == 'Sai vì A'


def test_resubmit_blocked_409(auth_api, quiz_user):
    quiz = _generate(auth_api, num=5).json()
    answers = [{'question_no': qq['question_no'], 'selected': 'b'} for qq in quiz['questions']]
    r1 = auth_api.post(f"/api/quizzes/{quiz['quiz_id']}/submit", {'answers': answers}, format='json')
    assert r1.status_code == 200
    r2 = auth_api.post(f"/api/quizzes/{quiz['quiz_id']}/submit", {'answers': answers}, format='json')
    assert r2.status_code == 409
    n = q1('SELECT COUNT(*) AS n FROM review_quiz_results WHERE quiz_id=%s', (quiz['quiz_id'],))['n']
    assert n == 1


def test_submit_other_users_quiz_403(auth_api, quiz_user, other_api):
    quiz = _generate(auth_api, num=5).json()
    res = other_api.post(f"/api/quizzes/{quiz['quiz_id']}/submit", {'answers': []}, format='json')
    assert res.status_code in (403, 404)
    assert 'review' not in (res.json() or {})


def test_submit_bad_body_400(auth_api, quiz_user):
    quiz = _generate(auth_api, num=5).json()
    res = auth_api.post(f"/api/quizzes/{quiz['quiz_id']}/submit", {}, format='json')
    assert res.status_code == 400


def test_get_quiz_roundtrip(auth_api, quiz_user, other_api):
    quiz = _generate(auth_api, num=5).json()

    r = auth_api.get(f"/api/quizzes/{quiz['quiz_id']}")
    assert r.status_code == 200
    data = r.json()
    assert data['status'] == 'generated'
    assert len(data['questions']) == 5
    for qq in data['questions']:
        for o in qq['options']:
            assert 'correct' not in o

    answers = [{'question_no': qq['question_no'], 'selected': 'b'} for qq in quiz['questions']]
    auth_api.post(f"/api/quizzes/{quiz['quiz_id']}/submit", {'answers': answers}, format='json')

    data2 = auth_api.get(f"/api/quizzes/{quiz['quiz_id']}").json()
    assert data2['status'] == 'submitted'
    assert data2['result']['score'] == 5
    assert 'questions' not in data2

    # quiz của người khác → 404, không lộ dữ liệu
    r3 = other_api.get(f"/api/quizzes/{quiz['quiz_id']}")
    assert r3.status_code == 404


def test_quiz_history(auth_api, quiz_user):
    quiz = _generate(auth_api, num=5).json()
    answers = [{'question_no': qq['question_no'], 'selected': 'b'} for qq in quiz['questions']]
    auth_api.post(f"/api/quizzes/{quiz['quiz_id']}/submit", {'answers': answers}, format='json')

    r = auth_api.get(f'/api/courses/{COURSE_ID}/quiz/history')
    assert r.status_code == 200
    hist = r.json()['history']
    assert any(h['quiz_id'] == quiz['quiz_id'] and h['score'] == 5 for h in hist)


def test_unknown_question_no_ignored(auth_api, quiz_user):
    quiz = _generate(auth_api, num=5).json()
    answers = [{'question_no': qq['question_no'], 'selected': 'b'} for qq in quiz['questions']]
    answers.append({'question_no': 999, 'selected': 'a'})
    res = auth_api.post(f"/api/quizzes/{quiz['quiz_id']}/submit", {'answers': answers}, format='json')
    assert res.status_code == 200
    assert res.json()['score'] == 5
