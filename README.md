# The NatiVis Server
## Install
### Prerequisites
* django
* requests
* django-cors-headers
* lxml
* nltk

### Note for installing lxml
**For windows:**

lxml should be installed from [wheel](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml).
```shell
pip install lxml‑3.5.0‑cp27‑none‑win_amd64.whl
```

**For ubuntu server 14.04.3 (64 bit):**

lxml should be installed as follows.
```shell
sudo apt-get install libxml2-dev libxslt1-dev python-dev zlib1g-dev 
pip install lxml
```
*Refferred from [here](http://stackoverflow.com/questions/6504810/how-to-install-lxml-on-ubuntu)*

## Running
```shell
python manage.py runserver 0.0.0.0:8002
```
**Note: Currently it is running on [http://166.111.139.15:8002]**
