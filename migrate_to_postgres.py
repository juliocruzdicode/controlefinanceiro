"""
Script para migrar dados do SQLite para PostgreSQL
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
from datetime import datetime
import hashlib

def conectar_sqlite():
    """Conecta ao banco SQLite"""
    sqlite_path = 'instance/controle_financeiro.db'
    if not os.path.exists(sqlite_path):
        sqlite_path = 'controle_financeiro.db'
    
    if not os.path.exists(sqlite_path):
        print("❌ Arquivo SQLite não encontrado!")
        return None
    
    return sqlite3.connect(sqlite_path)

def conectar_postgres():
    """Conecta ao banco PostgreSQL"""
    try:
        return psycopg2.connect(
            host=os.environ.get('POSTGRES_HOST', 'localhost'),
            database=os.environ.get('POSTGRES_DB', 'controle_financeiro'),
            user=os.environ.get('POSTGRES_USER', 'controle_financeiro'),
            password=os.environ.get('POSTGRES_PASSWORD', 'senha_segura_aqui'),
            port=os.environ.get('POSTGRES_PORT', '5432')
        )
    except psycopg2.OperationalError as e:
        print(f"❌ Erro ao conectar ao PostgreSQL: {e}")
        return None

def criar_tabelas_postgres(pg_conn):
    """Cria as tabelas no PostgreSQL baseado nos modelos"""
    print("📋 Criando tabelas no PostgreSQL...")
    
    with pg_conn.cursor() as cursor:
        # Usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuario (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                senha_hash VARCHAR(128) NOT NULL,
                ativo BOOLEAN NOT NULL DEFAULT true,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultimo_login TIMESTAMP,
                tentativas_login INTEGER DEFAULT 0,
                bloqueado_ate TIMESTAMP,
                mfa_ativo BOOLEAN DEFAULT false,
                mfa_secret VARCHAR(32),
                admin BOOLEAN DEFAULT false
            )
        """)
        
        # Categorias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categoria (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                cor VARCHAR(7) DEFAULT '#3498db',
                categoria_pai_id INTEGER REFERENCES categoria(id),
                usuario_id INTEGER NOT NULL REFERENCES usuario(id),
                UNIQUE(nome, usuario_id)
            )
        """)
        
        # Contas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conta (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                tipo VARCHAR(20) NOT NULL,
                saldo_inicial DECIMAL(10,2) DEFAULT 0.00,
                ativa BOOLEAN NOT NULL DEFAULT true,
                usuario_id INTEGER NOT NULL REFERENCES usuario(id),
                UNIQUE(nome, usuario_id)
            )
        """)
        
        # Tags
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tag (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(50) NOT NULL,
                cor VARCHAR(7) DEFAULT '#6c757d',
                usuario_id INTEGER NOT NULL REFERENCES usuario(id),
                UNIQUE(nome, usuario_id)
            )
        """)
        
        # Transações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacao (
                id SERIAL PRIMARY KEY,
                descricao VARCHAR(200) NOT NULL,
                valor DECIMAL(10,2) NOT NULL,
                data DATE NOT NULL,
                tipo VARCHAR(10) NOT NULL,
                categoria_id INTEGER NOT NULL REFERENCES categoria(id),
                conta_id INTEGER NOT NULL REFERENCES conta(id),
                observacoes TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_id INTEGER NOT NULL REFERENCES usuario(id)
            )
        """)
        
        # Tabela de associação transação-tag
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacao_tag (
                transacao_id INTEGER NOT NULL REFERENCES transacao(id) ON DELETE CASCADE,
                tag_id INTEGER NOT NULL REFERENCES tag(id) ON DELETE CASCADE,
                PRIMARY KEY (transacao_id, tag_id)
            )
        """)
        
        # Transações recorrentes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacao_recorrente (
                id SERIAL PRIMARY KEY,
                descricao VARCHAR(200) NOT NULL,
                valor DECIMAL(10,2) NOT NULL,
                tipo VARCHAR(10) NOT NULL,
                categoria_id INTEGER NOT NULL REFERENCES categoria(id),
                conta_id INTEGER NOT NULL REFERENCES conta(id),
                frequencia VARCHAR(20) NOT NULL,
                dia_vencimento INTEGER,
                data_inicio DATE NOT NULL,
                data_fim DATE,
                ativa BOOLEAN NOT NULL DEFAULT true,
                observacoes TEXT,
                usuario_id INTEGER NOT NULL REFERENCES usuario(id)
            )
        """)
        
        # Índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacao_usuario_data ON transacao(usuario_id, data)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacao_categoria ON transacao(categoria_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacao_conta ON transacao(conta_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_categoria_usuario ON categoria(usuario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conta_usuario ON conta(usuario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tag_usuario ON tag(usuario_id)")
        
    pg_conn.commit()
    print("✅ Tabelas criadas com sucesso!")

def migrar_dados(sqlite_conn, pg_conn):
    """Migra dados do SQLite para PostgreSQL"""
    print("📊 Iniciando migração de dados...")
    
    with sqlite_conn.cursor() as sqlite_cur, pg_conn.cursor() as pg_cur:
        # 1. Migrar usuários
        print("👥 Migrando usuários...")
        sqlite_cur.execute("SELECT * FROM usuario")
        usuarios = sqlite_cur.fetchall()
        
        for usuario in usuarios:
            pg_cur.execute("""
                INSERT INTO usuario (id, nome, email, senha_hash, ativo, data_criacao, 
                                   ultimo_login, tentativas_login, bloqueado_ate, 
                                   mfa_ativo, mfa_secret, admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            """, usuario)
        
        # Atualizar sequence
        pg_cur.execute("SELECT setval('usuario_id_seq', (SELECT COALESCE(MAX(id), 1) FROM usuario))")
        
        # 2. Migrar categorias
        print("📁 Migrando categorias...")
        sqlite_cur.execute("SELECT * FROM categoria")
        categorias = sqlite_cur.fetchall()
        
        for categoria in categorias:
            pg_cur.execute("""
                INSERT INTO categoria (id, nome, cor, categoria_pai_id, usuario_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, categoria)
        
        pg_cur.execute("SELECT setval('categoria_id_seq', (SELECT COALESCE(MAX(id), 1) FROM categoria))")
        
        # 3. Migrar contas
        print("🏦 Migrando contas...")
        sqlite_cur.execute("SELECT * FROM conta")
        contas = sqlite_cur.fetchall()
        
        for conta in contas:
            pg_cur.execute("""
                INSERT INTO conta (id, nome, tipo, saldo_inicial, ativa, usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, conta)
        
        pg_cur.execute("SELECT setval('conta_id_seq', (SELECT COALESCE(MAX(id), 1) FROM conta))")
        
        # 4. Migrar tags
        print("🏷️ Migrando tags...")
        try:
            sqlite_cur.execute("SELECT * FROM tag")
            tags = sqlite_cur.fetchall()
            
            for tag in tags:
                pg_cur.execute("""
                    INSERT INTO tag (id, nome, cor, usuario_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, tag)
            
            pg_cur.execute("SELECT setval('tag_id_seq', (SELECT COALESCE(MAX(id), 1) FROM tag))")
        except sqlite3.OperationalError:
            print("⚠️ Tabela 'tag' não existe no SQLite, pulando...")
        
        # 5. Migrar transações
        print("💰 Migrando transações...")
        sqlite_cur.execute("SELECT * FROM transacao")
        transacoes = sqlite_cur.fetchall()
        
        for transacao in transacoes:
            pg_cur.execute("""
                INSERT INTO transacao (id, descricao, valor, data, tipo, categoria_id, 
                                     conta_id, observacoes, data_criacao, usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, transacao)
        
        pg_cur.execute("SELECT setval('transacao_id_seq', (SELECT COALESCE(MAX(id), 1) FROM transacao))")
        
        # 6. Migrar associações transação-tag
        print("🔗 Migrando associações transação-tag...")
        try:
            sqlite_cur.execute("SELECT * FROM transacao_tag")
            transacao_tags = sqlite_cur.fetchall()
            
            for assoc in transacao_tags:
                pg_cur.execute("""
                    INSERT INTO transacao_tag (transacao_id, tag_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, assoc)
        except sqlite3.OperationalError:
            print("⚠️ Tabela 'transacao_tag' não existe no SQLite, pulando...")
        
        # 7. Migrar transações recorrentes
        print("🔄 Migrando transações recorrentes...")
        try:
            sqlite_cur.execute("SELECT * FROM transacao_recorrente")
            recorrentes = sqlite_cur.fetchall()
            
            for recorrente in recorrentes:
                pg_cur.execute("""
                    INSERT INTO transacao_recorrente (id, descricao, valor, tipo, categoria_id,
                                                    conta_id, frequencia, dia_vencimento, 
                                                    data_inicio, data_fim, ativa, observacoes, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, recorrente)
            
            pg_cur.execute("SELECT setval('transacao_recorrente_id_seq', (SELECT COALESCE(MAX(id), 1) FROM transacao_recorrente))")
        except sqlite3.OperationalError:
            print("⚠️ Tabela 'transacao_recorrente' não existe no SQLite, pulando...")
    
    pg_conn.commit()
    print("✅ Migração de dados concluída!")

def verificar_migracao(sqlite_conn, pg_conn):
    """Verifica se a migração foi bem-sucedida"""
    print("🔍 Verificando migração...")
    
    tabelas = ['usuario', 'categoria', 'conta', 'transacao']
    
    with sqlite_conn.cursor() as sqlite_cur, pg_conn.cursor() as pg_cur:
        for tabela in tabelas:
            try:
                sqlite_cur.execute(f"SELECT COUNT(*) FROM {tabela}")
                sqlite_count = sqlite_cur.fetchone()[0]
                
                pg_cur.execute(f"SELECT COUNT(*) FROM {tabela}")
                pg_count = pg_cur.fetchone()[0]
                
                if sqlite_count == pg_count:
                    print(f"✅ {tabela}: {sqlite_count} registros migrados com sucesso")
                else:
                    print(f"⚠️ {tabela}: SQLite({sqlite_count}) != PostgreSQL({pg_count})")
            except Exception as e:
                print(f"❌ Erro ao verificar {tabela}: {e}")

def main():
    """Função principal"""
    print("🚀 Iniciando migração SQLite → PostgreSQL")
    print("=" * 50)
    
    # Conectar aos bancos
    print("🔌 Conectando aos bancos de dados...")
    sqlite_conn = conectar_sqlite()
    if not sqlite_conn:
        sys.exit(1)
    
    pg_conn = conectar_postgres()
    if not pg_conn:
        sqlite_conn.close()
        sys.exit(1)
    
    try:
        # Criar tabelas no PostgreSQL
        criar_tabelas_postgres(pg_conn)
        
        # Migrar dados
        migrar_dados(sqlite_conn, pg_conn)
        
        # Verificar migração
        verificar_migracao(sqlite_conn, pg_conn)
        
        print("=" * 50)
        print("🎉 Migração concluída com sucesso!")
        print("\n📝 Próximos passos:")
        print("1. Teste a aplicação com PostgreSQL")
        print("2. Faça backup do banco SQLite")
        print("3. Configure as variáveis de ambiente para produção")
        print("4. Execute: docker-compose up -d")
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        pg_conn.rollback()
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    main()
