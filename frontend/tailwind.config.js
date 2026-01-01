/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        // Modern monospaced font stack for numeric data
        // Prioritizes system fonts for performance and native look
        mono: [
          'SF Mono',              // macOS/iOS
          'Monaco',               // macOS fallback
          'Cascadia Code',        // Windows 11
          'Consolas',             // Windows fallback
          'Liberation Mono',      // Linux
          'Courier New',          // Universal fallback
          'monospace'             // System default
        ],
      },
    },
  },
  plugins: [],
}
