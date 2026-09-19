import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#f8fafc", // Clean light slate background
        surface: "#ffffff",    // Pure white surface
        card: "#ffffff",       // White cards
        border: "#e2e8f0",     // Crisp light gray border
        primary: "#059669",    // Emerald green
        "primary-hover": "#047857",
        accent: "#0284c7",
      },

      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
      }
    },
  },
  plugins: [],
};
export default config;
