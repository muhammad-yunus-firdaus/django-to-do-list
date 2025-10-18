/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",  // Semua file HTML di dalam folder templates
    "./tugas/templates/**/*.html",  //  HTML ada di dalam tugas/templates
    "./static/**/*.js",       // Semua file JS di dalam static
    "./static/**/*.css",      // Semua file CSS di dalam static
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
