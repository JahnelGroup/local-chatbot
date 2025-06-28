/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'chat-bg': '#f8fafc',
        'chat-user': '#3b82f6',
        'chat-bot': '#6b7280',
        'chat-input': '#f1f5f9',
      },
    },
  },
  plugins: [],
} 