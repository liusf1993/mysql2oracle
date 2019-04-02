import pymysql
import re

conn = pymysql.connect(host="127.0.0.1", user="root", password="123456", db="test")
cursor = conn.cursor()

re_key_1 = re.compile(r'KEY `(\w+)` \((.*)\)')
re_key_2 = re.compile(r'UNIQUE KEY `(\w+)` \((.*)\)')

def convert_index_ddl(table_name):
    cursor.execute("show create table %s" % table_name)
    rows = cursor.fetchall()
    ddl = rows[0][1]
    i_ddl = ""
    for line in ddl.split("\n"):
        # 一般索引
        key_match = re_key_1.match(line.strip())
        ukey_match = re_key_2.match(line.strip())
        if key_match:
            i_ddl += "create index " + key_match.group(1) + " on " + table_name + "(" \
                     + key_match.group(2).replace("`", "") + ");\n"
            #print(i_ddl)
        elif ukey_match:
            i_ddl += "alter table " + table_name + " add CONSTRAINT " + ukey_match.group(1) \
                     + " unique (" + ukey_match.group(2).replace("`", "") + ");\n"
    f = open("%s.sql" % table_name, "w")
    f.write(i_ddl)
    f.close()


def convert_table_ddl(table_name):
    cursor.execute("show full columns from %s" % table_name)
    rows = cursor.fetchall()
    f = open("dest.sql", "w")

    f.write("create table %s (\n" % table_name)
    i = 0
    for row in rows:
        col_name = row[0]
        col_def = row[1]
        col_nullable = row[3]
        col_default = row[5]
        col_pk = row[4]
        col_comm = row[8]
        if col_def.startswith("int", 0, 3):
            d_def = "number(10)"
        elif col_def.startswith("bigint", 0, 6):
            d_def = "number(20)"
        elif col_def.startswith("varchar", 0, 7):
            d_length = int(col_def[7:].replace("(", "").replace(")", "")) * 3
            d_def = "varchar2(" + str(d_length) + ")"
        elif col_def == "blob":
            d_def = "blob"
        elif col_def.startswith("decimal"):
            d_def = "number" + col_def[7:]
        elif col_def == "date" or col_def == "datetime" or col_def == "timestamp":
            d_def = "date"
        elif col_def.startswith("tinyint"):
            d_def = "number(4)"
        elif col_def == "text":
            d_def = "clob"
        else:
            print("暂不支持该类型转换，请等待工具升级")
            print(col_def)
        line = col_name + " " + d_def
        if col_default is not None:
            if col_default == "CURRENT_TIMESTAMP":
                line += " default sysdate"
            else:
                line += " default " + col_default
        if col_nullable == "NO":
            line += " not null"
        if col_pk == "PRI":
            line += " primary key"
        i += 1
        if i < len(rows):
            line += ","
        f.write(line + "\n")
    f.write(");")
    f.close()

convert_table_ddl("test")
convert_index_ddl("test")
