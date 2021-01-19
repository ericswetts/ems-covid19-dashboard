#!/usr/bin/env python
# coding: utf-8

# In[23]:


import psycopg2
from io import StringIO
import os
import pandas as pd
import requests
import os

def connect():
    DATABASE_URL = os.environ['DATABASE_URL']
    
    # Connect to the PostgreSQL database server 
    conn = None
    try:
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit(1) 
    print("Connection successful")
    return conn


def get_from_db(table):

    try:
        conn = connect()
        Cursor = conn.cursor()
        
    except Exception as e:
        print('Unable to connect to db. Please check credentials.')
        return e
        
    try:
        Cursor.execute('Select * from {}'.format(table))
    except Exception as e:
        print('Unable to execute SQL query. Rolling back query...')
        Cursor.execute('rollback')
        return e
        
    results = Cursor.fetchall()
    Cursor.close()
    return results

    
def set_to_db (df, table):
    conn = connect()
    Cursor = conn.cursor()
    try:
        Cursor.execute('DELETE FROM {};'.format(table))
        print('Successfully cleared cached data')
    except Exception as e:
        print(f'Failed to clear cached data : {e} ')
    copy_from_stringio(conn, df, table)
    Cursor.close()
    
    
#helper method to set data to db
def copy_from_stringio(conn, df, table):
    """
    Here we are going save the dataframe in memory 
    and use copy_from() to copy it to the table
    """
    # save dataframe to an in memory buffer
    buffer = StringIO()
    df.to_csv(buffer, index_label = 'id', header=False)
    print(df.columns)
    buffer.seek(0)
    
    cursor = conn.cursor()
    try:
        cursor.copy_from(buffer, table, sep=",")
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    print("Successfully posted to DB")
    cursor.close()
    
#API get method
def get_from_api():
    json_url = 'https://coronavirus-tracker-api.herokuapp.com/v2/locations?timelines=1'
    try:
        response = requests.get(json_url)
        timeline_json = response.json()
        return timeline_json
    
    except Exception as e:
        print('Error making API call: ', e)
        return e