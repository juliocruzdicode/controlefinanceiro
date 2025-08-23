#!/usr/bin/env python3
"""
Script para migrar o banco existente ou criar um novo com o sistema de contas
"""
import os
import sqlite3
from datetime import datetime

def backup_and_migrate():
    """Faz backup do banco atual e aplica migração"""
    db_files = []
    
    # Procurar por arquivos de banco possíveis
    for filename in os.listdir('.'):
        if filename.endswith('.db') or 'controle' in filename.lower():
            db_files.append(filename)
    
    print(f"📁 Arquivos encontrados: {os.listdir('.')}")
    print(f"🗄️  Possíveis bancos de dados: {db_files}")
    
    # Nome do banco principal
    db_name = 'controle_financeiro.db'
    
    # Se existe um banco, migrar. Senão, criar novo
    if os.path.exists(db_name):
        print(f"📊 Banco existente encontrado: {db_name}")
        migrar_banco_existente(db_name)
    else:
        print(f"🆕 Criando novo banco: {db_name}")
        criar_banco_novo(db_name)

def migrar_banco_existente(db_name):
    """Migra um banco existente adicionando as colunas conta_id"""
    try:
        # Fazer backup
        backup_name = f"{db_name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(db_name):
            import shutil
            shutil.copy2(db_name, backup_name)
            print(f"💾 Backup criado: {backup_name}")
        
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # 1. Verificar estrutura atual
        cursor.execute("PRAGMA table_info(transacao)")
        colunas_transacao = [row[1] for row in cursor.fetchall()]
        print(f"📋 Colunas em 'transacao': {colunas_transacao}")
        
        # 2. Criar tabela conta se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conta (
                id INTEGER NOT NULL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                descricao VARCHAR(200),
                tipo VARCHAR(20) NOT NULL,
                saldo_inicial FLOAT DEFAULT 0.0,
                cor VARCHAR(7) DEFAULT '#007bff',
                ativa BOOLEAN DEFAULT 1,
                data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CHECK (ativa IN (0, 1))
            )
        """)
        print("✅ Tabela 'conta' verificada/criada")
        
        # 3. Inserir contas padrão se não existirem
        cursor.execute("SELECT COUNT(*) FROM conta")
        if cursor.fetchone()[0] == 0:
            contas_padrao = [
                ('Minha Conta', 'Conta principal', 'corrente', 0.0, '#007bff', 1),
                ('Conta da Jéssica', 'Conta da Jéssica', 'corrente', 0.0, '#28a745', 1),
                ('Conta do Gabriel', 'Conta do Gabriel', 'corrente', 0.0, '#17a2b8', 1),
                ('Dinheiro', 'Dinheiro físico', 'dinheiro', 0.0, '#ffc107', 1),
            ]
            
            for nome, desc, tipo, saldo, cor, ativa in contas_padrao:
                cursor.execute("""
                    INSERT INTO conta (nome, descricao, tipo, saldo_inicial, cor, ativa)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (nome, desc, tipo, saldo, cor, ativa))
            print("✅ Contas padrão criadas")
        
        # 4. Adicionar conta_id na tabela transacao se não existir
        if 'conta_id' not in colunas_transacao:
            print("🔄 Adicionando coluna conta_id na tabela transacao...")
            cursor.execute("ALTER TABLE transacao ADD COLUMN conta_id INTEGER")
            
            # Pegar ID da primeira conta
            cursor.execute("SELECT id FROM conta LIMIT 1")
            primeira_conta_id = cursor.fetchone()[0]
            
            # Atualizar todas as transações
            cursor.execute("UPDATE transacao SET conta_id = ? WHERE conta_id IS NULL", (primeira_conta_id,))
            count = cursor.rowcount
            print(f"✅ {count} transações associadas à conta padrão")
        else:
            print("ℹ️  Coluna conta_id já existe em transacao")
        
        # 5. Verificar/migrar transacao_recorrente
        cursor.execute("PRAGMA table_info(transacao_recorrente)")
        colunas_recorrente = [row[1] for row in cursor.fetchall()]
        
        if 'conta_id' not in colunas_recorrente:
            print("🔄 Adicionando coluna conta_id na tabela transacao_recorrente...")
            cursor.execute("ALTER TABLE transacao_recorrente ADD COLUMN conta_id INTEGER")
            
            cursor.execute("SELECT id FROM conta LIMIT 1")
            primeira_conta_id = cursor.fetchone()[0]
            
            cursor.execute("UPDATE transacao_recorrente SET conta_id = ? WHERE conta_id IS NULL", (primeira_conta_id,))
            count = cursor.rowcount
            print(f"✅ {count} transações recorrentes associadas à conta padrão")
        else:
            print("ℹ️  Coluna conta_id já existe em transacao_recorrente")
        
        conn.commit()
        
        # Estatísticas finais
        cursor.execute("SELECT COUNT(*) FROM conta")
        total_contas = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM transacao")
        total_transacoes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM transacao_recorrente")
        total_recorrentes = cursor.fetchone()[0]
        
        print(f"\n📊 Estatísticas finais:")
        print(f"   - Contas: {total_contas}")
        print(f"   - Transações: {total_transacoes}")
        print(f"   - Transações recorrentes: {total_recorrentes}")
        
        conn.close()
        print("\n✅ Migração do banco existente concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def criar_banco_novo(db_name):
    """Cria um novo banco com todas as tabelas"""
    print("🆕 Criando novo banco de dados...")
    
    # Usar o app Flask para criar as tabelas
    import sys
    sys.path.append('.')
    
    try:
        from app import app, db
        from models import Conta, TipoConta
        
        with app.app_context():
            db.create_all()
            
            # Criar contas padrão
            contas_padrao = [
                Conta(nome="Minha Conta", descricao="Conta principal", tipo=TipoConta.CORRENTE, cor="#007bff"),
                Conta(nome="Conta da Jéssica", descricao="Conta da Jéssica", tipo=TipoConta.CORRENTE, cor="#28a745"),
                Conta(nome="Conta do Gabriel", descricao="Conta do Gabriel", tipo=TipoConta.CORRENTE, cor="#17a2b8"),
                Conta(nome="Dinheiro", descricao="Dinheiro físico", tipo=TipoConta.DINHEIRO, cor="#ffc107"),
            ]
            
            for conta in contas_padrao:
                db.session.add(conta)
            
            db.session.commit()
            print("✅ Novo banco criado com contas padrão!")
            
    except Exception as e:
        print(f"❌ Erro ao criar novo banco: {e}")

if __name__ == "__main__":
    print("🏦 Migração do Sistema de Contas")
    print("=" * 40)
    
    backup_and_migrate()
    
    print("\n🎉 Processo concluído!")
    print("\nPróximos passos:")
    print("1. Execute: python app.py")
    print("2. Acesse: http://localhost:5002")
    print("3. Teste o sistema de contas!")
