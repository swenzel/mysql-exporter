import click
import pymysql
from pymysql.cursors import DictCursor
import configparser
import os
import sys
import pathlib
import csv
import json
import yaml
from typing import Dict, NamedTuple, Iterable, Callable, Optional, Any
import datetime as dt
import itertools as it
from functools import wraps

CONNECTION=None
def get_connection() -> pymysql.Connection:
    global CONNECTION
    if CONNECTION is None:
        config = get_config()
        CONNECTION = pymysql.connect(
            host=config.get('host', 'localhost'),
            port=config.get('port', 3306),
            user=config.get('user', 'root'),
            password=config.get('password', '')
        )
    return CONNECTION


def ensure_cursor(cursor: Optional[DictCursor]=None) -> DictCursor:
    if cursor is None:
        return get_connection().cursor(pymysql.cursors.DictCursor)
    return cursor


def get_config() -> Dict:
    conf_file = pathlib.Path('mysqlexport.yml')
    if conf_file.exists():
        return yaml.safe_load(conf_file.read_text())

    conf_file = pathlib.Path('mysqlexport.yaml')
    if conf_file.exists():
        return yaml.safe_load(conf_file.read_text())

    conf_file = pathlib.Path('mysqlexport.json')
    if conf_file.exists():
        return yaml.safe_load(conf_file.read_text())

    return {}


@click.group(name='mysqlexport')
def main():
    pass


@main.group(name='list')
def list_it():
    pass


@list_it.command(name='databases')
@click.option("-o", "--output-format", type=str, default='plain')
def list_databases(output_format='plain'):
    curs = select_databases()
    output(curs, output_format)


def select_databases(curs: Optional[DictCursor]=None) -> pymysql.cursors.DictCursor:
    curs: pymysql.cursors.DictCursor = get_connection().cursor(pymysql.cursors.DictCursor)
    curs.execute("show databases;")
    return curs


@list_it.command(name="tables")
@click.option("-d", "--database", type=str, default='__all__')
@click.option("-o", "--output-format", type=str, default='plain')
def list_tables(database='__all__', output_format='plain'):
    if database == '__all__':
        dbs = select_databases()
    else:
        dbs = [{'Database': db} for db in database.split(',')]

    curs = ensure_cursor()
    output(it.chain.from_iterable(
        select_tables(database['Database'], curs) for database in dbs
    ), output_format)


def select_tables(database, curs: Optional[DictCursor]=None) -> pymysql.cursors.DictCursor:
    curs = ensure_cursor(curs)
    curs.execute(f"show tables from `{database}`;")
    tbl_key = f"Tables_in_{database}"
    return (
        {"Database": database, "Table": row[tbl_key]}
        for row in curs
    )


@main.group()
def dump():
    pass

@dump.command(name="table")
@click.argument('database')
@click.argument('table')
@click.option("-o", "--output-format", type=str, default='plain')
@click.option("-f", "--output-file", type=str, default="-")
def dump_table(database, table, output_format: str="plain", output_file: str="-"):
    curs = select_table_data(database, table)
    output(curs, output_format, output_file)


def select_table_data(database, table, curs: Optional[DictCursor]=None) -> DictCursor:
    curs = ensure_cursor(curs)
    curs.execute(f"select * from `{database}`.`{table}`;")
    return curs


@dump.command(name="database")
@click.argument('database')
@click.option("-o", "--output-format", type=str, default='plain')
def dump_database(database, output_format: str="plain"):
    tables = select_tables(database)
    extension = get_extension(output_format)
    curs = ensure_cursor()
    pathlib.Path(database).mkdir(exist_ok=True)
    for table in tables:
        database, table = table["Database"], table["Table"]
        output_file = f'{database}/{table}{extension}'
        output(select_table_data(database, table, curs), output_format, output_file)


def get_extension(output_format: str):
    if output_format == 'plain':
        return '.txt'
    elif output_format == 'csv':
        return '.csv'
    elif output_format == 'rjson':
        return '.rjson'


def output(result: Iterable[Dict], output_format: str="plain", output_file:str='-'):
    with click.open_file(output_file, 'w') as output_stream:
        if output_format == 'plain':
            output_plain(result, output_stream)
        elif output_format == 'csv':
            output_csv(result, output_stream)
        elif output_format == 'rjson':
            output_rjson(result, output_stream)
        else:
            raise ValueError(f"Unknown output format {output_format}")


def output_plain(result: Iterable[Dict], output_stream):
    first = True
    keys = None
    for row in result:
        if first:
            keys = sorted(row.keys())
            output_stream.write(' '.join(keys)+'\n')
            output_stream.write(' '.join('-'*len(key) for key in keys)+'\n')
            first = False
        values = [str(row[key]) for key in keys]
        output_stream.write(' '.join(value if ' ' not in value else repr(value)
            for value in values
        )+'\n')


def output_csv(result: Iterable[Dict], output_stream):
    writer = None
    first = True
    for row in result:
        if first:
            writer = csv.DictWriter(output_stream, list(row.keys()))
            writer.writeheader()
            first = False
        writer.writerow(row)


def output_rjson(result: Iterable[Dict], output_stream):
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (dt.time, dt.datetime, dt.date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))
    
    for row in result:
        output_stream.write(json.dumps(row, default=json_serial)+'\n')


if __name__ == "__main__":
    main()
