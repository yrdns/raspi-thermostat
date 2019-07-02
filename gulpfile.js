var gulp   = require("gulp");
var concat = require("gulp-concat");
var noop   = require("gulp-noop");
var rename = require("gulp-rename");
var terser = require("gulp-terser");

out_dir = "static";
js_out = "main.bundle.min.js";
css_out = "main.bundle.min.css";

js_files = ["node_modules/jquery/dist/jquery.min.js",
            "node_modules/moment/min/moment.min.js",
            "node_modules/chart.js/dist/Chart.min.js",
            "src/js/main.js"];

css_files = ["node_modules/chart.js/dist/Chart.min.css",
             "src/css/main.css"]

function buildJS(minify) {
    return gulp.src(js_files)
        .pipe(concat(js_out))
        .pipe(minify ? terser() : noop())
        .pipe(gulp.dest(out_dir))
}

gulp.task("build-js", function() { return buildJS(true); });
gulp.task("build-js-debug", function() { return buildJS(false); });

gulp.task("build-css", function () {
    return gulp.src(css_files)
        .pipe(concat(css_out))
        .pipe(gulp.dest(out_dir));
});

gulp.task("build-main", gulp.parallel("build-js", "build-css"));
gulp.task("build-main-debug", gulp.parallel("build-js-debug", "build-css"));

gulp.task("build", gulp.parallel("build-main"));
gulp.task("build-debug", gulp.parallel("build-main-debug"));

gulp.task("default", gulp.parallel("build"));

