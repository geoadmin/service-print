service-print
============


Print service for [https://map.geo.admin.ch], based on [MapFish Print v3](http://mapfish.github.io/)


# Print war

The war file `print-servlet-2.1.3-SNAPSHOT.war` is base on the mapfish-print 2.1.3 branch [#46d901520](https://github.com/mapfish/mapfish-print/commit/46d9015209fb2d975cee3f580bf387cd2f15b2e0)
with the patch `0001-do-not-recycle-connection.patch? applied.

# Getting started

Checkout the source code:

    git clone https://github.com/geoadmin/print-service.git

or when you're using ssh key (see https://help.github.com/articles/generating-ssh-keys):

    git clone git@github.com:geoadmin/print-service.git

# Docker


    curl localhost:8009/service-print-main/pdf/info.json
    {"scales":[{"name":"1:500","value":"500.0"},{"name":"1:1,000","value":"1000.0"},{"name":"1:2,500","value":"2500.0"},{"name":"1:5,000","value":"5000.0"},{"name":"1:10,000","value":"10000.0"},{"name":"1:20,000","value":"20000.0"},{"name":"1:25,000","value":"25000.0"},{"name":"1:50,000","value":"50000.0"},{"name":"1:100,000","value":"100000.0"},{"name":"1:200,000","value":"200000.0"},{"name":"1:300,000","value":"300000.0"},{"name":"1:500,000","value":"500000.0"},{"name":"1:1,000,000","value":"1000000.0"},{"name":"1:1,500,000","value":"1500000.0"},{"name":"1:2,500,000","value":"2500000.0"}],"dpis":[{"name":"150","value":"150"}],"outputFormats":[{"name":"pdf"}],"layouts":[{"name":"1 A4 landscape","map":{"width":802,"height":530},"rotation":true},{"name":"2 A4 portrait","map":{"width":550,"height":760},"rotation":true},{"name":"3 A3 landscape","map":{"width":1150,"height":777},"rotation":true},{"name":"4 A3 portrait","map":{"width":802,"height":1108},"rotation":true}],"printURL":"http://localhost:8009/service-print-main/pdf/print.pdf","createURL":"http://localhost:8009/service-print-main/pdf/create.json"}




    curl -H "Host: service-print.dev.bgdi.ch"  localhost:80/print/info.json
    {"scales":[{"name":"1:500","value":"500.0"},{"name":"1:1,000","value":"1000.0"},{"name":"1:2,500","value":"2500.0"},{"name":"1:5,000","value":"5000.0"},{"name":"1:10,000","value":"10000.0"},{"name":"1:20,000","value":"20000.0"},{"name":"1:25,000","value":"25000.0"},{"name":"1:50,000","value":"50000.0"},{"name":"1:100,000","value":"100000.0"},{"name":"1:200,000","value":"200000.0"},{"name":"1:300,000","value":"300000.0"},{"name":"1:500,000","value":"500000.0"},{"name":"1:1,000,000","value":"1000000.0"},{"name":"1:1,500,000","value":"1500000.0"},{"name":"1:2,500,000","value":"2500000.0"}],"dpis":[{"name":"150","value":"150"}],"outputFormats":[{"name":"pdf"}],"layouts":[{"name":"1 A4 landscape","map":{"width":802,"height":530},"rotation":true},{"name":"2 A4 portrait","map":{"width":550,"height":760},"rotation":true},{"name":"3 A3 landscape","map":{"width":1150,"height":777},"rotation":true},{"name":"4 A3 portrait","map":{"width":802,"height":1108},"rotation":true}],"printURL":"http://localhost:8009/service-print-main/pdf/print.pdf","createURL":"http://localhost:8009/service-print-main/pdf/create.json"}3


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




