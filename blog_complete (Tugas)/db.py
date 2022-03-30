import pymysql


def db_connection():
    """ function to open connection """
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        database='db_blog_complete',
        user='root',
        password=''
    )
    return conn
