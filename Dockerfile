FROM python
COPY . /code
WORKDIR /code
RUN pip install -r requirements.txt
