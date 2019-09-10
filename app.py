from flask import Flask, render_template
import os
import controllers

app = Flask(__name__, template_folder='views')

app.register_blueprint(controllers.main_blueprint)
app.register_blueprint(controllers.extension_blueprint)
app.register_blueprint(controllers.team_blueprint)
app.register_blueprint(controllers.graphs)
app.register_blueprint(controllers.read_rosters)
app.register_blueprint(controllers.rankings)

app.secret_key = os.urandom(24)

if __name__ == '__main__':
    app.run(host='localhost', port=3000, debug=True)