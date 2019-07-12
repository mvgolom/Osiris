

# Name

## Requirements 
* [Python >= 3.6](https://www.python.org/downloads/)
* [MongoDB >= 3.8](https://www.mongodb.com/what-is-mongodb)
* [Virtualenv >= 15.0.0](https://virtualenv.pypa.io/en/latest/installation/)
### Create Virtual  Environment
~~~sh
virtualenv -p python3 venv
~~~
~~~python
-p #Set the python version virtualenv need to use
~~~
~~~python
venv #Name to a new virtual  environment
~~~

### Install Python Requirements
For this step you need instaled all items in [Requirements](##Requirements) and create a virtual  environment using **virtualenv**
1. Active virtual  environment
* For this we gonna to use the [source](https://bash.cyberciti.biz/guide/Source_command) command on linux
	~~~python
	source venv/bin/activate
	~~~
	After this step the name of virtual  environment will appear first on the terminal linux path like this.

	~~~sh
	(venv)[root@localhost ~]#
	~~~
2. Install Python requirements from the **requirements.txt** using the following command
	~~~sh
	pip install -r requirements.txt
	~~~
	Now we have installed all requirements to run the tool 

*If you need exit of virtualenv environment use this command.*
~~~sh
deactivate
~~~
# How to use

## Start Tool
With all requirements installed is time to prepare tool for run 
1. The first step is create and initialize database
	~~~sh
	python configInit.py
	~~~
After this step the tool is able to interact by command line or web interface

## Command Line
The simplest  interaction form to the tool with the tool, The command line allow 8 operations 
### Add projects to mining
~~~sh
python config.py --projects projects.json
~~~
*where need a json formatted* 
### Quantity of Finished Projects
~~~sh
python config.py --projects
~~~
### Add GitHub Keys 
~~~sh
python config.py --keys keys.json
~~~
*where need a json formatted* 
### Quantity of key in Database
~~~sh
python config.py --keys
~~~
### Quantity of finished projects
~~~sh
python config.py --finished
~~~
### Crawler Status
~~~sh
python config.py --status
~~~
status: ON/OFF
projects in database
completed projects
GitHub keys on in database
## Interface Web
To activate the Web Interface use this command.
~~~sh
python configWeb.py
~~~
The interface run in 
~~~url
http://localhost:5000/
~~~
projects CRUD can be found [here](http://localhost:5000/projects)
~~~url
http://localhost:5000/projects
~~~
GitHub keys CRUD can be found [here](http://localhost:5000/keys)
~~~url
http://localhost:5000/keys
~~~
### Database metrics to .CSV
Can you use command
~~~sh
python extractDataset.py
~~~
to extract all repositories metrics of database each to .csv file in ./results in project directory 
*for compatibility was used **#** instead of **/** in file name for each repository file*
*then*
**owner/repo**
*now*
**owner#repo**
##  JSON Valid Format
