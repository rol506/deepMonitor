
if __name__ == "__main__":
    from flsite import app
    from waitress import serve
    serve(app, host="0.0.0.0", port=app.config["PORT"])
