# Downloader for Reddit
[![Made with Django](https://img.shields.io/badge/made%20with-Django-orange)](https://pypi.org/project/Django)
[![Build Status](https://travis-ci.com/Floyd-Droid/jf-reddit-downloader.svg?branch=master)](https://travis-ci.com/Floyd-Droid/jf-reddit-downloader)
![Python](https://img.shields.io/badge/python-3.9-blue.svg)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE.md)

This application gathers and downloads Reddit submission data, with or without a Reddit account. To see this project in action, visit https://jf-reddit-downloader.herokuapp.com

Simply log in with your Reddit account (or skip directly to the search form), then enter search criteria into the form. 
Once the desired submissions are selected, you can determine what kind of data to download:
(1) Submission metadata (as JSON)
(2) Comment metadata (as JSON)
(3) External data. Currently, this only includes image files of type jpg, png, or gif. All other types are ignored.

The files are generated on the server, placed into a zip file, and delivered to the user for download.

If authenticated through Reddit, a search history is kept. In addition, any search can be made a 'favorite' to quickly search again later on.


# Used Technologies

* Python 3.9
* HTML5
* CSS3
* JavaScript
* Bootstrap 4
* Django web framework 3.1.6
* PostgreSQL 12.4 (hosted by Heroku)

# Installation

Clone the repo and create a virtual environment within the project directory.
```bash
git clone https://github.com/Floyd-Droid/jf-issue-tracker.git
pip3 -m venv myenv
```

Activate the virtual environment.
```bash
# Linux and OSX
source myenv/bin/activate
# Windows
myenv\scripts\activate.bat
```

Install PostgreSQL, and use pip to install the other requirements.
```bash
pip3 install -r requirements.txt
```

# Deployment

To deploy your web application to Heroku, gather requirements into a text file, and make sure a Procfile is present. Git is required to deploy to Heroku, so commit all necessary project files.

Download the Heroku CLI toolbelt from the website. In the command line, login to your Heroku account with
```bash
heroku login
```
and provide your info. Create a new Heroku app, then push to master.
```bash
heroku create <app_name>
git push heroku master
```

Make migrations to Heroku's PostgreSQL database, and create a superuser for your Heroku app's admin site.
```bash
heroku run python manage.py makemigrations
heroku run python manage.py createsuperuser
```

You will also need to set Heroku's environment variables. For example, set the SECRET_KEY with
```bash
heroku config:set SECRET_KEY=a_key_that_is_secret
```
The same needs to be done for the DATABASE_URL, as well as any other variables.

# Author

Jourdon Floyd

email: jourdonfloyd@gmail.com

GitHub: https://github.com/Floyd-Droid

# License

This project is licensed under the MIT License - see the LICENSE.md file for details.