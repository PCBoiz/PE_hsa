"""Nhập ngân hàng câu hỏi đề thi thử từ một bảng tính.

── VÌ SAO (04/09/2026) ─────────────────────────────────────────────────────

Đo trên CSDL thật: **đúng MỘT đề thi thử** tồn tại, và nó đến từ `seed_data`.
Không có API quản trị nào cho đề thi — tức tới hôm nay, đường DUY NHẤT để có
thêm một đề là sửa mã nguồn. Mà trụ cột 4 của `TOPHSA_STRATEGY_PLAN` (đề CBT
/150, phân tích mạnh–yếu, vòng phản hồi về lộ trình) là thứ biến sản phẩm này
thành *luyện thi* thay vì một trang bài giảng. Với một đề, học viên tự đo được
đúng một lần.

Anh chốt: đề do TopHSA cung cấp. Nên việc ở đây không phải soạn câu hỏi, mà là
mở đường cho nội dung của họ chảy vào — bằng thứ họ có sẵn, là bảng tính.

── HÌNH DẠNG BẢNG TÍNH, VÀ VÌ SAO CHỌN THẾ ─────────────────────────────────

Một dòng = một câu hỏi. Đó là hình dạng Kahoot dùng, và nó đúng vì người soạn đề
đã nghĩ theo dòng sẵn rồi: một câu, bốn phương án, một đáp án.

Đáp án nhận HAI cách viết, cố ý:
  · chép nguyên văn phương án đúng — cách người soạn đề hay làm;
  · hoặc chữ cái A/B/C/D — cách người chấm hay làm.
Ưu tiên khớp NGUYÊN VĂN trước. Nếu để chữ cái thắng trước thì một đề có phương
án đúng là chuỗi "B" (hoàn toàn có thật ở câu hỏi về đáp án trắc nghiệm) sẽ bị
hiểu thành "phương án thứ hai" — sai âm thầm, và chỉ lộ ra khi học viên đã thi.
"""
import re
import unicodedata

from mockexam.views import SECTION_LABELS

#: Cột bắt buộc trong bảng tính. Tên tiếng Việt, chép nguyên từ mẫu tải về.
COT_BAT_BUOC = ('phần thi', 'câu hỏi', 'đáp án')

#: Cột phương án. Bốn là đủ cho HSA; thừa cột thì bỏ qua, thiếu thì thành câu điền.
COT_LUA_CHON = ('lựa chọn a', 'lựa chọn b', 'lựa chọn c', 'lựa chọn d')

#: Tên cột người dùng hay gõ khác đi. Khai TƯỜNG MINH — xem `common/bangtinh.py`
#: về việc vì sao không tự bỏ dấu để đoán.
TEN_KHAC = {
    'phan thi': 'phần thi', 'hợp phần': 'phần thi', 'hop phan': 'phần thi',
    'cau hoi': 'câu hỏi', 'nội dung câu hỏi': 'câu hỏi', 'noi dung cau hoi': 'câu hỏi',
    'dap an': 'đáp án', 'đáp án đúng': 'đáp án', 'dap an dung': 'đáp án',
    'lua chon a': 'lựa chọn a', 'lua chon b': 'lựa chọn b',
    'lua chon c': 'lựa chọn c', 'lua chon d': 'lựa chọn d',
    'a': 'lựa chọn a', 'b': 'lựa chọn b', 'c': 'lựa chọn c', 'd': 'lựa chọn d',
    'ma cau': 'mã câu', 'giai thich': 'giải thích', 'lời giải': 'giải thích',
    'chu de': 'chủ đề', 'topic': 'chủ đề',
}

#: Trần độ dài. BÁO chứ không cắt — cắt ngầm thì người soạn tưởng đã vào đủ, và
#: phát hiện ra vào đúng lúc học viên đang thi.
MAX_CAU_HOI = 2000
MAX_LUA_CHON = 500


def _bo_dau(s):
    """Bỏ dấu tiếng Việt — CHỈ dùng để đoán tên hợp phần, không dùng cho tiêu đề cột."""
    s = unicodedata.normalize('NFD', str(s or '').lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').replace('đ', 'd')


#: Nhãn hợp phần → khoá kỹ thuật. Nhận cả tên tiếng Việt lẫn khoá tiếng Anh.
_PHAN = {}
for khoa, nhan in SECTION_LABELS.items():
    _PHAN[khoa] = khoa
    _PHAN[_bo_dau(nhan)] = khoa
_PHAN.update({
    'tu duy dinh luong': 'quantitative', 'toan': 'quantitative',
    'tu duy dinh tinh': 'verbal', 'van': 'verbal', 'ngu van': 'verbal',
    'khoa hoc': 'science', 'tieng anh': 'science', 'khoa hoc & tieng anh': 'science',
})


def _ma_hop_le(s):
    return re.sub(r'[^a-zA-Z0-9_]+', '_', s or '').strip('_')[:40]


def doc_cau_hoi(ban_ghi):
    """``[(số dòng, {cột: giá trị})]`` → ``(danh sách câu hỏi, danh sách lỗi)``.

    Trả CẢ HAI để bên gọi kiểm toàn bộ rồi mới ghi. Dừng ở lỗi đầu tiên là bắt
    người soạn tải lên lại cho từng lỗi một — vòng lặp làm người ta bỏ cuộc.
    """
    cau, loi, ma_da_dung = [], [], {}

    for dong, b in ban_ghi:
        def sai(msg, _d=dong):
            loi.append('Dòng %d: %s' % (_d, msg))

        noi_dung = b.get('câu hỏi', '')
        if not noi_dung:
            sai('thiếu "câu hỏi".')
            continue
        if len(noi_dung) > MAX_CAU_HOI:
            sai('"câu hỏi" dài %d ký tự, tối đa %d.' % (len(noi_dung), MAX_CAU_HOI))
            continue

        phan_tho = b.get('phần thi', '')
        phan = _PHAN.get(_bo_dau(phan_tho))
        if not phan:
            sai('"phần thi" là %r — phải là một trong: %s.'
                % (phan_tho or '(trống)',
                   ', '.join(sorted(set(SECTION_LABELS.values())))))
            continue

        # Giữ HAI danh sách, cố ý:
        #   `theo_cot` — đúng vị trí cột A/B/C/D, kể cả cột bỏ trống ở giữa
        #   `lua_chon` — chỉ những phương án CÓ nội dung, để lưu và để hiện
        theo_cot = [b.get(c, '') for c in COT_LUA_CHON]
        lua_chon = [x for x in theo_cot if x]
        qua_dai = [x for x in lua_chon if len(x) > MAX_LUA_CHON]
        if qua_dai:
            sai('một phương án dài %d ký tự, tối đa %d.'
                % (max(len(x) for x in qua_dai), MAX_LUA_CHON))
            continue

        dap_an = b.get('đáp án', '')
        if not dap_an:
            sai('thiếu "đáp án".')
            continue

        if lua_chon:
            if len(lua_chon) < 2:
                sai('câu trắc nghiệm cần ít nhất 2 phương án (đang có %d). '
                    'Bỏ trống hết các cột "Lựa chọn" thì thành câu điền đáp án.'
                    % len(lua_chon))
                continue
            # SO BẰNG CHÍNH PHÉP SO CỦA MÁY CHẤM, không bằng `set()` thô.
            #
            # Chú thích cũ nói "máy chấm sẽ không phân biệt được" trong khi nó
            # dùng một phép so mà máy chấm KHÔNG dùng: `mockexam/views.py::_norm`
            # bỏ hoa/thường, khoảng trắng và cả dấu `%`. Nên bốn phương án
            #
            #     30%  ·  30  ·  3%  ·  300%
            #
            # — một câu hỏi toán hoàn toàn bình thường — lọt qua cửa này, rồi
            # học viên chọn `30` (SAI) vẫn được tính đúng vì máy chấm thấy nó
            # bằng `30%`. Điểm và bản đồ mạnh–yếu đều lệch, không dấu vết.
            #
            # Nhập trễ để tránh vòng import: `mockexam/views.py` không nhập
            # ngược lại tệp này, nhưng nhập ở đầu tệp thì đường nhập kéo theo cả
            # module chấm thi chỉ để dùng một hàm ba dòng.
            from mockexam.views import _norm
            gon = [_norm(x) for x in lua_chon]
            if len(set(gon)) != len(gon):
                trung = sorted({g for g in gon if gon.count(g) > 1})
                sai('có hai phương án MÁY CHẤM COI LÀ MỘT (%s). Máy chấm bỏ '
                    'hoa/thường, khoảng trắng và dấu %%, nên "30%%" và "30" là '
                    'cùng một đáp án — học viên chọn cái sai vẫn được điểm.'
                    % ', '.join('%r' % t for t in trung))
                continue
            # NGUYÊN VĂN trước, chữ cái sau. Xem lý do ở đầu tệp.
            if dap_an in lua_chon:
                dung = dap_an
            elif len(dap_an) == 1 and dap_an.upper() in 'ABCD':
                # Tra theo CỘT, không theo vị trí trong danh sách đã nén.
                #
                # Bản đầu tra `lua_chon[ord(x)-65]` trên danh sách ĐÃ BỎ các ô
                # trống. Một cột "Lựa chọn C" để trống là đủ để đáp án "D" trỏ
                # sang phương án khác: A,B,_,D nén lại thành [A,B,D], và
                # `[A,B,D][3]` thì hết chỉ số nên báo "chỉ có 3 phương án" —
                # nhưng đáp án "C" thì `[A,B,D][2]` = D, KHÔNG báo gì và lưu SAI.
                #
                # Sai âm thầm ở đây không dừng lại ở một câu hỏi: nó vào ngân
                # hàng đề, được chấm, và lộ ra dưới dạng "học viên thắc mắc vì
                # sao chọn đúng mà bị trừ điểm" — nhiều tuần sau, không dấu vết.
                vt = ord(dap_an.upper()) - 65
                if not theo_cot[vt]:
                    sai('"đáp án" ghi %r nhưng cột "Lựa chọn %s" đang để trống. '
                        'Điền phương án vào cột ấy, hoặc sửa đáp án cho khớp cột '
                        'có nội dung (đang có: %s).'
                        % (dap_an, dap_an.upper(),
                           ', '.join(chr(65 + i) for i, v in enumerate(theo_cot) if v)))
                    continue
                dung = theo_cot[vt]
            else:
                sai('"đáp án" (%r) không trùng phương án nào. Chép đúng nguyên văn '
                    'một phương án, hoặc ghi chữ cái A/B/C/D.' % dap_an[:60])
                continue
            mot = {'type': 'mcq', 'options': lua_chon, 'answer': dung}
        else:
            mot = {'type': 'fill', 'answer': dap_an}

        ma = _ma_hop_le(b.get('mã câu', '')) or 'q_%s_%d' % (phan[:2], dong)
        if ma in ma_da_dung:
            sai('"mã câu" %r đã dùng ở dòng %d. Mã phải khác nhau, hoặc bỏ trống '
                'để hệ thống tự đặt.' % (ma, ma_da_dung[ma]))
            continue
        ma_da_dung[ma] = dong

        mot.update({'id': ma, 'section': phan, 'question': noi_dung})
        if b.get('chủ đề'):
            mot['topic'] = b['chủ đề']
        # `giải thích` được nhận và lưu, dù engine hiện CHƯA hiện nó. Cố ý: nội
        # dung do đối tác bàn giao một lần, và bắt họ nhập lại cả ngân hàng khi
        # engine biết hiện lời giải là chuyện không nên xảy ra.
        if b.get('giải thích'):
            mot['explain'] = b['giải thích']
        cau.append(mot)

    if not cau and not loi:
        loi.append('Tệp không có dòng câu hỏi nào (chỉ có dòng tiêu đề?).')
    return cau, loi
