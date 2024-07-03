from app import create_app, db
from app.models import User, Chat, Document
from werkzeug.security import generate_password_hash
import os
from app.utils import ensure_directories, check_permissions, train_model

app = create_app()

def reset_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset completed.")

def create_test_user():
    with app.app_context():
        if User.query.count() == 0:
            test_user = User(username='test', password=generate_password_hash('test'))
            db.session.add(test_user)
            db.session.commit()
            print("Test user created.")

if __name__ == '__main__':
    ensure_directories()
    check_permissions()

    # Check if the database file exists
    db_file = 'instance/app.db'  # Adjust this path if your database is stored elsewhere
    if os.path.exists(db_file):
        reset_database()
    else:
        with app.app_context():
            db.create_all()

    create_test_user()

    # Train the model at startup if necessary
    train_result = train_model()
    print(train_result)

    app.run(debug=True)