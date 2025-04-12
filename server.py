import os
import tempfile
import subprocess
import logging
import base64
import sys
from datetime import datetime
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename

# 配置日志 - 增强日志设置，确保信息被打印出来
logging.basicConfig(
    # level=logging.DEBUG,  # 修改为DEBUG级别以显示更多日志
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("ocrmypdf.log"),
        logging.StreamHandler(sys.stdout)  # 明确指定输出到标准输出
    ]
)

# 添加一条启动日志，确认日志系统正常工作
logging.info("OCRmyPDF Web服务开始启动")

app = Flask(__name__)
app.secret_key = 'ocrmypdf_web_secret_key'
app.config['UPLOAD_FOLDER'] = '/tmp'

# 从环境变量读取最大上传文件大小，默认为128MB
max_content_length = os.environ.get('MAX_CONTENT_LENGTH')
if max_content_length:
    try:
        app.config['MAX_CONTENT_LENGTH'] = int(max_content_length)
        logging.info(f"设置最大上传文件大小为: {app.config['MAX_CONTENT_LENGTH']} 字节 ({app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024):.2f} MB)")
    except ValueError:
        logging.warning(f"无效的MAX_CONTENT_LENGTH值: {max_content_length}，使用默认值500MB")
        app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 默认限制为500MB
else:
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 默认限制为500MB
    logging.info(f"使用默认最大上传文件大小: {app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024):.2f} MB")

# 设置其他Flask配置
app.config['MAX_CONTENT_PATH'] = None  # 禁用路径长度限制
app.config['UPLOAD_FOLDER'] = '/tmp'

# 创建必要的目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# OCR处理函数
def process_pdf_file(input_path, options):
    """处理PDF文件，应用OCR并返回新文件路径"""
    try:
        # 定义输出路径
        output_path = input_path + '_ocr.pdf'
        
        # 获取OCR选项
        ocr_enabled = options.get('ocr_enabled', True)
        language = options.get('language', 'eng+chi_sim')
        deskew = options.get('deskew', False)
        optimize_level = options.get('optimize_level', 1)
        rotate_pages = options.get('rotate_pages', False)
        remove_background = options.get('remove_background', False)
        force_ocr = options.get('force_ocr', False)
        
        # 构建OCRmyPDF命令
        cmd = ['ocrmypdf', '--optimize', str(optimize_level)]
        
        # 添加语言选项
        if language:
            cmd.extend(['-l', language])
        
        # 添加其他选项
        if deskew:
            cmd.append('--deskew')
        
        if rotate_pages:
            cmd.append('--rotate-pages')
        
        if remove_background:
            cmd.append('--remove-background')
        
        if force_ocr:
            cmd.append('--force-ocr')
            
        if not ocr_enabled:
            cmd.append('--skip-text')
        
        # 添加引擎选项
        cmd.extend(['--pdf-renderer', 'hocr'])
        cmd.extend(['--tesseract-oem', '1'])
        
        # 添加输入和输出路径
        cmd.extend([input_path, output_path])
        
        # 运行OCRmyPDF命令
        process = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True
        )
        
        # 检查处理结果
        if process.returncode != 0:
            logging.error(f"OCR处理失败: {process.stderr}")
            return None
        
        return output_path
    
    except Exception as e:
        logging.exception(f"处理文件时出错: {str(e)}")
        return None

# 生成HTML模板
@app.route('/')
def index():
    # 获取/tmp目录下的所有PDF文件
    pdf_files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.lower().endswith('.pdf') and not filename.lower().endswith('_ocr.pdf'):
            pdf_files.append(filename)
    
    # 生成简单的HTML页面
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OCRmyPDF Web 界面</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            .header {
                text-align: center;
                color: #1E88E5;
                margin-bottom: 30px;
            }
            .container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
            }
            .column {
                flex: 1;
                min-width: 300px;
            }
            .section {
                background-color: #f9f9f9;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .section-title {
                font-size: 18px;
                margin-bottom: 15px;
                color: #333;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
            }
            input, select {
                width: 100%;
                padding: 8px;
                box-sizing: border-box;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            input[type="checkbox"] {
                width: auto;
                margin-right: 10px;
            }
            input[type="submit"] {
                background-color: #1E88E5;
                color: white;
                border: none;
                padding: 10px 20px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 20px;
            }
            input[type="submit"]:hover {
                background-color: #1976D2;
            }
            .info-box {
                background-color: #E3F2FD;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .file-input {
                margin-top: 20px;
            }
            .sidebar {
                background-color: #f0f0f0;
                padding: 20px;
                border-radius: 8px;
            }
            .message {
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .success {
                background-color: #D5F5E3;
                color: #1E8449;
            }
            .error {
                background-color: #FADBD8;
                color: #C0392B;
            }
            .tabs {
                display: flex;
                margin-bottom: 20px;
            }
            .tab {
                padding: 10px 20px;
                cursor: pointer;
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-bottom: none;
                border-radius: 5px 5px 0 0;
                margin-right: 5px;
            }
            .tab.active {
                background-color: #1E88E5;
                color: white;
            }
            .tab-content {
                display: none;
            }
            .tab-content.active {
                display: block;
            }
            .file-list {
                max-height: 200px;
                overflow-y: auto;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                margin-bottom: 15px;
            }
            .file-item {
                padding: 8px;
                border-bottom: 1px solid #eee;
                cursor: pointer;
            }
            .file-item:hover {
                background-color: #f5f5f5;
            }
            .file-item.selected {
                background-color: #E3F2FD;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>OCRmyPDF Web 界面</h1>
        </div>
        
        <div class="container">
            <div class="column">
                <div class="tabs">
                    <div class="tab active" onclick="switchTab('upload-tab')">上传新文件</div>
                    <div class="tab" onclick="switchTab('existing-tab')">使用已有文件</div>
                </div>
                
                <div id="upload-tab" class="tab-content active">
                    <form action="/upload" method="post" enctype="multipart/form-data">
                        <div class="section">
                            <h2 class="section-title">OCR选项</h2>
                            
                            <div class="form-group">
                                <input type="checkbox" id="ocr_enabled" name="ocr_enabled" value="true" checked>
                                <label for="ocr_enabled">启用OCR文字识别</label>
                            </div>
                            
                            <div class="form-group">
                                <label for="language">识别语言</label>
                                <select id="language" name="language">
                                    <option value="eng">英语</option>
                                    <option value="chi_sim">简体中文</option>
                                    <option value="eng+chi_sim">英语+简体中文</option>
                                    <option value="chi_sim_vert">简体中文垂直文本</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="optimize_level">文件优化级别 (0=不优化; 1=无损优化; 2=轻度有损; 3=最大压缩)</label>
                                <input type="range" id="optimize_level" name="optimize_level" min="0" max="3" value="1">
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2 class="section-title">高级选项</h2>
                            
                            <div class="form-group">
                                <input type="checkbox" id="deskew" name="deskew" value="true">
                                <label for="deskew">自动校正倾斜</label>
                            </div>
                            
                            <div class="form-group">
                                <input type="checkbox" id="rotate_pages" name="rotate_pages" value="true">
                                <label for="rotate_pages">自动旋转页面</label>
                            </div>
                            
                            <div class="form-group">
                                <input type="checkbox" id="remove_background" name="remove_background" value="true">
                                <label for="remove_background">移除背景</label>
                            </div>
                            
                            <div class="form-group">
                                <input type="checkbox" id="force_ocr" name="force_ocr" value="true">
                                <label for="force_ocr">强制OCR</label>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2 class="section-title">上传PDF文件</h2>
                            
                            <div class="info-box">
                                上传PDF文件后，系统将根据您选择的设置自动处理。请等待处理完成。
                            </div>
                            
                            <div class="file-input">
                                <input type="file" name="pdf_file" accept=".pdf" required>
                            </div>
                            
                            <input type="submit" value="上传并处理">
                        </div>
                    </form>
                </div>
                
                <div id="existing-tab" class="tab-content">
                    <form action="/process-existing" method="post">
                        <div class="section">
                            <h2 class="section-title">OCR选项</h2>
                            
                            <div class="form-group">
                                <input type="checkbox" id="ocr_enabled_ex" name="ocr_enabled" value="true" checked>
                                <label for="ocr_enabled_ex">启用OCR文字识别</label>
                            </div>
                            
                            <div class="form-group">
                                <label for="language_ex">识别语言</label>
                                <select id="language_ex" name="language">
                                    <option value="eng">英语</option>
                                    <option value="chi_sim">简体中文</option>
                                    <option value="eng+chi_sim">英语+简体中文</option>
                                    <option value="chi_sim_vert">简体中文垂直文本</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="optimize_level_ex">文件优化级别 (0=不优化; 1=无损优化; 2=轻度有损; 3=最大压缩)</label>
                                <input type="range" id="optimize_level_ex" name="optimize_level" min="0" max="3" value="1">
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2 class="section-title">高级选项</h2>
                            
                            <div class="form-group">
                                <input type="checkbox" id="deskew_ex" name="deskew" value="true">
                                <label for="deskew_ex">自动校正倾斜</label>
                            </div>
                            
                            <div class="form-group">
                                <input type="checkbox" id="rotate_pages_ex" name="rotate_pages" value="true">
                                <label for="rotate_pages_ex">自动旋转页面</label>
                            </div>
                            
                            <div class="form-group">
                                <input type="checkbox" id="remove_background_ex" name="remove_background" value="true">
                                <label for="remove_background_ex">移除背景</label>
                            </div>
                            
                            <div class="form-group">
                                <input type="checkbox" id="force_ocr_ex" name="force_ocr" value="true">
                                <label for="force_ocr_ex">强制OCR</label>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2 class="section-title">选择现有PDF文件</h2>
                            
                            <div class="info-box">
                                从已经存在的文件中选择一个PDF文件进行处理。这些文件已经存在于服务器上，无需重新上传。
                            </div>
                            
                            <div class="form-group">
                                <label for="existing_file">选择文件:</label>
                                <div class="file-list" id="file-list">
                                    """
    
    # 添加PDF文件列表
    for i, pdf_file in enumerate(pdf_files):
        html += f'<div class="file-item" onclick="selectFile(this, \'{pdf_file}\')">{pdf_file}</div>'
    
    if not pdf_files:
        html += '<div>没有找到PDF文件。请先上传文件或将文件放入uploads目录。</div>'
    
    html += """
                                </div>
                                <input type="hidden" id="selected_file" name="selected_file" required>
                            </div>
                            
                            <input type="submit" value="处理选中文件" id="process-btn" disabled>
                        </div>
                    </form>
                </div>
            </div>
            
            <div class="column">
                <div class="sidebar">
                    <h2>关于</h2>
                    <p>这是一个基于 <a href="https://github.com/jbarlow83/OCRmyPDF" target="_blank">OCRmyPDF</a> 的网页工具。</p>
                    
                    <h3>特点:</h3>
                    <ul>
                        <li>对PDF文件进行OCR识别</li>
                        <li>支持多种语言</li>
                        <li>文件优化选项</li>
                        <li>简单易用的界面</li>
                    </ul>
                    
                    <h3>如何使用</h3>
                    <ol>
                        <li>选择OCR选项</li>
                        <li>上传PDF文件或选择已有文件</li>
                        <li>等待处理完成</li>
                        <li>下载处理后的PDF</li>
                    </ol>
                    
                    <hr>
                    <p>基于 jbarlow83/ocrmypdf-alpine</p>
                </div>
            </div>
        </div>
        
        <script>
            function switchTab(tabId) {
                // 隐藏所有标签内容
                const tabContents = document.querySelectorAll('.tab-content');
                tabContents.forEach(content => {
                    content.classList.remove('active');
                });
                
                // 显示选中的标签内容
                document.getElementById(tabId).classList.add('active');
                
                // 更新标签样式
                const tabs = document.querySelectorAll('.tab');
                tabs.forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // 激活当前标签
                if (tabId === 'upload-tab') {
                    tabs[0].classList.add('active');
                } else {
                    tabs[1].classList.add('active');
                }
            }
            
            function selectFile(element, filename) {
                // 移除所有选中状态
                const fileItems = document.querySelectorAll('.file-item');
                fileItems.forEach(item => {
                    item.classList.remove('selected');
                });
                
                // 选中当前文件
                element.classList.add('selected');
                
                // 设置隐藏的input值
                document.getElementById('selected_file').value = filename;
                
                // 启用处理按钮
                document.getElementById('process-btn').disabled = false;
            }
        </script>
    </body>
    </html>
    """
    return html

@app.route('/upload', methods=['POST'])
def upload_file():
    # 记录请求内容长度
    content_length = request.content_length
    logging.info(f"收到上传请求，内容长度: {content_length / (1024 * 1024):.2f}MB")
    
    # 检查是否有文件被上传
    if 'pdf_file' not in request.files:
        return "没有文件被上传", 400

    file = request.files['pdf_file']
    
    # 检查文件名是否为空
    if file.filename == '':
        return "未选择文件", 400
    
    # 收集处理选项
    options = {
        'ocr_enabled': 'ocr_enabled' in request.form,
        'language': request.form.get('language', 'eng+chi_sim'),
        'deskew': 'deskew' in request.form,
        'optimize_level': int(request.form.get('optimize_level', 1)),
        'rotate_pages': 'rotate_pages' in request.form,
        'remove_background': 'remove_background' in request.form,
        'force_ocr': 'force_ocr' in request.form
    }
    
    try:
        # 保存上传的文件
        filename = secure_filename(file.filename)
        temp_input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
        file.save(temp_input_path)
        
        # 处理文件
        output_path = process_pdf_file(temp_input_path, options)
        
        if output_path:
            # 渲染下载页面
            download_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>OCRmyPDF Web 界面 - 下载</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        line-height: 1.6;
                    }}
                    .header {{
                        text-align: center;
                        color: #1E88E5;
                        margin-bottom: 30px;
                    }}
                    .success-msg {{
                        background-color: #D5F5E3;
                        padding: 20px;
                        border-radius: 8px;
                        margin-bottom: 30px;
                        text-align: center;
                    }}
                    .button {{
                        display: inline-block;
                        background-color: #1E88E5;
                        color: white;
                        padding: 12px 24px;
                        text-decoration: none;
                        border-radius: 4px;
                        margin: 10px;
                    }}
                    .button:hover {{
                        background-color: #1976D2;
                    }}
                    .button-container {{
                        text-align: center;
                        margin-top: 30px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>OCRmyPDF Web 界面</h1>
                </div>
                
                <div class="success-msg">
                    <h2>PDF处理成功完成！</h2>
                    <p>现在您可以下载OCR处理后的文件。</p>
                </div>
                
                <div class="button-container">
                    <a href="/download/{os.path.basename(output_path)}" class="button">下载处理后的PDF</a>
                    <a href="/" class="button">处理新文件</a>
                </div>
            </body>
            </html>
            """
            return download_html
        else:
            # 处理失败，删除临时文件
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
            
            return "PDF处理失败，请检查日志获取更多信息。", 500
    
    except Exception as e:
        logging.exception("上传过程中出错")
        return f"处理PDF时出错: {str(e)}", 500

@app.route('/process-existing', methods=['POST'])
def process_existing_file():
    """处理已经存在于服务器上的PDF文件"""
    # 记录处理请求
    logging.info(f"收到处理已有文件的请求")
    
    # 检查是否有文件被选择
    if 'selected_file' not in request.form or not request.form['selected_file']:
        return "没有选择文件", 400
    
    selected_file = request.form['selected_file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], selected_file)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return "所选文件不存在", 404
    
    # 收集处理选项
    options = {
        'ocr_enabled': 'ocr_enabled' in request.form,
        'language': request.form.get('language', 'eng+chi_sim'),
        'deskew': 'deskew' in request.form,
        'optimize_level': int(request.form.get('optimize_level', 1)),
        'rotate_pages': 'rotate_pages' in request.form,
        'remove_background': 'remove_background' in request.form,
        'force_ocr': 'force_ocr' in request.form
    }
    
    try:
        # 处理文件
        output_path = process_pdf_file(file_path, options)
        
        if output_path:
            # 渲染下载页面
            download_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>OCRmyPDF Web 界面 - 下载</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        line-height: 1.6;
                    }}
                    .header {{
                        text-align: center;
                        color: #1E88E5;
                        margin-bottom: 30px;
                    }}
                    .success-msg {{
                        background-color: #D5F5E3;
                        padding: 20px;
                        border-radius: 8px;
                        margin-bottom: 30px;
                        text-align: center;
                    }}
                    .button {{
                        display: inline-block;
                        background-color: #1E88E5;
                        color: white;
                        padding: 12px 24px;
                        text-decoration: none;
                        border-radius: 4px;
                        margin: 10px;
                    }}
                    .button:hover {{
                        background-color: #1976D2;
                    }}
                    .button-container {{
                        text-align: center;
                        margin-top: 30px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>OCRmyPDF Web 界面</h1>
                </div>
                
                <div class="success-msg">
                    <h2>PDF处理成功完成！</h2>
                    <p>现在您可以下载OCR处理后的文件。</p>
                </div>
                
                <div class="button-container">
                    <a href="/download/{os.path.basename(output_path)}" class="button">下载处理后的PDF</a>
                    <a href="/" class="button">处理新文件</a>
                </div>
            </body>
            </html>
            """
            return download_html
        else:
            # 处理失败
            return "PDF处理失败，请检查日志获取更多信息。", 500
    
    except Exception as e:
        logging.exception("处理已有文件时出错")
        return f"处理PDF时出错: {str(e)}", 500

@app.route('/download/<filename>')
def download(filename):
    """提供处理后的PDF文件下载"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return "文件不存在", 404
        
        # 提供文件下载
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename.replace('_ocr.pdf', '_processed.pdf')
        )
    
    except Exception as e:
        logging.exception("下载文件时出错")
        return f"下载文件时出错: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
        

