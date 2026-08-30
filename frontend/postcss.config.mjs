// Tailwind v4 chạy qua PostCSS. Không cần tailwind.config.js — mọi token khai
// bằng @theme trong src/app/tailwind.css (xem file đó để biết vì sao).
const config = {
  plugins: {
    '@tailwindcss/postcss': {},
  },
};

export default config;
