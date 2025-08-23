#!/usr/bin/env python3
"""
Script de migração usando SQLAlchemy para adicionar sistema de contas
"""
from app import app, db
from models import Conta, TipoConta, Transacao, TransacaoRecorrente
from sqlalchemy import text

def migrar_database():
    """Migra o banco de dados para incluir sistema de contas"""
    with app.app_context():
        print("🔄 Iniciando migração do banco de dados...")
        
        try:
            # 1. Criar todas as tabelas (incluindo a tabela conta)
            print("📝 Criando tabelas...")
            db.create_all()
            
            # 2. Verificar se já existem contas
            total_contas = Conta.query.count()
            if total_contas == 0:
                print("💼 Criando contas padrão...")
                contas_padrao = [
                    Conta(nome="Minha Conta", descricao="Conta principal", tipo=TipoConta.CORRENTE, cor="#007bff"),
                    Conta(nome="Conta da Jéssica", descricao="Conta da Jéssica", tipo=TipoConta.CORRENTE, cor="#28a745"),
                    Conta(nome="Conta do Gabriel", descricao="Conta do Gabriel", tipo=TipoConta.CORRENTE, cor="#17a2b8"),
                    Conta(nome="Dinheiro", descricao="Dinheiro físico", tipo=TipoConta.DINHEIRO, cor="#ffc107"),
                ]
                
                for conta in contas_padrao:
                    db.session.add(conta)
                
                db.session.commit()
                print("✅ Contas padrão criadas!")
            else:
                print(f"ℹ️  Já existem {total_contas} contas no banco")
            
            # 3. Verificar se as colunas conta_id existem
            try:
                # Tentar executar uma query simples para verificar se a coluna existe
                db.session.execute(text("SELECT conta_id FROM transacao LIMIT 1"))
                print("ℹ️  Coluna 'conta_id' já existe na tabela 'transacao'")
            except Exception as e:
                if "no such column" in str(e).lower():
                    print("🔄 Adicionando coluna 'conta_id' na tabela 'transacao'...")
                    
                    # Adicionar coluna conta_id na tabela transacao
                    db.session.execute(text('ALTER TABLE transacao ADD COLUMN conta_id INTEGER'))
                    
                    # Obter ID da primeira conta para usar como padrão
                    primeira_conta = Conta.query.first()
                    if primeira_conta:
                        print(f"📎 Associando transações existentes à conta: {primeira_conta.nome}")
                        db.session.execute(
                            text("UPDATE transacao SET conta_id = :conta_id WHERE conta_id IS NULL"),
                            {'conta_id': primeira_conta.id}
                        )
                        
                        # Contar transações atualizadas
                        result = db.session.execute(text("SELECT COUNT(*) FROM transacao WHERE conta_id = :conta_id"), 
                                                  {'conta_id': primeira_conta.id})
                        count = result.scalar()
                        print(f"✅ {count} transações associadas à conta padrão")
                    
                    db.session.commit()
                else:
                    raise e
            
            # 4. Verificar tabela transacao_recorrente
            try:
                db.session.execute(text("SELECT conta_id FROM transacao_recorrente LIMIT 1"))
                print("ℹ️  Coluna 'conta_id' já existe na tabela 'transacao_recorrente'")
            except Exception as e:
                if "no such column" in str(e).lower():
                    print("🔄 Adicionando coluna 'conta_id' na tabela 'transacao_recorrente'...")
                    
                    db.session.execute(text('ALTER TABLE transacao_recorrente ADD COLUMN conta_id INTEGER'))
                    
                    # Obter ID da primeira conta
                    primeira_conta = Conta.query.first()
                    if primeira_conta:
                        db.session.execute(
                            text("UPDATE transacao_recorrente SET conta_id = :conta_id WHERE conta_id IS NULL"),
                            {'conta_id': primeira_conta.id}
                        )
                        
                        result = db.session.execute(text("SELECT COUNT(*) FROM transacao_recorrente WHERE conta_id = :conta_id"), 
                                                  {'conta_id': primeira_conta.id})
                        count = result.scalar()
                        print(f"✅ {count} transações recorrentes associadas à conta padrão")
                    
                    db.session.commit()
                else:
                    raise e
            
            # Estatísticas finais
            total_contas = Conta.query.count()
            total_transacoes = Transacao.query.count()
            total_recorrentes = TransacaoRecorrente.query.count()
            
            print(f"\n📊 Estatísticas finais:")
            print(f"   - Contas: {total_contas}")
            print(f"   - Transações: {total_transacoes}")
            print(f"   - Transações recorrentes: {total_recorrentes}")
            
            print("\n✅ Migração concluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante migração: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🏦 Sistema de Contas - Migração do Banco de Dados")
    print("=" * 50)
    
    sucesso = migrar_database()
    
    if sucesso:
        print("\n🎉 Migração concluída! O sistema de contas está pronto para uso.")
        print("\nPróximos passos:")
        print("1. Execute a aplicação: python app.py")
        print("2. Acesse o menu 'Contas' para gerenciar suas contas")
        print("3. Ao criar novas transações, selecione a conta desejada")
    else:
        print("\n❌ Migração falhou. Verifique os erros acima.")
