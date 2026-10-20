import os
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

def connect():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)

def json_value(value):
    return Jsonb(value)
