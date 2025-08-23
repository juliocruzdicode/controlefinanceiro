#!/usr/bin/env python3
"""
Migração para adicionar isolamento por usuário
Adiciona campos user_id nas tabelas e associa dados existentes ao admin
"""

import os
import sys
from sqlalchemy import text

# Importar app configurado
from app import app, db, Usuario, Transacao, Categoria, Conta, Tag, TransacaoRecorrente

def executar_migracao():
    """Executa a migração de isolamento por usuário"""
    try:
        with app.app_context():
            print("🔄 Iniciando migração de isolamento por usuário...")
            
            # Verificar se já existe usuário admin
            admin = Usuario.query.filter_by(is_admin=True).first()
            if not admin:
                print("❌ Erro: Nenhum usuário admin encontrado!")
                print("   Execute primeiro o sistema para criar o usuário admin.")
                return False
            
            print(f"👤 Usuário admin encontrado: {admin.username} (ID: {admin.id})")
            
            # Lista de colunas para adicionar
            colunas_migrar = [
                ('transacao', 'user_id'),
                ('categoria', 'user_id'), 
                ('conta', 'user_id'),
                ('tag', 'user_id'),
                ('transacao_recorrente', 'user_id')
            ]
            
            # Verificar quais colunas já existem
            for tabela, coluna in colunas_migrar:
                try:
                    # Tentar consultar a coluna
                    resultado = db.session.execute(text(f"SELECT {coluna} FROM {tabela} LIMIT 1"))
                    print(f"✅ Coluna {tabela}.{coluna} já existe")
                except Exception:
                    # Coluna não existe, adicionar
                    print(f"➕ Adicionando coluna {tabela}.{coluna}...")
                    
                    # Adicionar coluna (permitir NULL temporariamente)
                    db.session.execute(text(f"""
                        ALTER TABLE {tabela} 
                        ADD COLUMN {coluna} INTEGER REFERENCES usuario(id)
                    """))
                    
                    # Atualizar registros existentes para o admin
                    db.session.execute(text(f"""
                        UPDATE {tabela} 
                        SET {coluna} = {admin.id} 
                        WHERE {coluna} IS NULL
                    """))
                    
                    print(f"✅ Coluna {tabela}.{coluna} adicionada e populada")
            
            # Atualizar constraint de unicidade da tag para incluir user_id
            try:
                # Remover constraint unique da tag.nome
                db.session.execute(text("DROP INDEX IF EXISTS ix_tag_nome"))
                
                # Criar novo índice único considerando user_id
                db.session.execute(text("""
                    CREATE UNIQUE INDEX ix_tag_nome_user 
                    ON tag(nome, user_id)
                """))
                print("✅ Constraint de unicidade da tag atualizada")
            except Exception as e:
                print(f"⚠️  Aviso ao atualizar constraint da tag: {e}")
            
            # Commit das mudanças
            db.session.commit()
            
            # Verificar dados migrados
            print(f"\n📊 Resumo da migração:")
            print(f"   • Transações: {Transacao.query.count()}")
            print(f"   • Categorias: {Categoria.query.count()}")  
            print(f"   • Contas: {Conta.query.count()}")
            print(f"   • Tags: {Tag.query.count()}")
            print(f"   • Trans. Recorrentes: {TransacaoRecorrente.query.count()}")
            
            print(f"\n✅ Migração concluída com sucesso!")
            print(f"   Todos os dados existentes foram associados ao usuário admin.")
            print(f"   Agora cada usuário terá seus próprios dados isolados.")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        db.session.rollback()
        return False

if __name__ == '__main__':
    if executar_migracao():
        print("🎉 Sistema pronto! Cada usuário agora terá seus próprios dados.")
    else:
        print("💥 Migração falhou. Verifique os logs acima.")
        sys.exit(1)
