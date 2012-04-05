import config
import MySQLdb
db = MySQLdb.connect( host = config.mysql_host,
                      user = config.mysql_user,
                      passwd = config.mysql_pass)
cursor = db.cursor()
cursor.execute ('CREATE DATABASE IF NOT EXISTS ' + config.mysql_dbname + ';')
cursor.close ()
db.close ()

conn = MySQLdb.connect(\
                host = config.mysql_host,\
                user = config.mysql_user,\
                passwd = config.mysql_pass,\
                db = config.mysql_dbname\
)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS reserves(\
                    id BIGINT UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT,\
                    sw1 SMALLINT UNSIGNED,\
                    sw1_port SMALLINT UNSIGNED,\
                    sw2 SMALLINT UNSIGNED,\
                    sw2_port SMALLINT UNSIGNED,\
                    deleted SMALLINT UNSIGNED\
                );')
conn.commit()
db.close ()
conn.close ()
