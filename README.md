service-print
============


Print service for [https://map.geo.admin.ch], based on [MapFish Print v3](http://mapfish.github.io/)


# Getting started

Checkout the source code:

    git clone https://github.com/geoadmin/print-service.git

or when you're using ssh key (see https://help.github.com/articles/generating-ssh-keys):

    git clone git@github.com:geoadmin/print-service.git


Create a developer specific build configuration:

    cp rc_example rc_user_<username>

Change the port number in the newly created buildout configuration file (In dev mode)

Where "username" is your specific rc configuration. To create the specific build:

    make user

If you do this on mf1t, you need to make sure that a correct configuration exists under
    
    /var/www/vhosts/print-service/conf

that points to your working directory. If all is well, you can reach your pages at:

    http://print-service.dev.bgdi.ch/<username>/

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
