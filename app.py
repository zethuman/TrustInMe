from flask import Flask
import bot
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

app.register_blueprint(bot)

app.run()
