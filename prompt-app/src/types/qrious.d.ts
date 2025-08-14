// src/types/qrious.d.ts

declare module 'qrious' {
  interface QRiousOptions {
    background?: string;
    backgroundAlpha?: number;
    foreground?: string;
    foregroundAlpha?: number;
    level?: string; // Hata düzeltme seviyesi: 'L', 'M', 'Q', 'H'
    mime?: string;
    padding?: number;
    size?: number;
    value?: string;
    [key: string]: any; // Diğer olası özellikler için
  }

  class QRious {
    constructor(options: QRiousOptions);
    toDataURL(mime?: string): string;
    // Eğer başka metodları kullanacaksanız buraya ekleyebilirsiniz
  }

  export default QRious;
}
