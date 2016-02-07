# The NatiVis Server
## Install
### Prerequisites
* django
* requests
* django-cors-headers
* lxml
* nltk

**Note: For windows, lxml usually should be installed from [wheel](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml) with `pip install lxml-3.5.0-cp27-none-win_amd64.whl`.**

### Note for installing lxml
**For windows:**

lxml should be installed from [wheel](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml).
```shell
pip install lxml-3.5.0-cp27-none-win_amd64.whl
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

**Note:**

**Currently the server is running on [http://166.111.139.15:8002]**

**A client can be accessed from [http://pi.cs.tsinghua.edu.cn/lab/nativis]**

## TODO
Restructure the project to include client code (since `tree.py` and `features.py` are shared).

Insert formula like this:

![equation](http://latex.codecogs.com/png.latex?1%2Bsin%28mc%5E2%29%0D%0A)

*Refferred from [here](http://stackoverflow.com/questions/12502440/markdown-formula-display-in-github)*

## Acknowledgement
This project is built on [Aloha Editor](https://github.com/alohaeditor/Aloha-Editor)
