#!/usr/bin/env python3
"""
Script de migração específico para adicionar coluna recorrencia_id na tabela transacao
"""

import sys
import os
import sqlite3
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def migrar_banco():
    """Migra o banco de dados existente adicionando a coluna recorrencia_id"""
    try:
        print("🔧 Iniciando migração do banco de dados...")
        
        # Conectar ao banco SQLite
        conn = sqlite3.connect('controle_financeiro.db')
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(transacao)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'recorrencia_id' not in colunas:
            print("📝 Adicionando coluna recorrencia_id à tabela transacao...")
            cursor.execute("ALTER TABLE transacao ADD COLUMN recorrencia_id INTEGER")
            conn.commit()
            print("✅ Coluna recorrencia_id adicionada com sucesso!")
        else:
            print("ℹ️  Coluna recorrencia_id já existe")
        
        # Verificar se a tabela transacao_recorrente existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transacao_recorrente'")
        if not cursor.fetchone():
            print("📝 Criando tabela transacao_recorrente...")
            cursor.execute('''
                CREATE TABLE transacao_recorrente (
                    id INTEGER NOT NULL PRIMARY KEY,
                    descricao VARCHAR(200) NOT NULL,
                    valor FLOAT NOT NULL,
                    tipo VARCHAR(7) NOT NULL,
                    tipo_recorrencia VARCHAR(10) NOT NULL DEFAULT 'unica',
                    status VARCHAR(10) NOT NULL DEFAULT 'ativa',
                    data_inicio DATETIME NOT NULL,
                    data_fim DATETIME,
                    data_criacao DATETIME NOT NULL,
                    total_parcelas INTEGER,
                    parcelas_geradas INTEGER DEFAULT 0,
                    categoria_id INTEGER NOT NULL,
                    FOREIGN KEY(categoria_id) REFERENCES categoria (id)
                )
            ''')
            conn.commit()
            print("✅ Tabela transacao_recorrente criada com sucesso!")
        else:
            print("ℹ️  Tabela transacao_recorrente já existe")
        
        conn.close()
        print("🎉 Migração do banco concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        return False

if __name__ == '__main__':
    sucesso = migrar_banco()
    if sucesso:
        print("✅ Banco migrado com sucesso! Agora pode executar a migração completa.")
    else:
        print("❌ Migração do banco falhou!")
        sys.exit(1)
