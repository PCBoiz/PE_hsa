import { serverJson } from '@/lib/server-api';

import TermsClient, { type TermRow } from './TermsClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Đợt học | TopHSA' };

type Payload = { terms: TermRow[]; statuses: string[] };

export default async function DotHocPage() {
  const kq = await serverJson<Payload>('/api/admin/terms', { requireAuth: true });

  return (
    <TermsClient
      initial={kq.ok ? kq.data.terms : []}
      statuses={kq.ok ? kq.data.statuses : ['active', 'finished', 'cancelled']}
      loi={kq.ok ? null : kq.message}
    />
  );
}
