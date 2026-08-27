from fastapi import FastAPI
from pydantic import BaseModel
from database import init_database, get_connection

app = FastAPI(title="Watch2Earn API")


# Initialize database
init_database()


class UserData(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None


@app.get("/")
def home():
    return {
        "status": "online",
        "app": "Watch2Earn",
        "version": "1.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/users")
def create_or_get_user(user: UserData):

    connection = get_connection()

    existing_user = connection.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (user.telegram_id,)
    ).fetchone()

    if existing_user:
        connection.close()

        return {
            "status": "existing",
            "user": dict(existing_user)
        }

    connection.execute(
        """
        INSERT INTO users
        (telegram_id, username, first_name)
        VALUES (?, ?, ?)
        """,
        (
            user.telegram_id,
            user.username,
            user.first_name
        )
    )

    connection.commit()

    new_user = connection.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (user.telegram_id,)
    ).fetchone()

    connection.close()

    return {
        "status": "created",
        "user": dict(new_user)
    }
