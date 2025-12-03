docker run \
    -d \
    -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=todo_reminder \
    -p 5432:5432 \
    -v todo_reminder_local_db:/var/lib/postgresql \
    postgres
