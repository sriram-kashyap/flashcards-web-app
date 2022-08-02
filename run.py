from main import create_app

app, api, celery = create_app()

if __name__ == "__main__":
    app.run(debug=True)    
    celery.autodiscover_tasks()
