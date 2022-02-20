# ts-commertials-remover
### What it does
ts-commertials-remover detects TV commertials banner/logo by simpliy running image matching with giving template, and utilize ffmpeg to cut and concat to achievn the final output. The code is ugly and unpythonic, hopefully, it works.
### Run
```
python2 qiantanglaoniangjiu_main.py
```
### Prequsitions
This project is wrote in Python 2.7, but I think it won't take took long to migr
ate to Python 3.7. Hope I will do it one day.
- [retry-decorator](https://github.com/saltycrane/retry-decorator)
- opencv
- numpy
- m3u8
