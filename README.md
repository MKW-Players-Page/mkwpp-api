# Mario Kart Wii Players' Page (API)

This is the backend portion of the new Players' Page site for MKW. The frontend is located in the
[mkwpp-web](https://github.com/MKW-Players-Page/mkwpp-web) repository.

## Project setup for local development

### Running the project

To get this project up and running, you'll need to have Docker installed on your machine. After
that, simply navigate to the root of the repository where the `Dockerfile` is located and run the
following command:

```.sh
docker compose up -d
```

This will run the app. On your first time running this, the required images will be downloaded and
the project's image will be built.

Now, the database needs to be configured and populated. The following steps only need to be done
once the first time you run this project.

### Migrating the database

The first thing you'll need to do is run the migrations. This will create all the database tables
needed by the application.

```.sh
docker compose exec app python manage.py migrate
```

If you now go to http://localhost:8000/admin/ on your browser, you should be greeted by the Django
admin site's login view.

### Creating the admin user

Next, you'll need an admin account to be able to log in. Run the following command and follow the
prompts.

```.sh
docker compose exec app python manage.py createsuperuser
```

You should now be able to log into the admin site using the credentials of the new superuser.

### Populating the database

Finally, for the app to be able to do anything useful, you'll need to populate the database with
some data. This project comes with fixtures for required data such as tracks and regions, as well
as player and score data extracted from the existing Players' Page.

```.sh
docker compose exec app python manage.py loaddata regions trackcups tracks standardlevels standards players scores
```

Once that is done, you will need to generate playerstats, which can be done by running:

```.sh
docker compose exec app python manage.py generate_playerstats
```

These are pretty heavy operations and may take up to a few minutes to run depending on your machine.

Congrats! You've successfully ran and set up the project. The next logical step is to set up the
frontend, for which instructions can be found
[in this repository](https://github.com/MKW-Players-Page/mkwpp-web).

## Contributing

If you want to contribute, please read the following guidelines.

### Pushing commits

Commits should not be pushed directly to the `main` branch. Instead, push to a separate branch and
create a pull request, and wait for a maintainer to review. There is no way to enforce this without
upgrading to a paid account, but do make sure to follow this rule. It would be greatly appreciated.

### Code quality

This repository has an automatic lint step on every commit running Flake8. Code must pass this test
before being approved and pushed to `main`. You can install it locally with `pip install flake8` and
run it simply with `flake8` at the root of the project.

### Adding dependencies

To add and external library to the project, install the package within the Docker container using
pip, then freeze the requirements.

```.sh
docker compose exec app pip install <package>
docker compose exec app pip freeze > requirements.txt
```

### Sharing database changes

If you create or update entries in the database and wish to share those changes, run the following
command:

```.sh
docker compose exec app python manage.py dumpdata <app_label>.<model_name> --indent 4 > <app_label>/fixtures/<model_name>.json
```

You would replace all instances of `<model_name>` with the (lowercase) name of the model and
`<app_label>` with the name of the app the model belongs to. For example, to dump all standards:

```.sh
docker compose exec app python manage.py dumpdata timetrials.standard --indent 4 > timetrials/fixtures/standards.json
```

Note that the plural form is used for the JSON file names.

## Project structure

This project uses Django as the framework with the Django REST framework library to create a
RESTful API for the React frontend to consume. An OpenAPI specification is automatically generated
by the DRF-spectacular package, as well as an interactive user interface using Swagger UI, which can
be accessed through the URL path `/api/schema/swagger-ui/`.

The `mkwpp` directory contains the project configuration. There are currently two apps, `core` and
`timetrials`. The `core` app only defines the custom user model, and the `timetrials` app contains
all the models, views, and logic needed to run the time trials leaderboard.
