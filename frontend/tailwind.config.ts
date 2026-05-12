import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Aptos"', '"Sohne"', '"IBM Plex Sans"', "ui-sans-serif", "system-ui"],
        numeric: ['"Aptos"', '"DIN Alternate"', "ui-sans-serif", "system-ui"]
      },
      boxShadow: {
        panel: "0 22px 70px color-mix(in oklch, black 48%, transparent)"
      }
    }
  },
  plugins: []
} satisfies Config;
