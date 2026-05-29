"""Compatibility wrapper for older entrypoint names."""

from app import app


if __name__ == "__main__":
    app.run(debug=True)