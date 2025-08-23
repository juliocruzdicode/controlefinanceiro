"""
Script para recriar a tabela de usuários com os novos campos.
Use este script se o migrar_perfil_usuario.py não funcionar no SQLite.
"""
from app import app, db
from models import Usuario
import sys
import sqlite3
import os

def recriar_tabela_usuario():
    """Recria a tabela de usuário preservando os dados existentes"""
    with app.app_context():
        # Verificar se estamos usando SQLite
        if 'sqlite' not in app.config['SQLALCHEMY_DATABASE_URI']:
            print("Este script é apenas para SQLite. Use o migrar_perfil_usuario.py para PostgreSQL.")
            return
        
        # Ajustar o caminho para usar o diretório instance
        if 'instance/' not in app.config['SQLALCHEMY_DATABASE_URI']:
            db_path = os.path.join('instance', app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        else:
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            
        if not os.path.exists(db_path):
            print(f"Banco de dados não encontrado: {db_path}")
            return
        
        print(f"Recriando tabela usuario no banco: {db_path}")
        
        # 1. Backup dos dados existentes
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar se a tabela existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuario'")
            if not cursor.fetchone():
                print("Tabela usuario não existe. Nada a fazer.")
                return
            
            # Buscar os dados existentes
            cursor.execute("SELECT id, username, email, password_hash, mfa_secret, mfa_enabled, "
                         "backup_codes, email_verified, email_verification_token, "
                         "email_verification_sent_at, is_admin, is_active, created_at, "
                         "last_login, failed_login_attempts, locked_until FROM usuario")
            usuarios = cursor.fetchall()
            
            print(f"Dados de {len(usuarios)} usuários salvos para migração")
            
            # 2. Renomear tabela antiga
            cursor.execute("ALTER TABLE usuario RENAME TO usuario_old")
            conn.commit()
            
            # 3. Fechar conexão para permitir SQLAlchemy criar a nova tabela
            conn.close()
            
            # 4. Criar nova tabela com o esquema atual
            db.create_all()
            print("Nova tabela usuario criada com os campos adicionais")
            
            # 5. Migrar dados
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for user in usuarios:
                # Os novos campos (telefone, data_nascimento, sexo, cidade) serão NULL
                query = """
                INSERT INTO usuario (id, username, email, password_hash, mfa_secret, mfa_enabled,
                                  backup_codes, email_verified, email_verification_token,
                                  email_verification_sent_at, is_admin, is_active, created_at,
                                  last_login, failed_login_attempts, locked_until,
                                  telefone, data_nascimento, sexo, cidade)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL)
                """
                cursor.execute(query, user)
            
            conn.commit()
            print(f"{len(usuarios)} usuários migrados com sucesso")
            
            # 6. Atualizar sequência de autoincremento (se necessário)
            if usuarios:
                max_id = max(user[0] for user in usuarios)
                # Verificar se a tabela sqlite_sequence existe
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
                if cursor.fetchone():
                    cursor.execute(f"UPDATE sqlite_sequence SET seq = {max_id} WHERE name = 'usuario'")
                    conn.commit()
                    print(f"Sequência de autoincremento atualizada para {max_id}")
                else:
                    print("Tabela sqlite_sequence não encontrada, pulando atualização de sequência.")
            
            # 7. Deletar tabela antiga (opcional)
            cursor.execute("DROP TABLE usuario_old")
            conn.commit()
            print("Tabela antiga removida")
            
            conn.close()
            print("Migração concluída com sucesso!")
            
        except Exception as e:
            print(f"Erro durante a migração: {e}")
            print("Tentando reverter alterações...")
            try:
                # Tentar reverter para a tabela antiga se algo deu errado
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Verificar se a tabela antiga ainda existe
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuario_old'")
                if cursor.fetchone():
                    # Verificar se nova tabela existe para deletá-la
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuario'")
                    if cursor.fetchone():
                        cursor.execute("DROP TABLE usuario")
                    
                    # Restaurar tabela antiga
                    cursor.execute("ALTER TABLE usuario_old RENAME TO usuario")
                    conn.commit()
                    print("Reversão concluída. Tabela original restaurada.")
                
                conn.close()
            except Exception as e2:
                print(f"Erro ao tentar reverter: {e2}")
                print("Você pode precisar restaurar manualmente o banco de dados.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'force':
        recriar_tabela_usuario()
    else:
        print("⚠️  ATENÇÃO: Este script vai recriar a tabela de usuários.")
        print("⚠️  Faça um backup do seu banco de dados antes de continuar!")
        resposta = input("Digite 'SIM' para continuar: ")
        if resposta.upper() == 'SIM':
            recriar_tabela_usuario()
        else:
            print("Operação cancelada pelo usuário.")
