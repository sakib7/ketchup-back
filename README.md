# Installation
Make sure the python on the host machine is at least 3.x.  

### Initiate virtual environment  
```
python -m venv .venv
```
This will create a folder called `.venv`, which contains the scripts to activate the virtual environment. After activate, all the pachages installed via `pip install <packagename>` will be installed in the `.venv` dir without messing up the global environment.  
  
**NB: Make sure to run:  
```.venv/Scripts/Activate.ps1```  (windows)   
or   
```.venv/Scripts/activate```(MacOS/Linux)   
everytime before actually doing anything (e.p. install packages/running server)**.  
  
#### Install neccessary packages
install these: 
```
pip install django
pip install djangorestframework
pip install djangorestframework-simplejwt
pip install django-cors-headers
pip install Pillow
pip install python-dotenv
pip install yagmail
pip install six
```
Then it should be able to run with:
```
python .\manage.py runserver
```
