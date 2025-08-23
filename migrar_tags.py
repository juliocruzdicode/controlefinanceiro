#!/usr/bin/env python3
"""
Script para migrar o banco de dados e adicionar o sistema de tags.
Este script cria:
- Tabela 'tag' para armazenar as tags
- Tabela 'transacao_tags' para relacionamento muitos-para-muitos
"""

import sqlite3
from datetime import datetime
import os

def backup_database(db_path):
    """Cria um backup do banco de dados antes da migração"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_tags_{timestamp}"
    
    # Copiar arquivo original para backup
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup criado: {backup_path}")
    return backup_path

def check_tables_exist(cursor):
    """Verifica se as tabelas de tags já existem"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('tag', 'transacao_tags')")
    existing_tables = [row[0] for row in cursor.fetchall()]
    return 'tag' in existing_tables, 'transacao_tags' in existing_tables

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
        
        # Verificar se as tabelas já existem
        tag_exists, transacao_tags_exists = check_tables_exist(cursor)
        
        if tag_exists and transacao_tags_exists:
            print("✅ Tabelas de tags já existem. Migração não necessária.")
            conn.close()
            return True
        
        print("🔄 Iniciando migração do sistema de tags...")
        
        # 1. Criar tabela de tags
        if not tag_exists:
            cursor.execute("""
                CREATE TABLE tag (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome VARCHAR(50) NOT NULL UNIQUE,
                    descricao VARCHAR(200),
                    cor VARCHAR(7) DEFAULT '#6c757d',
                    ativa BOOLEAN DEFAULT 1,
                    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Tabela 'tag' criada")
        
        # 2. Criar tabela de relacionamento transacao_tags
        if not transacao_tags_exists:
            cursor.execute("""
                CREATE TABLE transacao_tags (
                    transacao_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (transacao_id, tag_id),
                    FOREIGN KEY (transacao_id) REFERENCES transacao(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
                )
            """)
            print("✅ Tabela 'transacao_tags' criada")
        
        # 3. Criar algumas tags padrão
        tags_padrao = [
            ('Pessoal', 'Gastos pessoais', '#007bff'),
            ('Trabalho', 'Gastos relacionados ao trabalho', '#28a745'),
            ('Casa', 'Gastos domésticos', '#ffc107'),
            ('Saúde', 'Gastos com saúde', '#dc3545'),
            ('Educação', 'Gastos com educação', '#6f42c1'),
            ('Lazer', 'Gastos com entretenimento', '#fd7e14'),
            ('Transporte', 'Gastos com transporte', '#20c997'),
            ('Viagem', 'Gastos com viagens', '#e83e8c')
        ]
        
        for nome, descricao, cor in tags_padrao:
            cursor.execute("SELECT id FROM tag WHERE nome = ?", (nome,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO tag (nome, descricao, cor, ativa, data_criacao)
                    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                """, (nome, descricao, cor))
        
        print("✅ Tags padrão criadas")
        
        # Commit das alterações
        conn.commit()
        conn.close()
        
        print("✅ Migração do sistema de tags concluída com sucesso!")
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
        
        # Verificar estrutura das tabelas
        print("\n📋 Estrutura da tabela 'tag':")
        cursor.execute("PRAGMA table_info(tag)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        print("\n📋 Estrutura da tabela 'transacao_tags':")
        cursor.execute("PRAGMA table_info(transacao_tags)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM tag")
        count = cursor.fetchone()[0]
        print(f"\n📊 Total de tags: {count}")
        
        # Listar tags criadas
        cursor.execute("SELECT nome, cor FROM tag ORDER BY nome")
        tags = cursor.fetchall()
        print("\n🏷️  Tags disponíveis:")
        for nome, cor in tags:
            print(f"  - {nome} ({cor})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

if __name__ == "__main__":
    # Caminho para o banco de dados
    db_path = "instance/controle_financeiro.db"
    
    print("🏷️  Iniciando migração do sistema de tags")
    print("=" * 50)
    
    if migrate_database(db_path):
        print("\n🔍 Verificando migração...")
        verify_migration(db_path)
        print("\n🎉 Sistema de tags implementado com sucesso!")
        print("Agora você pode usar tags personalizadas para classificar suas transações.")
    else:
        print("\n❌ Migração falhou. Verifique os logs de erro acima.")
