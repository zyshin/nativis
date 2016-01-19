# The NatiVis Server
## Install
### Prerequisites
* django
* requests
* django-cors-headers
* lxml
* nltk

**Note: For windows, lxml usually should be installed from [wheel](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml) with `pip install lxml-3.5.0-cp27-none-win_amd64.whl`.**

## Running
```shell
python manage.py runserver 0.0.0.0:8002
```

**Note:**
**Currently the server is running on [http://166.111.139.15:8002]**
**A client can be accessed from [http://pi.cs.tsinghua.edu.cn/lab/nativis]**

## TODO
Restructure the project to include client code (since `tree.py` and `features.py` are shared).

## Acknowledgement
This project is built on [Aloha Editor](https://github.com/alohaeditor/Aloha-Editor)
