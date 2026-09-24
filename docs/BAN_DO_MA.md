# Bản đồ mã (graphify, mức tệp) — sinh tự động, đừng sửa tay

Sinh lại: `graphify update backend`, `graphify update frontend/src`, `graphify update frontend/public/static/js` (PowerShell; Git Bash làm graphify sập) rồi `python scripts/tong_hop_graphify.py docs/BAN_DO_MA.md`. Tệp test/migration bị bỏ.

## backend — 131 tệp mã (bỏ test/migration), 445 cạnh tệp→tệp

| Tệp | fan-in (tệp dùng nó) | fan-out (tệp nó dùng) | betweenness | nút | dòng |
|---|---|---|---|---|---|
| `backend/common/db.py` | 64 | 0 | 0.000 | 9 | 200 |
| `backend/common/clock.py` | 43 | 0 | 0.000 | 3 | 30 |
| `backend/common/permissions.py` | 29 | 1 | 0.000 | 22 | 249 |
| `backend/common/__init__.py` | 17 | 0 | 0.000 | 1 | 0 |
| `backend/common/audit.py` | 16 | 3 | 0.002 | 3 | 178 |
| `backend/teaching/vocab.py` | 16 | 1 | 0.000 | 3 | 70 |
| `backend/common/events.py` | 15 | 2 | 0.000 | 7 | 317 |
| `backend/common/views.py` | 14 | 0 | 0.000 | 3 | 52 |
| `backend/stats/goals.py` | 13 | 2 | 0.000 | 6 | 165 |
| `backend/common/identity.py` | 8 | 0 | 0.000 | 4 | 62 |
| `backend/courses/truy_cap.py` | 7 | 2 | 0.000 | 8 | 94 |
| `backend/common/params.py` | 7 | 1 | 0.000 | 6 | 133 |
| `backend/teaching/sessions.py` | 6 | 10 | 0.003 | 23 | 980 |
| `backend/stats/competency.py` | 6 | 3 | 0.000 | 8 | 362 |
| `backend/accounts/hashers.py` | 6 | 0 | 0.000 | 19 | 107 |
| `backend/accounts/validators.py` | 6 | 0 | 0.000 | 5 | 54 |
| `backend/stats/__init__.py` | 6 | 0 | 0.000 | 1 | 0 |
| `backend/accounts/hoat_dong.py` | 5 | 3 | 0.001 | 3 | 79 |

Betweenness cao nhất (tệp "cầu nối" giữa các cụm):
- `backend/teaching/sessions.py` 0.003 (fan-in 6, fan-out 10, 980 dòng)
- `backend/teaching/admin_users.py` 0.003 (fan-in 3, fan-out 18, 955 dòng)
- `backend/teaching/views.py` 0.003 (fan-in 3, fan-out 22, 1026 dòng)
- `backend/accounts/views.py` 0.002 (fan-in 2, fan-out 11, 670 dòng)
- `backend/accounts/authentication.py` 0.002 (fan-in 3, fan-out 1, 137 dòng)
- `backend/common/audit.py` 0.002 (fan-in 16, fan-out 3, 178 dòng)
- `backend/common/errors.py` 0.001 (fan-in 1, fan-out 2, 93 dòng)
- `backend/teaching/bao_doi_lich.py` 0.001 (fan-in 1, fan-out 6, 122 dòng)
- `backend/mockexam/views.py` 0.001 (fan-in 3, fan-out 6, 497 dòng)
- `backend/teaching/overview.py` 0.001 (fan-in 2, fan-out 9, 729 dòng)

Ma trận phụ thuộc giữa app backend (dòng = app gọi, cột = app bị gọi; số cạnh hàm):

| gọi \ bị gọi | accounts | achievements | backend | chatbot | common | config | courseadmin | courses | forum | leaderboard | lessons | mockexam | notifications | quizzes | roadmap | stats | teaching |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **accounts** |  |  |  |  | 95 |  |  |  |  |  |  |  |  |  |  |  |  |
| **achievements** |  |  |  |  | 12 |  |  |  |  |  |  |  |  |  |  |  |  |
| **backend** | 3 |  |  |  | 8 |  |  | 2 |  |  |  |  |  |  |  |  |  |
| **chatbot** |  |  |  |  | 19 |  |  |  |  |  |  |  |  |  |  | 8 |  |
| **common** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| **config** |  |  |  |  | 2 |  |  |  |  |  |  |  |  |  |  |  | 2 |
| **courseadmin** |  |  |  |  | 37 |  |  |  |  |  | 13 |  |  |  |  |  |  |
| **courses** |  |  |  |  | 39 |  |  |  |  |  |  |  |  |  |  |  |  |
| **forum** |  |  |  |  | 36 |  |  |  |  |  |  |  | 3 |  |  |  |  |
| **leaderboard** |  |  |  |  | 13 |  |  |  |  |  |  |  |  |  |  |  | 3 |
| **lessons** |  | 3 |  |  | 51 |  |  | 7 |  |  |  |  |  |  |  |  |  |
| **mockexam** |  | 3 |  |  | 58 |  |  |  |  |  |  |  |  |  |  |  |  |
| **notifications** |  |  |  |  | 28 |  |  |  |  |  |  |  |  |  |  |  |  |
| **quizzes** |  |  |  |  | 31 |  |  |  |  |  |  |  |  |  |  |  |  |
| **roadmap** | 3 |  |  |  | 19 |  |  |  |  |  |  |  |  |  |  |  |  |
| **stats** |  | 3 |  | 2 | 127 |  |  |  |  |  |  |  |  | 2 |  |  |  |
| **teaching** | 46 |  |  |  | 645 |  |  | 16 |  |  |  | 2 | 8 |  |  | 42 |  |

Vòng phụ thuộc giữa app (độ dài ≤ 3): 1
- chatbot → stats → chatbot

## react — 155 tệp mã (bỏ test/migration), 467 cạnh tệp→tệp

| Tệp | fan-in (tệp dùng nó) | fan-out (tệp nó dùng) | betweenness | nút | dòng |
|---|---|---|---|---|---|
| `src/components/ui/index.ts` | 37 | 0 | 0.000 | 1 | 20 |
| `src/components/ui/Button.tsx` | 26 | 0 | 0.000 | 4 | 92 |
| `src/lib/api.ts` | 25 | 2 | 0.004 | 9 | 197 |
| `src/components/ui/Card.tsx` | 25 | 1 | 0.001 | 3 | 93 |
| `src/lib/kiemDang.ts` | 24 | 0 | 0.000 | 5 | 61 |
| `src/lib/server-api.ts` | 23 | 3 | 0.006 | 6 | 193 |
| `src/lib/vaiTro.ts` | 19 | 0 | 0.000 | 8 | 43 |
| `src/components/ui/Chip.tsx` | 18 | 0 | 0.000 | 4 | 56 |
| `src/app/(standalone)/quan-tri/layVai.ts` | 16 | 2 | 0.004 | 3 | 39 |
| `src/components/ui/EmptyState.tsx` | 16 | 0 | 0.000 | 2 | 42 |
| `src/components/PageStyles.tsx` | 11 | 0 | 0.000 | 2 | 14 |
| `src/components/ui/Table.tsx` | 11 | 0 | 0.000 | 7 | 168 |
| `src/app/(standalone)/quan-tri/vai.ts` | 10 | 1 | 0.000 | 7 | 103 |
| `src/components/bieuTuong.tsx` | 10 | 0 | 0.000 | 3 | 83 |
| `src/app/(standalone)/quan-tri/ChanVai.tsx` | 10 | 0 | 0.000 | 4 | 42 |
| `src/components/ui/Field.tsx` | 8 | 0 | 0.000 | 2 | 79 |
| `src/components/AppShell.tsx` | 7 | 7 | 0.002 | 6 | 671 |
| `src/components/ui/Toast.tsx` | 7 | 0 | 0.000 | 7 | 89 |

Betweenness cao nhất (tệp "cầu nối" giữa các cụm):
- `src/lib/server-api.ts` 0.006 (fan-in 23, fan-out 3, 193 dòng)
- `src/app/(standalone)/quan-tri/layVai.ts` 0.004 (fan-in 16, fan-out 2, 39 dòng)
- `src/lib/api.ts` 0.004 (fan-in 25, fan-out 2, 197 dòng)
- `src/components/AppShell.tsx` 0.002 (fan-in 7, fan-out 7, 671 dòng)
- `src/lib/auth.ts` 0.002 (fan-in 6, fan-out 1, 157 dòng)
- `src/components/ui/Card.tsx` 0.001 (fan-in 25, fan-out 1, 93 dòng)
- `src/lib/hinhDang.ts` 0.001 (fan-in 6, fan-out 3, 115 dòng)
- `src/app/(base)/dashboard/DashboardClient.tsx` 0.001 (fan-in 1, fan-out 13, 1031 dòng)
- `src/components/Chatbot.tsx` 0.001 (fan-in 3, fan-out 4, 278 dòng)
- `src/lib/duLieuHsa.ts` 0.001 (fan-in 3, fan-out 2, 63 dòng)

## js_cu — 0 tệp mã (bỏ test/migration), 0 cạnh tệp→tệp

| Tệp | fan-in (tệp dùng nó) | fan-out (tệp nó dùng) | betweenness | nút | dòng |
|---|---|---|---|---|---|

Betweenness cao nhất (tệp "cầu nối" giữa các cụm):
