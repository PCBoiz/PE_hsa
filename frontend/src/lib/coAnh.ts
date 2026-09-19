/**
 * Co ảnh người dùng đính kèm về cạnh dài ≤1280px, JPEG 0,85, trả data URL.
 *
 * Ảnh chụp đề bằng điện thoại là 3–8 MB; gửi nguyên thì vượt trần thân request
 * (Django 2,5 MB) và tốn 4G của học viên. 1280px đủ để mô hình đọc chữ trên đề
 * (đo 20/09/2026: PNG 900×260 đọc đúng từng số) và thường chỉ còn 100–400 kB.
 * PNG trong suốt được phủ nền trắng: chữ đen trên nền trong suốt thành đen
 * trên đen khi ép sang JPEG.
 *
 * Chuyển từ `chatbot.js::handleChatbotImageUpload` (20/09/2026).
 */
export const CANH_MAX = 1280;

export function coAnh(file: File): Promise<string> {
  return new Promise((ok, loi) => {
    if (!file.type.startsWith('image/')) { loi(new Error('không phải ảnh')); return; }
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      const tiLe = Math.min(1, CANH_MAX / Math.max(img.naturalWidth, img.naturalHeight));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(img.naturalWidth * tiLe));
      canvas.height = Math.max(1, Math.round(img.naturalHeight * tiLe));
      const ctx = canvas.getContext('2d');
      if (!ctx) { loi(new Error('không có canvas')); return; }
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      ok(canvas.toDataURL('image/jpeg', 0.85));
    };
    img.onerror = () => { URL.revokeObjectURL(url); loi(new Error('không đọc được ảnh')); };
    img.src = url;
  });
}
