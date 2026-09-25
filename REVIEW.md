# REVIEW.md — soát một thay đổi trước khi đẩy / gộp

Mỗi lượt soát một câu hỏi; ghi phát hiện kèm MỨC NẶNG. Cổng máy bắt được thì dựa vào cổng, mắt người soát phần
cổng không thấy.

## Mức nặng
| Mức | Nghĩa | Xử lý |
|---|---|---|
| **CHẶN** | sai dữ liệu, lộ dữ liệu / sai quyền, hỏng deploy, mất dữ liệu | sửa trước khi đẩy, kèm test đỏ-trước |
| **NÊN** | sai luật dự án, nợ mới, chữ / giao diện lệch chuẩn | sửa trong cùng nhánh |
| **GÓP Ý** | dễ đọc hơn, đặt tên | tuỳ người viết, trả lời một dòng |

## Các lượt soát
| # | Lượt | Hỏi gì | Cổng máy |
|---|---|---|---|
| 1 | Đúng sai | Luật nghiệp vụ đúng ở biên (ngày đầu/cuối, huỷ, rỗng)? Test đỏ trên mã cũ? Đột biến bị giết? Lỗi không bị nuốt (RULES §8)? | pytest từng mô-đun, `e2e/unit`, bộ đột biến |
| 2 | Bảo mật / quyền | View mới có lớp quyền + phạm vi (`can_see_class`)? Đối tượng không thuộc phạm vi → 404? Không lộ `.env`, token; SQL có tham số? | `tang_vai.py --kiem`, `tests_ma_tran_quyen`, `quet_quyen.py` |
| 3 | Lược đồ | DDL chỉ cộng, mục § mới ở cuối, có dòng `kiem_luoc_do`? `bootstrap_schema` HAI lần = 0 mục lượt 2? Mục dữ liệu mỗi lượt có WHERE? | guard `tests_luoc_do_muc`, `bootstrap_schema --kiem`, `--dien-tap` |
| 4 | Miền / cấu trúc | Tệp mới đúng miền? Có ghi bảng miền khác (phải qua hàm dịch vụ)? Sổ nợ co chứ không phình? Không vòng import miền? | `cau_truc.py --kiem` (f7), `ban_do.mjs --kiem` |
| 5 | Giao diện / tiếp cận | Mở thật hai khổ (1440, 390), sáng + tối, ảnh đã xem? Không px cứng, không tràn ngang? axe 0 vi phạm? Màn chặn theo `chanTu`? | tsc, eslint `--max-warnings 0`, `do_axe.mjs`, `do_giao_dien.mjs`, e2e |
| 6 | Chữ người dùng | Tiếng Việt người dùng hiểu, không mã kỹ thuật / tên cột / câu lỗi máy chủ thô; nhất quán với `vocab.py` / `huongDan.ts`? | (mắt người) |

## Mức tối thiểu theo loại thay đổi
- Chỉ tài liệu: lượt 6.
- Backend không đổi lược đồ: 1, 2, 4.
- Có mục lược đồ: 1, 2, 3, 4.
- Có màn: 1, 2, 4, 5, 6.

Cổng pre-push (`.githooks/pre-push`) phải ĐẠT; `--no-verify` chỉ khi ghi rõ lý do trong commit.
