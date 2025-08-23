"""
Script para migração do banco de dados SQLite para PostgreSQL
"""
import os
import sys
import psycopg2
import sqlite3
from psycopg2.extras import execute_values
from datetime import datetime

def conectar_sqlite(sqlite_path):
    """
    Conecta ao banco SQLite
    
    Args:
        sqlite_path: Caminho para o arquivo SQLite
    
    Returns:
        objeto de conexão SQLite
    """
    try:
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row  # Para acessar colunas pelo nome
        print(f"✅ Conectado ao SQLite: {sqlite_path}")
        return conn
    except sqlite3.Error as e:
        print(f"❌ Erro ao conectar ao SQLite: {str(e)}")
        sys.exit(1)

def conectar_postgres(host, database, user, password, port=5432):
    """
    Conecta ao banco PostgreSQL
    
    Args:
        host: Host do PostgreSQL
        database: Nome do banco de dados
        user: Usuário
        password: Senha
        port: Porta (padrão: 5432)
    
    Returns:
        objeto de conexão PostgreSQL
    """
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        print(f"✅ Conectado ao PostgreSQL: {database}@{host}:{port}")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Erro ao conectar ao PostgreSQL: {str(e)}")
        sys.exit(1)

def obter_tabelas(sqlite_conn):
    """
    Obtém lista de tabelas do SQLite
    
    Args:
        sqlite_conn: Conexão SQLite
    
    Returns:
        lista de nomes de tabelas
    """
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tabelas = [row['name'] for row in cursor.fetchall()]
    return tabelas

def obter_esquema_tabela(sqlite_conn, tabela):
    """
    Obtém esquema de uma tabela
    
    Args:
        sqlite_conn: Conexão SQLite
        tabela: Nome da tabela
    
    Returns:
        lista de tuplas (nome_coluna, tipo_coluna)
    """
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [(row['name'], row['type']) for row in cursor.fetchall()]
    return colunas

def mapear_tipo_sqlite_para_postgres(tipo_sqlite):
    """
    Converte tipo do SQLite para o PostgreSQL
    
    Args:
        tipo_sqlite: Tipo no SQLite
    
    Returns:
        tipo equivalente no PostgreSQL
    """
    tipo_sqlite = tipo_sqlite.upper()
    mapeamento = {
        'INTEGER': 'INTEGER',
        'REAL': 'NUMERIC',
        'TEXT': 'TEXT',
        'BLOB': 'BYTEA',
        'BOOLEAN': 'BOOLEAN',
        'DATETIME': 'TIMESTAMP',
        'DATE': 'DATE',
        'TIME': 'TIME'
    }
    
    for sqlite_tipo, pg_tipo in mapeamento.items():
        if sqlite_tipo in tipo_sqlite:
            return pg_tipo
    
    return 'TEXT'  # Tipo padrão

def migrar_tabela(sqlite_conn, pg_conn, tabela):
    """
    Migra uma tabela do SQLite para o PostgreSQL
    
    Args:
        sqlite_conn: Conexão SQLite
        pg_conn: Conexão PostgreSQL
        tabela: Nome da tabela
    
    Returns:
        bool: True se a migração foi bem-sucedida
    """
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # Obter esquema da tabela
        esquema = obter_esquema_tabela(sqlite_conn, tabela)
        
        # Criar lista de colunas para SQL
        colunas = [coluna[0] for coluna in esquema]
        
        # Obter dados da tabela SQLite
        sqlite_cursor.execute(f"SELECT * FROM {tabela}")
        dados = sqlite_cursor.fetchall()
        
        if not dados:
            print(f"ℹ️ Tabela {tabela} está vazia. Pulando.")
            return True
        
        # Preparar dados para inserção
        valores = []
        for linha in dados:
            # Converter linha para dicionário e depois lista ordenada
            linha_dict = dict(linha)
            valores.append([linha_dict.get(coluna) for coluna in colunas])
        
        # Construir query de inserção
        campos = ', '.join(colunas)
        
        # Inserir dados no PostgreSQL
        execute_values(
            pg_cursor, 
            f"INSERT INTO {tabela} ({campos}) VALUES %s ON CONFLICT DO NOTHING", 
            valores
        )
        
        pg_conn.commit()
        print(f"✅ Tabela {tabela}: {len(dados)} registros migrados")
        return True
        
    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Erro ao migrar tabela {tabela}: {str(e)}")
        return False

def migrar_para_postgres():
    """
    Migra o banco completo do SQLite para o PostgreSQL
    
    Returns:
        bool: True se a migração foi bem-sucedida
    """
    from app import app
    
    print("🚀 Iniciando migração de SQLite para PostgreSQL...")
    
    # Verificar se as variáveis de ambiente necessárias estão definidas
    pg_vars = ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
    for var in pg_vars:
        if var not in os.environ:
            print(f"❌ Variável de ambiente {var} não definida!")
            return False
    
    # Obter caminho do banco SQLite
    if 'sqlite' not in app.config['SQLALCHEMY_DATABASE_URI']:
        print("❌ Configuração atual não é SQLite!")
        return False
    
    sqlite_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    if 'instance/' not in sqlite_path and not sqlite_path.startswith('/'):
        sqlite_path = os.path.join('instance', sqlite_path)
    
    # Conectar aos bancos
    sqlite_conn = conectar_sqlite(sqlite_path)
    pg_conn = conectar_postgres(
        host=os.environ['POSTGRES_HOST'],
        database=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        port=int(os.environ.get('POSTGRES_PORT', 5432))
    )
    
    # Obter lista de tabelas
    tabelas = obter_tabelas(sqlite_conn)
    print(f"📋 Tabelas encontradas: {', '.join(tabelas)}")
    
    # Criar tabelas no PostgreSQL usando SQLAlchemy
    with app.app_context():
        from app import db
        print("📝 Criando esquema no PostgreSQL...")
        db.create_all()
    
    # Migrar cada tabela
    sucessos = 0
    falhas = 0
    
    for tabela in tabelas:
        print(f"\n🔄 Migrando tabela: {tabela}")
        if migrar_tabela(sqlite_conn, pg_conn, tabela):
            sucessos += 1
        else:
            falhas += 1
    
    # Fechar conexões
    sqlite_conn.close()
    pg_conn.close()
    
    print(f"\n📊 Resumo da migração: {sucessos} tabela(s) migrada(s), {falhas} falha(s)")
    
    if falhas == 0:
        print("\n✅ Migração para PostgreSQL concluída com sucesso!")
        print("\nPara usar o PostgreSQL, configure as seguintes variáveis de ambiente:")
        print("  export SQLALCHEMY_DATABASE_URI=\"postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}\"")
    else:
        print("\n⚠️ Migração concluída com erros. Verifique os logs acima.")
    
    return falhas == 0

if __name__ == "__main__":
    migrar_para_postgres()
