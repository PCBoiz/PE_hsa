'use client';

// Route động /lesson/[courseId] — chỉ còn khoá HSA (TopHSA luyện thi ĐGNL ĐHQGHN).
// hsa_quantitative | hsa_verbal | hsa_science → LessonHsa (luồng đảo ngược 5 bước).
// courseId khác → redirect /courses/<id> (nội dung lập trình kế thừa từ pe_test đã gỡ 2026-08-10).
import { use, useEffect } from 'react';

import LessonHsa from '@/components/LessonHsa';

const HSA_COURSES = ['hsa_quantitative', 'hsa_verbal', 'hsa_science'];

export default function LessonDispatchPage({ params }: { params: Promise<{ courseId: string }> }) {
  const { courseId } = use(params);
  const isHsa = HSA_COURSES.includes(courseId);

  useEffect(() => {
    if (!isHsa) {
      window.location.replace(`/courses/${courseId}`);
    }
  }, [courseId, isHsa]);

  if (isHsa) return <LessonHsa courseId={courseId} />;
  return null;
}
