'use client';

// /courses/db_design_tc — course_db_design.html với data-course="db_design_tc".
import CourseDbDesign from '@/components/CourseDbDesign';
import PageStyles from '@/components/PageStyles';

const CSS = [
  '/static/css/style.css',
  '/static/css/dashboard.css',
  '/static/css/pages.css',
  '/static/css/dark-mode.css',
  '/static/css/chatbot.css',
  '/static/css/course_db_design.css',
];

export default function Page() {
  return (
    <>
      <PageStyles hrefs={CSS} />
      <CourseDbDesign courseId="db_design_tc" />
    </>
  );
}
