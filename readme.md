# ts-commertials-remover
### What it does
ts-commertials-remover detects TV commertials banner/logo by simpliy running image matching with a giving template, and utilize ffmpeg to cut and concat to achieve the final output. This code is ugly and unpythonic, hopefully, it works.
### Run
```
python main.py
```
### Prequsitions
This project is compatible with both Python version 2 and 3.
- [retry-decorator](https://github.com/saltycrane/retry-decorator)
- opencv
- numpy
- m3u8
- ~~requests~~
- tqdm
