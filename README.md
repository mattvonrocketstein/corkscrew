[About](#about) |
[Installation](#installation) |
[Configuration](#configuration) |
[CLI](#cli) |
[Testing](#testing) |


<a name="about">About</a>
=========================

I'll write something here one day.


<a name="installation">Installation</a>
=======================================

Stable stuff:

```shell
  $ pip install corkscrew
```

Freshest stuff:

```shell
  $ git clone https://github.com/mattvonrocketstein/corkscrew.git
  $ python setup.py develop
```


<a name="configuration">Sample .ini</a>
==================================

```ini
    [mongo]
    host=localhost
    db_name=some_db_name

    [proxy]
    /keys=https://github.com/your_username/keys

    [redirects]
    /gmail=https://gmail.com
    /github=/code

    [github]
    user=your_username

    [flask]
    app=your.flask.app
    host=0.0.0.0
    port=5000
    debug=false
    after_request=corkscrew.plumbing.after_request
    before_request=corkscrew.plumbing.before_request
    secret_key=random_string
    autoindex={'/url/path' : '~/filesystem/path'}

    [corkscrew]
    views=your.flask.app.views.__views__
    default_auth_next=/
    templates=corkscrew,your.flask.app
    runner=corkscrew.runner.flask
    logfile=~/corkscrew.log

    [users]
    admin=pbkdf2:sha1:hash
```

<a name="cli">Command Line</a>
==================================
  ```shell
    >corkscrew -h
    usage: corkscrew [-h] [-c CMD] [-e EXECFILE] [-v] [--shell]
                     [--config CONFIG] [--port PORT]
                     [--runner RUNNER] [--encode ENCODE]

    optional arguments:
      -h, --help            show this help message and exit
      -c CMD                just like python -c or sh -c (pass in a command)
      -e EXECFILE, --exec EXECFILE
                            a filename to execute
      -v, --version         show version information
      --shell               application shell
      --config CONFIG       use config file
      --port PORT           server listen port
      --runner RUNNER       dotpath for app server
      --encode ENCODE       encode password hash using werkzeug
  ```

<a name="jinja-filters">Jinja Filters</a>
=========================================

    * intcomma (humanize.intcomma)
    * nautraltime (humanize.naturaltime)
    * nautraldate (humanize.naturaldate)

<a name="jinja-filters">CSS / Javascript</a>
=============================================

<a name="testing">TESTING</a>
=============================

```shell
  $ cd corkscrew
  $ tox
```
