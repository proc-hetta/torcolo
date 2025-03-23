# Torcolo

Torcolo is a simple storage server general purpose. It is not developed to be used in enterprise production environment as it is mainly developed for fun. There is no security check regarding file dimensions and similar stuffs, feel free to contribute with as many pull-requests as you want to expand the software with new features.

The software is used to host and provide on demand resources for [/proc/hetta](https://blog.prochetta.best) projects.

## Technologies

As it has to be a simple server, without strict requirements in terms of efficiency, the selected technology is python, with [Flask](https://flask.palletsprojects.com/) as web application framework. Database communication is implemented using SQLAlchemy 2.X, with particular focus to use it in a backend-agnostic manner.

Stored file maximum dimension is related to selected backend configuration and capabilities. As an example, if [SQLite](https://www.sqlite.org/) is used the default maximum file dimension is [1GB](https://www.sqlite.org/limits.html), raisable until 2GB

## Usage
