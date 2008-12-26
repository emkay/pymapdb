#!/usr/bin/env python
import pygraphviz as pgv
import MySQLdb
import re, sys, getpass
from optparse import OptionParser

PROGRAMS = ['dot', 'circo', 'neato']
DEFAULTS = {'user': '', 'password': '', 'host': '127.0.0.1', 'database': '', 'filename': 'temp.png', 'shape': 'box', 'program': 'circo'}
MAX_TABLES_PER_IMAGE = 30

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
	parser.add_option("-s", "--shape", action="store", type="string", dest="shape", 
		help="Set the shape of the nodes.")
	parser.add_option("-m", "--host", action="store", type="string", dest="host",
		help="The host where the database lives.")
	if not sys.argv[1:]:
		parser.print_help()
		exit(2)
	(options, arg) = parser.parse_args()
	return (options, arg)

def main():
	(options, arg) = parse_setup()
	password = getpass.unix_getpass("Enter your password:", sys.stderr) if options.password else DEFAULTS['password']
	username = options.username if options.username else DEFAULTS['username']
	database = options.database if options.database else DEFAULTS['database']
	filename = options.filename if options.filename else DEFAULTS['filename']
	program  = options.program if options.program and options.program in PROGRAMS else DEFAULTS['program']
	shape    = options.shape if options.shape else DEFAULTS['shape']
	host     = options.host if options.host else DEFAULTS['host']
	db = MySQLdb.connect(host=host, user=username, passwd=password, db=database)
	cur1 = db.cursor()
	numrows = cur1.execute('SHOW tables')

	G=pgv.AGraph()
	G.node_attr['shape']=shape

	fkc_matcher = re.compile('CONSTRAINT')

	if numrows > 0:
		table_counter = 0
		filename_counter = 1
		rows = cur1.fetchall()
		for row in rows:
			table_counter += 1
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
								if table_counter == MAX_TABLES_PER_IMAGE and not options.noimage:
									filename_split = filename.split('.')
									new_filename = filename_split[0] + str(filename_counter) + '.' + filename_split[1]
									G.draw(new_filename, prog=program)
									table_counter = 0
									filename_counter += 1
									G = pgv.AGraph()
								G.add_edge('table: ' + table_pk[0] + ' primary key:' + table_pk[1], 'table: ' + row[0] + ' foreign key:' + fk)

	cur1.close()
	db.close()

	if options.graphviz or options.noimage:
		write(G)
	
	if not options.noimage and table_counter < MAX_TABLES_PER_IMAGE:
		filename_counter += 1
		filename_split = filename.split('.')
		new_filename = filename_split[0] + str(filename_counter) + '.' + filename_split[1]
		G.draw(new_filename, prog=program)

if __name__ == "__main__":
	main()
