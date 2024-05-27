FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

EXPOSE 8000

# Install system-wide dependencies
RUN apt-get update && \
  apt-get install --no-install-recommends -y git curl gcc python3-dev && \
  apt-get clean autoclean && \
  apt-get autoremove --yes && \
  rm -rf /var/lib/apt/lists/*

# Create user for app
ENV APP_USER=appuser
RUN useradd --create-home $APP_USER
WORKDIR /home/$APP_USER
USER $APP_USER

# Use venv directly via PATH
ENV VENV_PATH=/home/$APP_USER/.venv/bin
ENV USER_PATH=/home/$APP_USER/.local/bin
ENV PATH="$VENV_PATH:$USER_PATH:$PATH"

RUN pip install -r requirements.txt
#  poetry config virtualenvs.in-project true
#
#COPY poetry.lock pyproject.toml ./

COPY vpn vpn

CMD python3 vpn/main.py
