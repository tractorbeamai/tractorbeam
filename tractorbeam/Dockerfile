FROM python:3.12-slim

# set the working directory
WORKDIR /code

# install uv
RUN apt-get update && apt-get install -y curl
ENV VIRTUAL_ENV=/usr/local
RUN curl -fsSL https://astral.sh/uv/install.sh | sh

# copy requirements.txt
COPY ./requirements.txt /code/requirements.txt

# install deps
RUN /root/.cargo/bin/uv pip install --no-cache --upgrade -r /code/requirements.txt

# copy migrations
COPY ./alembic.ini  /code/alembic.ini
COPY ./migrations   /code/migrations

# copy application code
COPY ./app /code/app

# run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]

