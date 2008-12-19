#!/usr/bin/env python
import pygraphviz as pgv
import MySQLdb
import re, sys, getpass
from optparse import OptionParser

def write(G):
	s=G.string()
	print s

def clean_column(column):
	column = re.sub('.+FOREIGN KEY ','', column)
	column = re.sub('\) ENGINE=InnoDB.+', '', column)
	column = re.sub('\n', '',column)
	return column

def clean_pk(pk):
	pk = re.sub('`', '', pk)
	pk = re.sub('^\s', '', pk)
	pk = re.sub(',$', '', pk)
	return pk

def clean_fk(fk):
	fk = re.sub('\(', '', fk)
	fk = re.sub('\)', '', fk)
	fk = re.sub('`', '', fk)
	return fk

def parse_setup():
	parser = OptionParser()
	parser.add_option("-u", "--user", action="store", type="string", 
		dest="username", help="MySQL user name", metavar="USER")
	parser.add_option("-p", "--password", action="store_true", dest="password",
		help="Require a password.")
	parser.add_option("-d", "--database", action="store", type="string",
		dest="database", help="MySQL database name", metavar="DATABASE")
	parser.add_option("-f", "--file", action="store", type="string",
		dest="filename", help="Name of file to place compiled graphviz in.", metavar="FILENAME")
	parser.add_option("-c", "--program", action="store", dest="program")
	parser.add_option("-g", "--graphviz", action="store_true", dest="graphviz",
		help="Compile down to graphviz and send to STDOUT")
	parser.add_option("-n", "--noimage", action="store_true", dest="noimage",
		help="Do not make an image. Implies that you meant to say -g as well.")
	(options, arg) = parser.parse_args(sys.argv[1:])
	return (options, arg)
							
def main():
	
	(options, arg) = parse_setup()

	if options.password:
		password = getpass.unix_getpass("Enter your password:")
	else:
		password = ''

	if options.username:
		username = options.username
	else:
		username = ''

	if options.database:
		database = options.database
	else:
		database = ''
	
	if options.filename:
		filename = options.filename
	else:
		filename = 'temp.png'

	if options.program and options.program in ['neato', 'circo', 'dot']:
		program = options.program
	else:
		program = 'circo'
			
	db = MySQLdb.connect(host='127.0.0.1', user=username, passwd=password, db=database)
	cur1 = db.cursor()
	numrows = cur1.execute('SHOW tables')

	G=pgv.AGraph()
	G.node_attr['shape']='box'

	fkc_matcher = re.compile('CONSTRAINT')

	if numrows > 0:
		rows = cur1.fetchall()
		for row in rows:
			create_table_num_rows = cur1.execute('SHOW CREATE TABLE ' + row[0])
			if create_table_num_rows > 0:
				create_table_rows = cur1.fetchall()
				for create_table_row in create_table_rows:
					if fkc_matcher.search(create_table_row[1]) != None:
						columns = create_table_row[1].split('\n  ')
						for column in columns:
							if fkc_matcher.search(column) != None:
								column = clean_column(column)
								keys = column.split('REFERENCES')
								pk = clean_pk(keys[1])
								table_pk = pk.split(' ')
								fk = clean_fk(keys[0])
								G.add_edge('table: ' + table_pk[0] + ' primary key:' + table_pk[1], 'table: ' + row[0] + ' foreign key:' + fk)

	cur1.close()
	db.close()

	if options.graphviz or options.noimage:
		write(G)
	
	if not options.noimage:
		G.draw(filename, prog=program)

if __name__ == "__main__":
	main()
