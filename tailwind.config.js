/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.{html,js}"],
  theme: {
   
    extend: { colors: {
      'beige': '#FFF8EE',
      'pink': '#FFEAEA' ,
      'green': '#CCECBF',
      'brown': '#D5B569',
      'lightergreen': '#E4F2DE',
      'lightblue':'#D5EEFF',
      'darkblue': '#A5D6F9',
    },},
  },
  plugins: [],
}