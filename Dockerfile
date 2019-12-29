FROM python
COPY . /code
WORKDIR /code
RUN pip install mechanicalsoup jinja2 lxml