import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, dbname='guardnet', user='postgres', password='1410')
print('Connexion OK!')
