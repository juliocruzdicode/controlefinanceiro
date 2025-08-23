#!/usr/bin/env python3
"""
Script de migração para adicionar sistema de contas
"""
import sqlite3
import os
from datetime import datetime

def migrar_banco():
    """Migra o banco de dados para incluir sistema de contas"""
    db_path = 'controle_financeiro.db'
    
    if not os.path.exists(db_path):
        print("❌ Arquivo do banco de dados não encontrado!")
        return False
    
    # Conectar ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔄 Iniciando migração do banco de dados...")
        
        # 1. Criar tabela de contas
        print("📝 Criando tabela 'conta'...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conta (
                id INTEGER NOT NULL,
                nome VARCHAR(100) NOT NULL,
                descricao VARCHAR(200),
                tipo VARCHAR(20) NOT NULL,
                saldo_inicial FLOAT,
                cor VARCHAR(7),
                ativa BOOLEAN,
                data_criacao DATETIME NOT NULL,
                PRIMARY KEY (id),
                CHECK (ativa IN (0, 1))
            )
        ''')
        
        # 2. Verificar se já existem contas
        cursor.execute("SELECT COUNT(*) FROM conta")
        total_contas = cursor.fetchone()[0]
        
        if total_contas == 0:
            print("💼 Criando contas padrão...")
            contas_padrao = [
                ('Minha Conta', 'Conta principal', 'corrente', 0.0, '#007bff', 1),
                ('Conta da Jéssica', 'Conta da Jéssica', 'corrente', 0.0, '#28a745', 1),
                ('Conta do Gabriel', 'Conta do Gabriel', 'corrente', 0.0, '#17a2b8', 1),
                ('Dinheiro', 'Dinheiro físico', 'dinheiro', 0.0, '#ffc107', 1),
            ]
            
            data_atual = datetime.utcnow().isoformat()
            for nome, desc, tipo, saldo, cor, ativa in contas_padrao:
                cursor.execute('''
                    INSERT INTO conta (nome, descricao, tipo, saldo_inicial, cor, ativa, data_criacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (nome, desc, tipo, saldo, cor, ativa, data_atual))
        else:
            print(f"ℹ️  Já existem {total_contas} contas no banco")
        
        # 3. Verificar se a coluna conta_id já existe na tabela transacao
        cursor.execute("PRAGMA table_info(transacao)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        if 'conta_id' not in colunas:
            print("🔄 Adicionando coluna 'conta_id' na tabela 'transacao'...")
            # Adicionar coluna conta_id
            cursor.execute('ALTER TABLE transacao ADD COLUMN conta_id INTEGER')
            
            # Obter ID da primeira conta para usar como padrão
            cursor.execute("SELECT id FROM conta LIMIT 1")
            primeira_conta = cursor.fetchone()
            
            if primeira_conta:
                conta_padrao_id = primeira_conta[0]
                print(f"📎 Associando transações existentes à conta ID {conta_padrao_id}...")
                
                # Atualizar todas as transações existentes para usar a primeira conta
                cursor.execute("UPDATE transacao SET conta_id = ? WHERE conta_id IS NULL", (conta_padrao_id,))
                transacoes_atualizadas = cursor.rowcount
                print(f"✅ {transacoes_atualizadas} transações atualizadas")
        else:
            print("ℹ️  Coluna 'conta_id' já existe na tabela 'transacao'")
        
        # 4. Verificar e atualizar tabela transacao_recorrente
        cursor.execute("PRAGMA table_info(transacao_recorrente)")
        colunas_rec = [col[1] for col in cursor.fetchall()]
        
        if 'conta_id' not in colunas_rec:
            print("🔄 Adicionando coluna 'conta_id' na tabela 'transacao_recorrente'...")
            cursor.execute('ALTER TABLE transacao_recorrente ADD COLUMN conta_id INTEGER')
            
            # Obter ID da primeira conta
            cursor.execute("SELECT id FROM conta LIMIT 1")
            primeira_conta = cursor.fetchone()
            
            if primeira_conta:
                conta_padrao_id = primeira_conta[0]
                cursor.execute("UPDATE transacao_recorrente SET conta_id = ? WHERE conta_id IS NULL", (conta_padrao_id,))
                recorrentes_atualizadas = cursor.rowcount
                print(f"✅ {recorrentes_atualizadas} transações recorrentes atualizadas")
        else:
            print("ℹ️  Coluna 'conta_id' já existe na tabela 'transacao_recorrente'")
        
        # Confirmar mudanças
        conn.commit()
        print("✅ Migração concluída com sucesso!")
        
        # Mostrar estatísticas finais
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
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🏦 Sistema de Contas - Migração do Banco de Dados")
    print("=" * 50)
    
    sucesso = migrar_banco()
    
    if sucesso:
        print("\n🎉 Migração concluída! O sistema de contas está pronto para uso.")
        print("\nPróximos passos:")
        print("1. Execute a aplicação: python app.py")
        print("2. Acesse o menu 'Contas' para gerenciar suas contas")
        print("3. Ao criar novas transações, selecione a conta desejada")
    else:
        print("\n❌ Migração falhou. Verifique os erros acima.")
