import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import tseslint from "typescript-eslint";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),

  /* ── Tầng TYPE-AWARE, bật CÓ CHỌN ────────────────────────────────────────
     Đo 01/09/2026: bật cả `recommendedTypeChecked` cho `src/` ra **576 lỗi** —
     nhưng **561 trong đó là `no-unsafe-*`**, và tất cả sinh từ đúng một chỗ:
     `const W = () => window as any`, cầu nối sang các hàm toàn cục của main.js.
     Đó là một RANH GIỚI CỐ Ý (mã legacy không có kiểu), không phải một khiếm
     khuyết. Bật cả bộ là chôn 15 phát hiện thật dưới 561 dòng tiếng ồn — và
     tiếng ồn làm người ta thôi đọc cảnh báo (cùng lý do đã tắt `S608` bên ruff).

     Nên chỉ bật những luật CHỈ tầng này bắt được, và mỗi luật bắt một lớp lỗi
     đã từng xảy ra ở đây:
       · `no-floating-promises` — một lời gọi async không ai chờ: lỗi của nó
         biến mất không dấu vết, người dùng thấy màn hình đứng im.
       · `no-misused-promises` — đưa hàm async vào chỗ cần callback trả `void`
         (`onClick`, `onSubmit`): rejection không ai bắt.
       · `no-base-to-string` — `${obj}` ra `"[object Object]"`. Đúng lớp lỗi của
         T22, thứ đã hiện lên banner đỏ trước mặt trợ giảng. */
  ...tseslint.configs.base ? [] : [],
  {
    files: ["src/**/*.ts", "src/**/*.tsx"],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    plugins: { "@typescript-eslint": tseslint.plugin },
    rules: {
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/no-misused-promises": "error",
      "@typescript-eslint/no-base-to-string": "error",
      // `as never` là cách bịt miệng trình biên dịch chứ không phải mô tả kiểu.
      // Đã có một chỗ dùng nó (`AccountsClient.tsx`) và tầng cũ không bắt được.
      "no-restricted-syntax": ["error", {
        selector: "TSAsExpression > TSNeverKeyword",
        message: "`as never` bịt miệng trình biên dịch. Sửa kiểu, hoặc thu hẹp bằng một phép kiểm thật.",
      }],
    },
  },
  {
    // `catch (e) {}` mà không dùng `e` là lối viết bình thường: có nhánh nào đó
    // ta CỐ Ý bỏ qua, và chú thích ngay trong khối nói vì sao. ESLint 9 đổi mặc
    // định của `caughtErrors` sang `'all'`, nên 24 chỗ như thế bỗng thành cảnh
    // báo — không chỗ nào là lỗi.
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { caughtErrors: "none", argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
    },
  },

  {
    /* ── `public/static/js/**` là MỘT THẾ GIỚI KHÁC ───────────────────────────
       15 tệp JS thuần nạp bằng thẻ `<script>`, KHÔNG đi qua bundler. Trong đó
       hàm khai ở cấp cao nhất là BIẾN TOÀN CỤC của trang, và chúng được gọi từ
       thuộc tính `onclick=` trong JSX/HTML hoặc từ một tệp script khác — hai
       nơi eslint không nhìn thấy.

       Nên `no-unused-vars` ở đây báo 80 hàm "không dùng" mà thực tế đang chạy:
       `toggleModule`, `enroll`, `unenroll`, `markAllBellRead`… Tin nó mà xoá là
       vỡ ứng dụng — đúng cái bẫy mà danh sách "mã chết" ở T19 đã sập một lần.
       Tắt luật cho đúng thư mục này và ghi rõ vì sao, chứ không hạ ngưỡng chung
       để con số đẹp lên.

       Hàng rào CÓ ích cho thư mục này vẫn còn: CI chạy `node --check` từng tệp
       (một lỗi cú pháp ở đây từng giết cả màn Quản trị trên production ngày
       27/08/2026, trong khi mọi cửa kiểm khác đều xanh). */
    files: ["public/static/js/**/*.js"],
    rules: {
      "@typescript-eslint/no-unused-vars": "off",
    },
  },
]);

export default eslintConfig;
