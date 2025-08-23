#!/usr/bin/env python3
"""
Script para migrar o banco de dados adicionando campos de verificação de email
"""

from app import app, db
from models import Usuario
from sqlalchemy import text

def migrate_email_verification():
    """Adiciona campos de verificação de email"""
    with app.app_context():
        try:
            # Verificar se as colunas já existem
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(usuario)")).fetchall()
                existing_columns = [row[1] for row in result]
                
                migrations_needed = []
                
                if 'email_verified' not in existing_columns:
                    migrations_needed.append("ALTER TABLE usuario ADD COLUMN email_verified BOOLEAN DEFAULT 0")
                
                if 'email_verification_token' not in existing_columns:
                    migrations_needed.append("ALTER TABLE usuario ADD COLUMN email_verification_token VARCHAR(100)")
                
                if 'email_verification_sent_at' not in existing_columns:
                    migrations_needed.append("ALTER TABLE usuario ADD COLUMN email_verification_sent_at DATETIME")
                
                if migrations_needed:
                    print("🔄 Aplicando migrações de verificação de email...")
                    
                    for migration in migrations_needed:
                        print(f"   Executando: {migration}")
                        conn.execute(text(migration))
                        conn.commit()
                    
                    # Marcar usuários existentes como verificados (retrocompatibilidade)
                    print("   Marcando usuários existentes como verificados...")
                    conn.execute(text("UPDATE usuario SET email_verified = 1 WHERE email_verified IS NULL"))
                    conn.commit()
                    
                    print("✅ Migração concluída com sucesso!")
                    
                    # Estatísticas
                    total_users = conn.execute(text("SELECT COUNT(*) FROM usuario")).scalar()
                    verified_users = conn.execute(text("SELECT COUNT(*) FROM usuario WHERE email_verified = 1")).scalar()
                    
                    print(f"📊 Estatísticas:")
                    print(f"   Total de usuários: {total_users}")
                    print(f"   Usuários com email verificado: {verified_users}")
                    
                else:
                    print("✅ Banco de dados já está atualizado!")
                
        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            raise

if __name__ == '__main__':
    print("🚀 Iniciando migração de verificação de email...")
    migrate_email_verification()
    print("🎉 Migração finalizada!")
