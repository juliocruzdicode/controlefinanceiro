#!/usr/bin/env python3
"""
Script para migrar o banco de dados e adicionar a coluna conta_id à tabela transacao.
Este script resolve o erro: "no such column: transacao.conta_id"
"""

import sqlite3
from datetime import datetime
import os

def backup_database(db_path):
    """Cria um backup do banco de dados antes da migração"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    # Copiar arquivo original para backup
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup criado: {backup_path}")
    return backup_path

def check_conta_id_exists(cursor):
    """Verifica se a coluna conta_id já existe na tabela transacao"""
    cursor.execute("PRAGMA table_info(transacao)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    return 'conta_id' in column_names

def create_default_conta_if_needed(cursor):
    """Cria uma conta padrão se não existir nenhuma"""
    cursor.execute("SELECT COUNT(*) FROM conta")
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.execute("""
            INSERT INTO conta (nome, descricao, tipo, saldo_inicial, cor, ativa, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Conta Padrão', 'Conta criada automaticamente durante migração', 
              'corrente', 0.0, '#007bff', 1, datetime.utcnow()))
        print("✅ Conta padrão criada")
        return cursor.lastrowid
    else:
        # Usar a primeira conta disponível
        cursor.execute("SELECT id FROM conta LIMIT 1")
        conta_id = cursor.fetchone()[0]
        print(f"✅ Usando conta existente ID: {conta_id}")
        return conta_id

def migrate_database(db_path):
    """Executa a migração do banco de dados"""
    
    if not os.path.exists(db_path):
        print(f"❌ Erro: Banco de dados não encontrado em {db_path}")
        return False
    
    # Criar backup
    backup_path = backup_database(db_path)
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a migração já foi executada
        if check_conta_id_exists(cursor):
            print("✅ Coluna conta_id já existe na tabela transacao. Migração não necessária.")
            conn.close()
            return True
        
        print("🔄 Iniciando migração...")
        
        # Garantir que existe pelo menos uma conta
        conta_padrao_id = create_default_conta_if_needed(cursor)
        
        # 1. Criar nova tabela com a estrutura correta
        cursor.execute("""
            CREATE TABLE transacao_new (
                id INTEGER NOT NULL, 
                descricao VARCHAR(200) NOT NULL, 
                valor FLOAT NOT NULL, 
                tipo VARCHAR(7) NOT NULL, 
                data_transacao DATETIME NOT NULL, 
                data_criacao DATETIME NOT NULL, 
                categoria_id INTEGER NOT NULL, 
                conta_id INTEGER NOT NULL,
                recorrencia_id INTEGER, 
                PRIMARY KEY (id), 
                FOREIGN KEY(categoria_id) REFERENCES categoria (id),
                FOREIGN KEY(conta_id) REFERENCES conta (id),
                FOREIGN KEY(recorrencia_id) REFERENCES transacao_recorrente (id)
            )
        """)
        print("✅ Nova tabela transacao_new criada")
        
        # 2. Copiar dados da tabela antiga para a nova, adicionando conta_id
        cursor.execute(f"""
            INSERT INTO transacao_new (id, descricao, valor, tipo, data_transacao, data_criacao, categoria_id, conta_id, recorrencia_id)
            SELECT id, descricao, valor, tipo, data_transacao, data_criacao, categoria_id, {conta_padrao_id}, recorrencia_id
            FROM transacao
        """)
        
        rows_migrated = cursor.rowcount
        print(f"✅ {rows_migrated} transações migradas")
        
        # 3. Remover tabela antiga
        cursor.execute("DROP TABLE transacao")
        print("✅ Tabela antiga removida")
        
        # 4. Renomear nova tabela
        cursor.execute("ALTER TABLE transacao_new RENAME TO transacao")
        print("✅ Nova tabela renomeada para transacao")
        
        # 5. Atualizar transacao_recorrente para garantir que tem conta_id (se necessário)
        cursor.execute("PRAGMA table_info(transacao_recorrente)")
        rec_columns = cursor.fetchall()
        rec_column_names = [col[1] for col in rec_columns]
        
        if 'conta_id' not in rec_column_names:
            print("🔄 Adicionando conta_id à tabela transacao_recorrente...")
            cursor.execute(f"ALTER TABLE transacao_recorrente ADD COLUMN conta_id INTEGER REFERENCES conta(id)")
            cursor.execute(f"UPDATE transacao_recorrente SET conta_id = {conta_padrao_id} WHERE conta_id IS NULL")
            print("✅ Tabela transacao_recorrente atualizada")
        
        # Commit das alterações
        conn.commit()
        conn.close()
        
        print("✅ Migração concluída com sucesso!")
        print(f"📁 Backup salvo em: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        
        # Restaurar backup em caso de erro
        try:
            import shutil
            shutil.copy2(backup_path, db_path)
            print(f"🔄 Banco restaurado do backup: {backup_path}")
        except Exception as restore_error:
            print(f"❌ Erro ao restaurar backup: {restore_error}")
        
        return False

def verify_migration(db_path):
    """Verifica se a migração foi bem-sucedida"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar estrutura da tabela
        cursor.execute("PRAGMA table_info(transacao)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("\n📋 Estrutura atual da tabela transacao:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        if 'conta_id' in column_names:
            print("✅ Coluna conta_id encontrada!")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM transacao")
            count = cursor.fetchone()[0]
            print(f"📊 Total de transações: {count}")
            
            # Verificar se todas as transações têm conta_id
            cursor.execute("SELECT COUNT(*) FROM transacao WHERE conta_id IS NULL")
            null_count = cursor.fetchone()[0]
            
            if null_count == 0:
                print("✅ Todas as transações possuem conta_id válido")
            else:
                print(f"⚠️  {null_count} transações sem conta_id")
        else:
            print("❌ Coluna conta_id não encontrada!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

if __name__ == "__main__":
    # Caminho para o banco de dados
    db_path = "instance/controle_financeiro.db"
    
    print("🚀 Iniciando migração do banco de dados")
    print("=" * 50)
    
    if migrate_database(db_path):
        print("\n🔍 Verificando migração...")
        verify_migration(db_path)
        print("\n🎉 Migração concluída! O sistema agora deve funcionar corretamente.")
    else:
        print("\n❌ Migração falhou. Verifique os logs de erro acima.")
