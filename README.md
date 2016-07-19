service-print
============


Print service for [https://map.geo.admin.ch], based on [MapFish Print v3](http://mapfish.github.io/)


# Getting started

Checkout the source code:

    git clone https://github.com/geoadmin/print-service.git

or when you're using ssh key (see https://help.github.com/articles/generating-ssh-keys):

    git clone git@github.com:geoadmin/print-service.git


Create a developer specific build configuration:

    touch rc_user_<username>

Add the port number in the newly created user rc file. You should at least edit your dev port. For instance:

    export SERVER_PORT=9000

Every variables you export in rc_user_<username> will override the default ones in rc_dev and rc_user.

Where "username" is your specific rc configuration. To create the specific build:

    make user

If you do this on mf1t, you need to make sure that a correct configuration exists under
    
    /var/www/vhosts/print-service/conf

that points to your working directory. If all is well, you can reach your pages at:

    http://print-service.dev.bgdi.ch/<username>/


## Deploying to dev, int, prod and demo

Do the following commands **inside your working directory**. Here's how a standard
deploy process is done.

`make deploydev SNAPSHOT=true`

This updates the source in /var/www... to the latest master branch from github,
creates a snapshot and runs nosetests against the test db. The snapshot directory
will be shown when the script is done. *Note*: you can omit the `-s` parameter if
you don't want to create a snapshot e.g. for intermediate releases on dev main.

Once a snapshot has been created, you are able to deploy this snapshot to a
desired target. For integration, do

`make deployint SNAPSHOT=201512011411`

This will run the full nose tests **from inside the 201512011411 snapshot directory** against the **integration db cluster**. Only if these tests are successfull, the snapshot is deployed to the integration cluster.

`make deployprod SNAPSHOT=201512011411`

This will do the corresponding thing for prod (tests will be run **against prod backends**)
The same is valid for demo too:

`make deploydemo SNAPSHOT=201512011411`

You can disable the running of the nosetests against the target backends by adding
`notests` parameter to the snapshot command. This is handy in an emergency (when
deploying an old known-to-work snapshot) or when you have to re-deploy
a snapshot that you know has passed the tests for the given backend.
To disable the tests, use the following command:

`make deployint SNAPSHOT=201512011411 NO_TESTS=notests`

Use `notests` parameter with care, as it removes a level of tests.

Per default the deploy command uses the deploy configuration of the snapshot directory.
If you want to use the deploy configuration of directory from which you are executing this command, you can use:

`make deployint SNAPSHOT=201512011411 DEPLOYCONFIG=from_current_directory`


## Python Code Styling

We are currently using the FLAKES 8 convention for Python code.
You can find more information about our code styling here:

    http://www.python.org/dev/peps/pep-0008/
    http://pep8.readthedocs.org/en/latest/index.html

You can find additional information about autopep8 here:

    https://pypi.python.org/pypi/autopep8/

To check the code styling:

  ```bash
make lint
  ```

To autocorrect most linting mistakes

  ```bash
make autolint
  ```

*Add a pre-commit hook*

1. Create a pre-commit file

  ```bash
touch .git/hooks/pre-commit
  ```

2. Copy/paste the following script

  ```bash
#!/bin/bash

make lint
if [[ $? != 0 ]];
then
  echo "$(tput setaf 1) Nothing has been commited because of styling issues, please fix it according to the comments above $(tput sgr0)"
  exit 1
fi
  ```

3. Make this it executable

  ```bash
chmod +x .git/hooks/pre-commit
  ```

Now commits will be aborted if styling is not respected
