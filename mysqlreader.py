import pymysql
import re
import argparse


def convert_index_ddl(table_name):
    re_key_1 = re.compile(r'KEY `(\w+)` \((.*)\)')
    re_key_2 = re.compile(r'UNIQUE KEY `(\w+)` \((.*)\)')
    re_key_3 = re.compile(r'PRIMARY KEY +\((.*)\)')
    cursor.execute("show create table %s" % table_name)
    rows = cursor.fetchall()
    ddl = rows[0][1]
    i_ddl = ""
    for line in ddl.split("\n"):
        # 一般索引
        key_match = re_key_1.match(line.strip())
        # 唯一索引
        ukey_match = re_key_2.match(line.strip())
        # 主键索引
        pkey_match = re_key_3.match(line.strip())
        if key_match:
            i_ddl += "create index " + key_match.group(1) + " on " + table_name + "(" \
                     + key_match.group(2).replace("`", "") + ");\n"
        elif ukey_match:
            i_ddl += "alter table " + table_name + " add CONSTRAINT Un_" + table_name[2:25] \
                     + " unique (" + ukey_match.group(2).replace("`", "") + ");\n"
        elif pkey_match:
            i_ddl += "alter table " + table_name + " add CONSTRAINT pk_" + table_name[2:25] \
                     + " primary key (" + pkey_match.group(1).replace("`", "") + ");\n"
    f = open("out/%s.sql" % table_name, "a")
    f.write(i_ddl)
    f.close()


def convert_table_ddl(table_name):
    cursor.execute("show full columns from %s" % table_name)
    rows = cursor.fetchall()
    f = open("out/%s.sql" % table_name, "w")

    f.write("create table %s (\n" % table_name)
    i = 0
    d_def = ""
    for row in rows:
        col_name = row[0]
        col_def = row[1]
        col_nullable = row[3]
        col_default = row[5]
        if col_def.startswith("int", 0, 3):
            d_def = "number(10)"
        elif col_def.startswith("bigint", 0, 6):
            d_def = "number(20)"
        elif col_def.startswith("varchar", 0, 7):
            if int(col_def[7:].replace("(", "").replace(")", "")) * 3 <= 1024:
                d_length = int(col_def[7:].replace("(", "").replace(")", "")) * 3
            else:
                d_length = int(col_def[7:].replace("(", "").replace(")", ""))
            d_def = "varchar2(" + str(d_length) + ")"
        elif col_def == "blob" or col_def == "mediumblob":
            d_def = "blob"
        elif col_def.startswith("decimal"):
            d_def = "number" + col_def[7:]
        elif col_def.startswith("date") or col_def.startswith("datetime") or col_def.startswith("timestamp"):
            d_def = "date"
        elif col_def.startswith("tinyint"):
            d_def = "number(4)"
        elif col_def in ("longtext", "text"):
            d_def = "clob"
        else:
            print("暂不支持该类型转换，请等待工具升级")
            print(col_def)
        line = col_name + " " + d_def
        if col_default is not None:
            if col_default == "CURRENT_TIMESTAMP":
                line += " default sysdate"
            # Oracle会将空字符串自动变成null，因此不允许出现default ''，这里特殊处理
            elif col_default == "":
                line += ""
            else:
                line += " default '" + col_default + "'"
        if col_nullable == "NO":
            line += " not null"
        i += 1
        if i < len(rows):
            line += ","
        f.write(line + "\n")
    f.write(");\n")
    f.close()


def get_tables():
    cursor.execute("show tables")
    tables = cursor.fetchall()

    for table in tables:
        convert_table_ddl(table[0])
        convert_index_ddl(table[0])


def _argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--host", help="键入host地址")
    parser.add_argument("-u", "--user", help="type user name")
    parser.add_argument("-p", "--passwd", help="type password")
    parser.add_argument("-d", "--db", help="type db name")
    args = parser.parse_args()
    return args


def main():
    args = _argparse()
    host = args.host
    user = args.user
    password = args.passwd
    database = args.db
    conn = pymysql.connect(host=host, user=user, password=password, db=database)
    global cursor
    cursor = conn.cursor()
    get_tables()


if __name__ == '__main__':
    main()
