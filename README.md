# OCRmyPDFonWEB

## 修改内容

1. 使用 `GitHub Copilot Chat` 对代码进行了修改；

2. 更新 `ocrmypdf` 版本；

3. 使用 `flask` 替换 `streamlit`；

4. 大文件可上传到 `uploads` 文件夹，在 `使用已有文件` 标签中直接选取；

## 部署方法

```bash
docker-compose build --no-cache
docker-compose up -d
```
在浏览器中打开 `http://127.0.0.1:5000` 即可；

## 其他

1. 基于 [ocrmypdf/OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) 的容器 `jbarlow83/ocrmypdf-alpine`；

2. 语言包来源于 [tesseract-ocr/tessdata_best: Best (most accurate) trained LSTM models.](https://github.com/tesseract-ocr/tessdata_best)；



---
---
---

Streamlit Web UI for OCRmyPDF. Its codebase is tiny, so if you want to modify it, it should be straightforward. It is also stateless, making it easy to deploy. No volumes. No configuration.

![screenshot](screenshot.png "Screenshot")

## Requirements

* docker

## Usage

```
docker run --rm -p 127.0.0.1:8501:8501 razemio/ocrmypdfonweb
```

Open http://localhost:8501

## Develop

```
docker build -t razemio/ocrmypdfonweb:dev . # Only needed after you changed requirements.txt
docker run --rm -it -p 127.0.0.1:8501:8501 -v ${PWD}/server.py:/app/server.py razemio/ocrmypdfonweb:dev
```

Happy coding :)

## FAQ

### Why?

To keep your non-tech significant other happy. The terminal can be a dark place for some people.

### Why do you use OCRmyPDF version 12.7.2?
It is the last version which supports remove background. Which is somewhat impossible to find in normal PDF editors. Otherwise, OCRmyPDF works flawlessly, and I yet haven't found an issue which makes me want to upgrade.
