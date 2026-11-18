"""WSGI entry point for the Zenara application."""

from zenara import create_app

app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
