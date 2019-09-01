from models import db
from flask import Flask
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///trivia"


migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command("db", MigrateCommand)

if __name__ == "__main__":
    manager.run()
