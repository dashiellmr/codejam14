/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        'beige': '#FFF8EE',
        'pink': '#FFEAEA' ,
        'green': '#CCECBF',
        'brown': '#D5B569',
        'light-blue': '#D5EEFF',
        'dark-blue': '#A5D6F9',
      },
    },
  },
  plugins: [],
}