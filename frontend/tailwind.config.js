/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,jsx}", "./components/**/*.{js,jsx}", "./lib/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: { indigo: "#6c63ff", teal: "#4db6ac", pink: "#f06292", navy: "#3d4a6b" },
      },
    },
  },
  plugins: [],
};