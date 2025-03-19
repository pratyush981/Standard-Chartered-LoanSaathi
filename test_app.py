from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World! This is the Loan Saathi test page."

if __name__ == '__main__':
    app.run(debug=True)
