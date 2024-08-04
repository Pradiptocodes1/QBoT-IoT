import os
import random
import pandas as pd
from flask import Flask, render_template_string, request, jsonify
from werkzeug.utils import secure_filename
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

app = Flask(__name__)
app.static_folder = 'static'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
mistral_client = MistralClient(api_key="JAXv9n5zjE2FXlSzoGqeMolLp7uqQLqD")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IoT Labs QBoT</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        body, html { 
            font-family: 'Roboto', sans-serif;
            margin: 0;
            padding: 0;
            height: 100%;
            background-color: #2c2c2c;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            max-width: 800px;
            width: 100%;
            padding: 20px;
            box-sizing: border-box;
        }
        .logo-holder {
            width: 100px;
            height: 100px;
            margin: 20px auto;
            background-color: #1e90ff;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 24px;
            font-weight: bold;
            color: white;
            text-shadow: 0 0 10px rgba(30, 144, 255, 0.8);
        }
        h1 { 
            text-align: center;
            color: white;
            font-size: 36px;
            margin-bottom: 30px;
            text-shadow: 0 0 10px rgba(30, 144, 255, 0.8);
            animation: glow 2s ease-in-out infinite alternate;
        }
        @keyframes glow {
            from {
                text-shadow: 0 0 5px #1e90ff, 0 0 10px #1e90ff, 0 0 15px #1e90ff;
            }
            to {
                text-shadow: 0 0 10px #1e90ff, 0 0 20px #1e90ff, 0 0 30px #1e90ff;
            }
        }
        form { 
            margin-bottom: 20px; 
            background-color: #3c3c3c;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(30, 144, 255, 0.3);
        }
        button { 
            margin-top: 10px; 
            background-color: #1e90ff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        button:hover {
            background-color: #187bcd;
            box-shadow: 0 0 15px rgba(30, 144, 255, 0.5);
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        #result { 
            margin-top: 20px; 
            white-space: pre-wrap; 
            background-color: #3c3c3c;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(30, 144, 255, 0.3);
        }
        .question {
            color: white;
            background-color: #1e90ff;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .answer {
            color: #2ecc71;
            display: none;
            padding: 10px;
            background-color: #2c2c2c;
            border-radius: 5px;
        }
        #loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        .loader {
            border: 5px solid #3c3c3c;
            border-top: 5px solid #1e90ff;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            display: inline-block;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .background-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 0.1;
        }
        .background-animation span {
            position: absolute;
            width: 5px;
            height: 5px;
            background-color: #1e90ff;
            border-radius: 50%;
            animation: move 20s linear infinite;
        }
        @keyframes move {
            0% {
                transform: translateY(0) translateX(0);
            }
            100% {
                transform: translateY(-100vh) translateX(100vw);
            }
        }
    </style>
</head>
<body>
    <div class="background-animation">
        <span style="left: 10%; animation-delay: 0s;"></span>
        <span style="left: 30%; animation-delay: 2s;"></span>
        <span style="left: 50%; animation-delay: 4s;"></span>
        <span style="left: 70%; animation-delay: 6s;"></span>
        <span style="left: 90%; animation-delay: 8s;"></span>
    </div>
    <div class="container">
        <div class="logo-holder"><img src="{{ url_for('static', filename='iot.jpg') }}" alt="IoT Labs Logo" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;"></div>
        <h1>QboT</h1>
        <form id="upload-form" enctype="multipart/form-data">
            <div>
                <label for="python_file">Python Excel File:</label>
                <input type="file" id="python_file" name="python_file" accept=".xlsx, .xls" required>
            </div>
            <div>
                <label for="ml_file">ML Excel File:</label>
                <input type="file" id="ml_file" name="ml_file" accept=".xlsx, .xls" required>
            </div>
            <button type="submit">Upload Files</button>
        </form>
        <button id="python-btn" disabled>Generate Python Question</button>
        <button id="ml-btn" disabled>Generate ML Question</button>
        <div id="loading">
            <div class="loader"></div>
            <p>Generating question...</p>
        </div>
        <div id="result"></div>
    </div>

    <script>
        $(document).ready(function() {
            $('#upload-form').submit(function(e) {
                e.preventDefault();
                var formData = new FormData(this);
                $.ajax({
                    url: '/',
                    type: 'POST',
                    data: formData,
                    processData: false,
                    contentType: false,
                    success: function(response) {
                        alert('Files uploaded successfully');
                        $('#python-btn, #ml-btn').prop('disabled', false);
                    },
                    error: function(xhr) {
                        alert('Error: ' + xhr.responseJSON.error);
                    }
                });
            });

            function generateQuestion(category) {
                $('#loading').show();
                $('#result').empty();
                $.ajax({
                    url: '/generate_question',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({ category: category }),
                    success: function(response) {
                        $('#loading').hide();
                        var resultHtml = '<div class="question"><strong>Generated Question:</strong>\\n' + response.generated_question + '</div>' +
                                         '<button id="show-answer">Show Answer</button>' +
                                         '<div class="answer"><strong>Answer:</strong>\\n' + response.generated_answer + '</div>';
                        $('#result').html(resultHtml);
                        
                        $('#show-answer').click(function() {
                            $('.answer').toggle();
                        });
                    },
                    error: function(xhr) {
                        $('#loading').hide();
                        alert('Error: ' + xhr.responseJSON.error);
                    }
                });
            }

            $('#python-btn').click(function() {
                generateQuestion('python');
            });

            $('#ml-btn').click(function() {
                generateQuestion('ml');
            });
        });
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'python_file' not in request.files or 'ml_file' not in request.files:
            return jsonify({'error': 'Both files are required'}), 400

        python_file = request.files['python_file']
        ml_file = request.files['ml_file']
        if python_file.filename == '' or ml_file.filename == '':
            return jsonify({'error': 'Both files must be selected'}), 400

        if not allowed_file(python_file.filename) or not allowed_file(ml_file.filename):
            return jsonify({'error': 'Invalid file type. Please upload Excel files.'}), 400

        # Save files
        python_filename = secure_filename(python_file.filename)
        ml_filename = secure_filename(ml_file.filename)

        python_file.save(os.path.join(app.config['UPLOAD_FOLDER'], python_filename))
        ml_file.save(os.path.join(app.config['UPLOAD_FOLDER'], ml_filename))

        return jsonify({'message': 'Files uploaded successfully'}), 200

    return render_template_string(HTML_TEMPLATE)

@app.route('/generate_question', methods=['POST'])
def generate_question():
    category = request.json['category']
    
    if category not in ['python', 'ml']:
        return jsonify({'error': 'Invalid category'}), 400

    filename = f"{category}_file.xlsx"  
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(file_path):
        return jsonify({'error': f'{category.upper()} file not found'}), 404
    df = pd.read_excel(file_path)
    
    if 'Question' not in df.columns:
        return jsonify({'error': 'Invalid Excel format. "Question" column not found'}), 400
    random_question = random.choice(df['Question'].tolist())
    messages = [
        ChatMessage(role="system", content="You are a helpful assistant that generates new programming questions based on given questions."),
        ChatMessage(role="user", content=f"Based on this {category} question: '{random_question}', generate a new, similar but different question. Then, provide a short and concise solution in maximum 3 lines. Format your response as 'Question: [your generated question]' followed by 'Answer: [your solution]'.")
    ]

    chat_response = mistral_client.chat(
        model="mistral-large-latest",
        messages=messages
    )

    generated_content = chat_response.choices[0].message.content
    generated_question, generated_answer = generated_content.split('Answer:', 1)
    generated_question = generated_question.replace('Question:', '').strip()
    generated_answer = generated_answer.strip()

    return jsonify({
        'generated_question': generated_question,
        'generated_answer': generated_answer
    })

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
