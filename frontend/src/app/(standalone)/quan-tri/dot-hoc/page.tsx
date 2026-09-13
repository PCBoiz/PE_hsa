import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

import TermsClient, { type TermRow } from './TermsClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Đợt học | TopHSA' };

type Payload = { terms: TermRow[]; statuses: string[] };
/* Hình dạng `/api/admin/terms` (`teaching/terms.py::_dict`) — T18 mức 2. */
const HINH_DANG = z.looseObject({
  terms: z.array(z.looseObject({
    id: z.number(),
    code: z.string().nullable(),
    name: z.string(),
    startsOn: z.string().nullable(),
    endsOn: z.string().nullable(),
    examDate: z.string().nullable(),
    status: z.string(),
    note: z.string().nullable(),
    classes: z.number().optional(),
    students: z.number().optional(),
  })),
  statuses: z.array(z.string()),
}) satisfies HinhDang<Payload>;

export default async function DotHocPage() {
  const kq = await serverJson<Payload>('/api/admin/terms', { requireAuth: true }, HINH_DANG);

  return (
    <TermsClient
      initial={kq.ok ? kq.data.terms : []}
      statuses={kq.ok ? kq.data.statuses : ['active', 'finished', 'cancelled']}
      loi={kq.ok ? null : kq.message}
    />
  );
}
