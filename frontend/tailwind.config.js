/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b1220",
        panel: "#121a2b",
        panel2: "#1a2436",
        brand: "#2f81f7",
        danger: "#ef4444",
        warn: "#f59e0b",
        ok: "#22c55e",
      },
    },
  },
  plugins: [],
};
