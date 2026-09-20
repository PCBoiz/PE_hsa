import { redirect } from 'next/navigation';
import { z } from 'zod';

import { serverJson } from '@/lib/server-api';

/**
 * `/giang-day/cham/<bài>` → chuyển tới bảng chấm `/giang-day/bai-tap/<lớp>/<bài>`.
 *
 * Tồn tại vì chuông "em X đã nộp" (20/09/2026) chỉ mang id BÀI: bảng
 * `notifications` có một `ref_id`, không có chỗ cho lớp. Máy chủ tra lớp rồi
 * chuyển hướng; không phải giảng viên phụ trách thì API trả 404 và trang này
 * đưa về Việc hôm nay thay vì hiện một bảng chấm rỗng.
 */
export const dynamic = 'force-dynamic';

const HD = z.looseObject({ assignment: z.looseObject({ classId: z.number() }) });

export default async function ChamChuyenHuong({
  params,
}: {
  params: Promise<{ assignmentId: string }>;
}) {
  const { assignmentId } = await params;
  const kq = await serverJson<{ assignment: { classId: number } }>(
    `/api/teach/assignments/${assignmentId}/submissions`,
    { requireAuth: true },
    HD,
  );
  redirect(kq.ok ? `/giang-day/bai-tap/${kq.data.assignment.classId}/${assignmentId}` : '/giang-day');
}
