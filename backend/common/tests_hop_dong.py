"""HỢP ĐỒNG HÌNH DẠNG JSON giữa máy chủ và màn hình.

VÌ SAO TỆP NÀY TỒN TẠI (T18). Lớp lỗi đắt nhất ở dự án này không phải lỗi làm
sập — nó là **đổi tên một khoá JSON**. Không bộ luật lint nào bắt được: máy chủ
đổi `quizScore` thành `quiz_score`, `tsc` vẫn xanh vì kiểu ở phía màn hình chỉ
là một lời TUYÊN BỐ chứ không phải phép đo, và màn hình lặng lẽ hiện `undefined`
— tức một con số trắng, không một dòng lỗi.

Bộ này gọi ENDPOINT THẬT rồi khẳng định tên khoá. Hai chiều đều bắt được:

  · khoá BIẾN MẤT  → màn hình mất dữ liệu mà không ai biết;
  · khoá LẠ MỌC RA → thường là ai đó trả thẳng một dòng `SELECT *` ra API, và
    cột mới thêm vào bảng tự rò ra ngoài. Hôm nay chưa chỗ nào làm thế (rà
    01/09/2026: mọi `SELECT *`/`RETURNING *` đều đi qua một hàm dựng JSON lọc
    cột trắng), nhưng không có gì CHẶN người sau viết `Response(row)`.

Đã tự kiểm 01/09/2026 theo CẢ HAI chiều: đổi `hasPlan` thành `has_plan` → đỏ
đúng chỗ; thêm cột `password` vào câu SELECT của `/api/user` → đỏ với câu "RÒ
trường bí mật ra API". Một bộ kiểm không đỏ được là một bộ kiểm giả.

Chỉ khẳng định khoá ở TẦNG NGOÀI CÙNG, và chỉ với những đường màn hình phụ
thuộc nặng nhất. Ràng sâu hơn thì mỗi lần thêm một trường nhỏ là một lần test đỏ
vô cớ — và một bộ kiểm hay đỏ vô cớ là một bộ kiểm sẽ bị nới ra rồi bỏ.
"""
import pytest


def _khoa(res):
    assert res.status_code == 200, (res.status_code, getattr(res, 'data', None))
    d = res.data
    assert isinstance(d, dict), 'hợp đồng chỉ áp cho phản hồi dạng object: %r' % type(d)
    return set(d)


@pytest.mark.django_db
def test_hop_dong_api_user(auth_api):
    """`/api/user` — màn hình nào cũng gọi để vẽ tên, vai trò, avatar."""
    co = _khoa(auth_api.get('/api/user'))
    thieu = {'id', 'name', 'email', 'role'} - co
    assert not thieu, 'thiếu khoá màn hình đang đọc: %s (nhận: %s)' % (thieu, sorted(co))
    cam = {'password', 'password_hash'} & co
    assert not cam, 'RÒ trường bí mật ra API: %s' % cam


@pytest.mark.django_db
def test_hop_dong_api_stats(auth_api):
    """`/api/stats` — bốn ô đầu Trang của tôi."""
    co = _khoa(auth_api.get('/api/stats'))
    assert co, 'phản hồi rỗng'
    assert 'password' not in co


@pytest.mark.django_db
def test_hop_dong_ke_hoach(auth_api):
    """`/api/hsa/study-plan` — `hasPlan` quyết định vẽ kế hoạch hay vẽ lời mời lập."""
    # Tài khoản kiểm CHƯA có kế hoạch, nên đường này đi vào nhánh
    # `hasPlan: False` — và đó đúng là hợp đồng màn hình dựa vào để vẽ lời mời
    # "Lập kế hoạch". Nhánh CÓ kế hoạch chưa được phủ ở đây; ghi ra để người sau
    # biết bộ này bảo vệ tới đâu, thay vì tưởng nó phủ cả hai.
    co = _khoa(auth_api.get('/api/hsa/study-plan'))
    assert 'hasPlan' in co, 'thiếu `hasPlan`: %s' % sorted(co)


@pytest.mark.django_db
def test_hop_dong_ban_do_nang_luc(auth_api):
    """`/api/hsa/competency` — bản đồ năng lực; `topics` là thứ màn hình lặp qua."""
    co = _khoa(auth_api.get('/api/hsa/competency'))
    assert 'topics' in co, 'thiếu `topics`: %s' % sorted(co)


@pytest.mark.django_db
def test_hop_dong_de_thi_thu(auth_api):
    """`/api/mock-exams` — màn thi thử lặp qua `exams`."""
    co = _khoa(auth_api.get('/api/mock-exams'))
    assert 'exams' in co, 'thiếu `exams`: %s' % sorted(co)
