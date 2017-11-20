Print Service
=============


Print service for [https://map.geo.admin.ch], based on [MapFish Print v2](http://mapfish.github.io/)
It uses the standard *mapfish print protocol* of [MapFish Print v2](http://www.mapfish.org/doc/print/),
extended for multipages print.


# Architecture

## Elastic Load Balancer

* //vpc-lb-print-(dev|int|prod).intra.bgdi.ch

## Elastic File System
A r/w EFS for application, mounted in docker container on _/var/local/print_

* fs-080aa4c1.efs.eu-west-1.amazonaws.com://print/(dev|int|prod)

## Docker containers

* **nginx**, responding on port 8009, dispatching requests on various backend
* **flask** application, on port 8010, to split the *multipages* requests into
  single ones, and then merge them into a single pdf document
* **tomcat**, with a single application *service-print-main* responding on 8011
                                                                                                                                       
                                                                                                                      
  Nginx:8009               Flask (wsgi) :8010                Tomcat 8011                  EFS  
                                                                                                  
+----------------+         +-------------+                                          +-----------+
|                |         |             |          write assembled pages           |           |
|                |         | split into  |----------------------------------------->|           |
| /printmulti    | ------> | single page |        get single pages                  |           |
| /printprogress |         |   print     |<---------------------------------------- |           |
| /printcancel   |         |             |                                          |           |
|                |         |             | prints    +-------------------+          |           |
|                |         |             |-----------|                   | -------> |           |
|                |         |             | single    |                   |          |           |
|                |         +-------------+ page      |/service-print-main|          |           |
|                |                                   |                   |          |           |
|                |                                   |                   |          |           |
|                |                                   |                   |          |           |
|                |     single page print             |                   |  writes  |           |
|  /print        |-----------------------------------|                   |--------> |           |
|                |                                   |                   |          |           |
|                |        -                          |                   |          |           |
|                |                                   |                   |          |           |
|                |                                   |                   |          |           |
|                |                                   |                   |          |           |
| /(.*).pdf      |                                   +-------------------+          |           |
|                | <--------------------------------------------------------------  |           |
+----------------+                         retrieve PDFs                            |           |
                                                                                    |           |
                                                                                    +-----------+

                                                         
                                                                                            
# Endpoint

 print.geo.admin.ch and service-print.(dev|int|prod).bgdi.ch

 ELB: //vpc-lb-print-(dev|int|prod).intra.bgdi.ch:8009


# URI

    Apache/Nginx                                Flask/WSGI                                  Tomcat
   
    GET  /print/info.json                                                      GET /service-print-main/pdf/info.json
    
    POST /print/create.json                                                    POST /service-print-main/pdf/create.json
    
    POST /printmulti/create.json           POST /printmulti/create.json
    
    GET  /printprogress?id=232323          GET /printprogress?id=232323
    
    GET  /printcancel                      GET /printcancel                             EFS (/var/local/print
                                                                                        
    GET /print/-multi23444545.pdf.printout                                     mapfish-print-multi23444545.pdf.printout
    GET /print/9032936254995330149.pdf.printout                                mapfish-print9032936254995330149.pdf.printout


# Getting started

Checkout the source code:

    git clone https://github.com/geoadmin/print-service.git

or when you're using ssh key (see https://help.github.com/articles/generating-ssh-keys):


    make user

# Flask WSGI application

`Flask` alone development:

    make server
    
or serving with `gunicorn`

    make gunicornserver
    
# Tomcat

The war file `print-servlet-2.1.3-SNAPSHOT.war` is based on the mapfish-print 2.1.3 branch [#46d901520](https://github.com/mapfish/mapfish-print/commit/46d9015209fb2d975cee3f580bf387cd2f15b2e0)

If you update files in the `tomcat` directory, you'll have to rebuild the `.war` file
using the command:

    make printwar

This generate a new  file *service-print-main.war* using the `BASEWAR` war file.


# Docker

## Building

   make composetemplatedev dockerbuild

This build three docker images, labeled `staging`:

    swisstopo/service-print          staging               538532a4bed5        2 minutes ago       374.5 MB
    swisstopo/service-print-nginx    staging               f67aa9b5baa1        35 hours ago        152.3 MB
    swisstopo/service-print-tomcat   staging               17c35a184a46        4 days ago          424.7 MB


## Running locally

    make dockerrun

or

   docker-compose up
   
   
# Testing  

## Checker




## Tomcat

    curl localhost:8009/service-print-main/pdf/info.json
    {"scales":[{"name":"1:500","value":"500.0"},{"name":"1:1,000","value":"1000.0"},{"name":"1:2,500","value":"2500.0"},{"name":"1:5,000","value":"5000.0"},{"name":"1:10,000","value":"10000.0"},{"name":"1:20,000","value":"20000.0"},{"name":"1:25,000","value":"25000.0"},{"name":"1:50,000","value":"50000.0"},{"name":"1:100,000","value":"100000.0"},{"name":"1:200,000","value":"200000.0"},{"name":"1:300,000","value":"300000.0"},{"name":"1:500,000","value":"500000.0"},{"name":"1:1,000,000","value":"1000000.0"},{"name":"1:1,500,000","value":"1500000.0"},{"name":"1:2,500,000","value":"2500000.0"}],"dpis":[{"name":"150","value":"150"}],"outputFormats":[{"name":"pdf"}],"layouts":[{"name":"1 A4 landscape","map":{"width":802,"height":530},"rotation":true},{"name":"2 A4 portrait","map":{"width":550,"height":760},"rotation":true},{"name":"3 A3 landscape","map":{"width":1150,"height":777},"rotation":true},{"name":"4 A3 portrait","map":{"width":802,"height":1108},"rotation":true}],"printURL":"http://localhost:8009/service-print-main/pdf/print.pdf","createURL":"http://localhost:8009/service-print-main/pdf/create.json"}




    curl -H "Host: service-print.dev.bgdi.ch"  localhost:80/print/info.json
    {"scales":[{"name":"1:500","value":"500.0"},{"name":"1:1,000","value":"1000.0"},{"name":"1:2,500","value":"2500.0"},{"name":"1:5,000","value":"5000.0"},{"name":"1:10,000","value":"10000.0"},{"name":"1:20,000","value":"20000.0"},{"name":"1:25,000","value":"25000.0"},{"name":"1:50,000","value":"50000.0"},{"name":"1:100,000","value":"100000.0"},{"name":"1:200,000","value":"200000.0"},{"name":"1:300,000","value":"300000.0"},{"name":"1:500,000","value":"500000.0"},{"name":"1:1,000,000","value":"1000000.0"},{"name":"1:1,500,000","value":"1500000.0"},{"name":"1:2,500,000","value":"2500000.0"}],"dpis":[{"name":"150","value":"150"}],"outputFormats":[{"name":"pdf"}],"layouts":[{"name":"1 A4 landscape","map":{"width":802,"height":530},"rotation":true},{"name":"2 A4 portrait","map":{"width":550,"height":760},"rotation":true},{"name":"3 A3 landscape","map":{"width":1150,"height":777},"rotation":true},{"name":"4 A3 portrait","map":{"width":802,"height":1108},"rotation":true}],"printURL":"http://localhost:8009/service-print-main/pdf/print.pdf","createURL":"http://localhost:8009/service-print-main/pdf/create.json"}3

## Taging images and deploy to Docker Hub

# Rancher

## Deploy to int




