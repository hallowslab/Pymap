# Requirements

## System
* grep
* tail
* imapsync

## App
* [Python](https://www.python.org/) >= 3.8.10
* [Poetry](https://python-poetry.org/), make sure to use the new script at https://python-poetry.org/docs/master/#installing-with-the-official-installer
* Web server -> [Gunicorn](https://gunicorn.org/)(Included by default)/[Tornado](https://www.tornadoweb.org/en/stable/)/[Apache](https://www.apache.org/)/[Nginx](https://www.nginx.com/) to serve the built React App
* [Redis-server](https://redis.com/)
* [Imapsync](https://github.com/imapsync/imapsync)
* NodeJS - LTS
* Database SQLite/MySQL (WIP)

# Initial setup
### See [requirements](#requirements)
**NOTE: poetry commands should be run in `pymap/src` folder**

- Clone the repo with submodules `git clone --recurse-submodules ....`
- Install the python requirements
  * `poetry install` -> As indicated above this should be run in `pymap/src`
- Rename the configuration files `pymap/src/server/config.json.template` (remove ".template"), and modify the configuration according to your setup
- Create database (When you have no current database)
  * `poetry run task initDB`
  * `poetry run task createDB`
- Add user with admin rights (Ignore this step if you have imported a database)
  * `poetry run task addAdmin` Will create a user named admin with the the password "CHANGE_ME"
  * You can also manually add admins for this you need to access the poetry shell to run everything in the right environment and context see [Advanced Usage](#advanced-usage)
* Build the client
 - Navigate to `pymap/src/client` and run `npm run build`
 - This will build the app to `pymap/src/build`, serve this with either flask or one of the webservers mentioned above

# Getting started

* Serve the client with any of the servers mentioned in [requirements - Web server](#requirements)
* if you decide to serve the client without flask you will still need to start the API (**You should also set the environment variable of FLASK_HEADLESS="True" or FLASK_HEADLESS=1, this will not register the routes to serve the build react app**)
* Start the API
  - `poetry run task apiProd` -> This will start 4 gunicorn workers for the API
* Start the celery worker
  - `poetry run task worker`


# Additional Info

* operator role is required for scheduling, archiving and cancelling tasks, and admin for  removal
* User logs are stored in redis under {username}_logs, application logs use an internal logging module that outputs to console and filesystem
* App logs are stored in the log directory in the pymap.log


# Advanced Usage

If you need to interact with the application for adding users or launch in debug mode, you will need to access the environment so that it recognizes the proper python interpreter and adittional packages, for this you can run the following command `poetry shell`

Now if you need to add a user manually you can do so by using the following command `flask --app manage create-user username email@address password` and it will instantiate the application context so the user can be added to the database

## Commands
- `create-db` -> Creates the database structure
- `create-admin USER PASSWORD` -> Will add the USER identified by PASSWORD with admin role to the database, the email address defaults to USER@pymap-localhost
- `create-user USER EMAIL PASSWORD -r ROLES` -> Will add the USER identified by PASSWORD with the supplied roles to the database, the roles are a comma separated list, they are optional and the default is operator

@app.cli.command("create-user")


# DEV

# Dockers (not used atm)
### Pymap
#### This assumes you are on the project root directory

* Building pymap
  - `docker build -f .\dockers\ubuntu20.04\Dockerfile -t pymap .`
* Running pymap
  - ports are exposed with the following syntax HOST:GUEST
  - `docker run --name pymap -it -p 5000:5000 -p20:20 -p21:21 -p22:22 -p 3001:3000 -t pymap`
  - press 2 to automagically configure zsh

#### TODO:
* Make a logo
* Add requeue functionality
* Add failsafe to pass --gmail or --office when it detects one of their hosts and the parameter missing
* There is a bug where sometimes the additional arguments on the client side do not get passed correctly to the API,
  probably something to do with React state, TODO: Ensure the arguments get loaded as soon as the APP is, or save the arguments
  in the database as a user property string 
* If running the CLI remove the pipe to /dev/null
* Add admin functionality (WIP)
* Configure logging for both Flask and Celery (WIP)

#### TOFIX
```
logsComponent.js:47 
 GET http://vps.edu:5000/api/v1/tasks/4b3dfa24-43d4-45c2-87da-e3701bb8e7d1 400 (BAD REQUEST)
logsComponent.js:52 Res is 
logsComponent.js:53 
{error: 'AttributeError', message: "'TaskRevokedError' object has no attribute 'get'"}
error
: 
"AttributeError"
message
: 
"'TaskRevokedError' object has no attribute 'get'"
[[Prototype]]
: 
Object
```

#### Notes

* [Configure poetry with VSCode](https://stackoverflow.com/a/64434542) 
 - `poetry config virtualenvs.in-project true`

### Bugs/Issues

- Celery on windows always pending ->
 * Issue on [github](https://github.com/celery/celery/issues/2146) / Thread on [SO](https://stackoverflow.com/a/27358974)
 * Command `celery -A server.tasks worker -E --loglevel debug --pool=solo`

### Celery notes
* Using eventlet and and redis