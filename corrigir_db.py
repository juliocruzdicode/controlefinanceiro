#!/usr/bin/env python3
"""
Script simples para corrigir o banco de dados
"""
import sqlite3
import os

def corrigir():
    db_name = 'controle_financeiro.db'
    
    # Verificar se existe
    if not os.path.exists(db_name):
        print("❌ Banco não encontrado. Criando novo...")
        # Usar Flask para criar
        os.system('python -c "from app import app, db; app.app_context().push(); db.create_all()"')
        return
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    try:
        # Verificar colunas da tabela transacao
        cursor.execute("PRAGMA table_info(transacao)")
        colunas = [row[1] for row in cursor.fetchall()]
        print(f"Colunas atuais: {colunas}")
        
        # Se não tem conta_id, adicionar
        if 'conta_id' not in colunas:
            print("🔧 Adicionando coluna conta_id...")
            
            # Criar tabela conta
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conta (
                    id INTEGER PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    descricao VARCHAR(200),
                    tipo VARCHAR(20) DEFAULT 'corrente',
                    saldo_inicial FLOAT DEFAULT 0.0,
                    cor VARCHAR(7) DEFAULT '#007bff',
                    ativa BOOLEAN DEFAULT 1,
                    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Inserir conta padrão
            cursor.execute("SELECT COUNT(*) FROM conta")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO conta (nome, descricao, tipo) 
                    VALUES ('Minha Conta', 'Conta principal', 'corrente')
                """)
            
            # Adicionar coluna
            cursor.execute("ALTER TABLE transacao ADD COLUMN conta_id INTEGER")
            
            # Atualizar registros existentes
            cursor.execute("UPDATE transacao SET conta_id = 1 WHERE conta_id IS NULL")
            
            # Fazer o mesmo para transacao_recorrente se existir
            cursor.execute("PRAGMA table_info(transacao_recorrente)")
            cols_rec = [row[1] for row in cursor.fetchall()]
            
            if 'conta_id' not in cols_rec:
                cursor.execute("ALTER TABLE transacao_recorrente ADD COLUMN conta_id INTEGER")
                cursor.execute("UPDATE transacao_recorrente SET conta_id = 1 WHERE conta_id IS NULL")
            
            conn.commit()
            print("✅ Banco corrigido!")
        else:
            print("ℹ️  Coluna conta_id já existe")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    corrigir()
    print("\n🚀 Agora execute: python app.py")
