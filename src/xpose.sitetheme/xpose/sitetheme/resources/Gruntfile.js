/* jshint node: true */
'use strict';

module.exports = function (grunt) {

  // load all grunt tasks
  require('load-grunt-tasks')(grunt);

  // Project configuration.
  grunt.initConfig({

    // Metadata.
    pkg: grunt.file.readJSON('package.json'),
    banner: '/*!\n' +
            '* Xposeo Theme v<%= pkg.version %> by meetshaus\n' +
            '* Copyright <%= pkg.author %>\n' +
            '* Licensed under <%= pkg.licenses %>.\n' +
            '*\n' +
            '* Designed and built by meetshaus\n' +
            '*/\n',
    jqueryCheck: 'if (typeof jQuery === "undefined") { throw new Error(\"We require jQuery\") }\n\n',

    // Task configuration.
    clean: {
      dist: ['dist']
    },

    jshint: {
      options: {
        jshintrc: 'js/.jshintrc'
      },
      gruntfile: {
        src: 'Gruntfile.js'
      },
      src: {
        src: ['js/*.js']
      },
      test: {
        src: ['js/tests/unit/*.js']
      }
    },

    concat: {
      options: {
        banner: '<%= banner %>',
        stripBanners: false
      },
      dist: {
        src: [
          'bower_components/jquery/jquery.js',
          'bower_components/modernizr/modernizr.js',
          'bower_components/bootstrap/dist/js/bootstrap.js',
          'bower_components/momentjs/moment.js',
          'bower_components/momentjs/lang/de.js',
          'bower_components/livestampjs/livestamp.js',
          'bower_components/raphael/raphael.js',
          'bower_components/morris.js/morris.js',
          'assets/js/classie.js',
          'js/application.js'
        ],
        dest: 'dist/js/<%= pkg.name %>.js'
      },
      theme: {
        src: [
        'bower_components/bootstrap/dist/js/bootstrap.js',
        'bower_components/momentjs/moment.js',
        'bower_components/momentjs/lang/de.js',
        'bower_components/livestampjs/livestamp.js',
        'bower_components/raphael/raphael.js',
        'bower_components/morris.js/morris.js',
        'assets/js/classie.js',
        'js/application.js'
        ],
        dest: 'dist/js/main.js'
      }
    },

    uglify: {
      options: {
        banner: '<%= banner %>'
      },
      dist: {
        src: ['<%= concat.dist.dest %>'],
        dest: 'dist/js/<%= pkg.name %>.min.js'
      }
    },

    less: {
      compileTheme: {
        options: {
          strictMath: false,
          sourceMap: true,
          outputSourceFiles: true,
          sourceMapURL: '<%= pkg.name %>.css.map',
          sourceMapFilename: 'dist/css/<%= pkg.name %>.css.map'
        },
        files: {
          'dist/css/<%= pkg.name %>.css': 'less/styles.less'
        }
      },
      minify: {
        options: {
          cleancss: true,
          report: 'min'
        },
        files: {
          'dist/css/<%= pkg.name %>.min.css': 'dist/css/<%= pkg.name %>.css'
        }
      }
    },

    csscomb: {
      sort: {
        options: {
          config: 'less/.csscomb.json'
        },
        files: {
          'dist/css/<%= pkg.name %>.css': ['dist/css/<%= pkg.name %>.css']
        }
      }
    },


    copy: {
      fonts: {
        expand: true,
        flatten: true,
        src: [
        'bower_components/font-awesome/fonts/*',
        'assets/font/*'
        ],
        dest: 'dist/assets/fonts/'
      },
      ico: {
        expand: true,
        flatten: true,
        cwd: 'bower_components/',
        src: ['bootstrap/assets/ico/*'],
        dest: 'dist/assets/ico/'
      },
      images: {
        expand: true,
        flatten: true,
        src: ['assets/img/*'],
        dest: 'dist/assets/img/'
      },
      animations: {
        expand: true,
        flatten: true,
        src: ['bower_components/animate.css/*.css'],
        dest: 'dist/css/'
      }
    },
    imagemin: {
      dynamic: {
        files: [{
          expand: true,
          cwd: 'assets/img/',
          src: ['**/*.{png,jpg,gif}'],
          dest: 'dist/assets/img/'
        }]
      }
    },
    rev: {
      options:  {
        algorithm: 'sha256',
        length: 8
      },
      files: {
        src: ['dist/**/*.{js,css,png,jpg}']
      }
    },
    qunit: {
      options: {
        inject: 'js/tests/unit/phantom.js'
      },
      files: ['js/tests/*.html']
    },
    connect: {
      server: {
        options: {
          port: 3000,
          base: '.'
        }
      }
    },
    jekyll: {
      theme: {}
    },
    sed: {
      cleanAssetsDir: {
        path: 'dist/',
        pattern: '../../assets/',
        replacement: '../assets/',
        recursive: true
      },
      cleanSourceCSS: {
        path: 'dist/',
        pattern: '../dist/css/styles.css',
        replacement: 'css/styles.css',
        recursive: true
      },
      cleanSourceJS: {
        path: 'dist/',
        pattern: '../dist/js/rms.js',
        replacement: 'js/rms.min.js',
        recursive: true
      },
      cleanLogo: {
        path: 'dist/',
        pattern: '../assets/img/logo.png',
        replacement: '/++theme++xpose.sitetheme/assets/img/logo.png'
      }
    },

    validation: {
      options: {
        charset: 'utf-8',
        doctype: 'HTML5',
        failHard: true,
        reset: true,
        relaxerror: [
        'Bad value X-UA-Compatible for attribute http-equiv on element meta.',
        'Element img is missing required attribute src.'
        ]
      },
      files: {
        src: ['_site/**/*.html']
      }
    },

    watch: {
      src: {
        files: '<%= jshint.src.src %>',
        tasks: ['jshint:src', 'qunit']
      },
      test: {
        files: '<%= jshint.test.src %>',
        tasks: ['jshint:test', 'qunit']
      },
      recess: {
        files: 'less/*.less',
        tasks: ['recess']
      },
      templates: {
        files: '*.html',
        tasks: ['jekyll:theme']
      }
    },

    concurrent: {
      cj: ['recess', 'copy', 'concat', 'uglify'],
      ha: ['jekyll:theme', 'copy-templates', 'sed']
    }

  });


  // -------------------------------------------------
  // These are the available tasks provided
  // Run them in the Terminal like e.g. grunt dist-css
  // -------------------------------------------------

  // Prepare distrubution
  grunt.registerTask('dist-init', '', function () {
      grunt.file.mkdir('dist/assets/');
  });

  // Copy jekyll generated templates and rename for diazo
  grunt.registerTask('copy-templates', '', function () {
      grunt.file.copy('_site/index.html', 'dist/index.html');
      grunt.file.copy('_site/signin/index.html', 'dist/signin.html');
      grunt.file.copy('_site/theme/index.html', 'dist/theme.html');
      grunt.file.copy('_site/dashboard/index.html', 'dist/dashboard.html');
  });

  // Docs HTML validation task
  grunt.registerTask('validate-html', ['jekyll', 'validation']);

  // Javascript Unittests
  grunt.registerTask('unit-test', ['qunit']);

  // Test task.
  var testSubtasks = ['dist-css', 'jshint', 'validate-html'];

  grunt.registerTask('test', testSubtasks);

  // JS distribution task.
  grunt.registerTask('dist-js', ['concat', 'uglify']);

  // CSS distribution task.
  grunt.registerTask('less-compile', ['less:compileTheme']);
  grunt.registerTask('dist-css', ['less-compile', 'csscomb', 'less:minify']);

  // Assets distribution task.
  grunt.registerTask('dist-assets', ['newer:copy', 'newer:imagemin']);

  // Cache buster distribution task.
  grunt.registerTask('dist-cb', ['rev']);

  // Template distribution task.
  grunt.registerTask('dist-html', ['jekyll:theme', 'copy-templates', 'sed']);

  // Concurrent distribution task
  grunt.registerTask('dist-cc', ['test', 'concurrent:cj', 'concurrent:ha']);

  // Development task.
  grunt.registerTask('dev', ['dist-css', 'dist-js', 'dist-html']);

  // Full distribution task.
  grunt.registerTask('dist', ['clean', 'dist-css', 'dist-js', 'dist-html', 'dist-assets']);

  // Default task.
  grunt.registerTask('default', ['dist-cc']);
};