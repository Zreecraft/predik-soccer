/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Design tokens (dark-only) — sesuai UI_REDESIGN.md
        canvas: '#0f1a15', // --bg
        card: '#16241d', // --card
        ink: '#e9f1ec', // --ink
        mute: '#93a79b', // --mute
        line: '#27392f', // --line
        home: '#6aa0ff', // --home
        away: '#ff7d63', // --away
        draw: '#5d6f65', // --draw
        ok: '#52c58a', // --ok
        bad: '#ff8a73', // --bad
        // Alias lama (panel/line lama) diarahkan ke token baru agar
        // komponen yang belum disentuh tetap kontras & tidak rusak.
        panel: '#16241d',
      },
      fontFamily: {
        sans: ['Figtree', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['"Bricolage Grotesque"', 'Figtree', 'ui-sans-serif', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      fontSize: {
        // Guard: teks body minimal 15px, label minimal 13px
        xxs: ['0.6875rem', { lineHeight: '1rem' }], // 11px — hanya untuk angka kecil non-esensial
      },
      boxShadow: {
        panel: '0 1px 0 rgba(255,255,255,0.03) inset, 0 8px 24px rgba(0,0,0,0.25)',
        none: 'none',
      },
      borderRadius: {
        block: '16px', // blok utama
        elem: '8px', // elemen kecil
      },
    },
  },
  plugins: [],
}
