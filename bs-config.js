module.exports = {
  proxy: "http://127.0.0.1:5000",
  files: [
    "templates/**/*.html",
    "static/**/*.css",
    "static/**/*.js"
  ],
  port: 3000,
  open: true,
  notify: false,
  reloadDelay: 200
};
