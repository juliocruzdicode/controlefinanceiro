"""
Módulo para scripts de migração do banco de dados

Este módulo contém todos os scripts de migração utilizados para atualizar a estrutura
do banco de dados ao longo do desenvolvimento do sistema.

Os scripts são organizados em ordem cronológica e podem ser executados conforme necessário.
"""

# Importações padrão
import os
import sys
import sqlite3
import shutil
from datetime import datetime
import json
from dateutil.relativedelta import relativedelta

# Scripts de migração
from app.migrations.migrate_sqlalchemy import migrar_database
from app.migrations.migrate_accounts import migrar_contas
from app.migrations.migrate_tags import migrar_tags
from app.migrations.migrate_users import migrar_usuarios
from app.migrations.migrate_themes import migrar_temas
from app.migrations.migrate_reset_token import migrar_token_redefinicao
from app.migrations.migrate_verification import migrar_verificacao_email
from app.migrations.migrate_recurring import migrar_recorrentes
from app.migrations.migrate_user_profiles import migrar_perfil_usuario
from app.migrations.migrate_isolation import migrar_isolamento
from app.migrations.migrate_postgres import migrar_para_postgres

def criar_backup_database(db_path=None):
    """
    Cria um backup do banco de dados atual
    
    Args:
        db_path: Caminho do arquivo de banco de dados. Se None, usa o padrão do aplicativo.
    
    Returns:
        str: Caminho do arquivo de backup criado
    """
    from app import app
    
    if db_path is None:
        # Determinar caminho do banco de dados a partir da configuração
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            if 'instance/' in app.config['SQLALCHEMY_DATABASE_URI']:
                db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            else:
                db_path = os.path.join('instance', app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    # Copiar arquivo original para backup
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup criado em: {backup_path}")
    
    return backup_path

def executar_todas_migracoes():
    """
    Executa todas as migrações em sequência
    
    Returns:
        bool: True se todas as migrações foram executadas com sucesso, False caso contrário
    """
    from app import app, db
    
    try:
        with app.app_context():
            print("🚀 Iniciando processo de migração completo...")
            
            # Criar backup antes de começar
            criar_backup_database()
            
            # Executar migrações em ordem
            migrar_database()
            migrar_contas()
            migrar_tags()
            migrar_usuarios()
            migrar_temas()
            migrar_token_redefinicao()
            migrar_verificacao_email()
            migrar_recorrentes()
            migrar_perfil_usuario()
            migrar_isolamento()
            
            print("✅ Todas as migrações foram executadas com sucesso!")
            return True
            
    except Exception as e:
        print(f"❌ Erro durante a migração: {str(e)}")
        return False

def limpar_e_recriar_banco():
    """
    Limpa completamente o banco de dados e recria todas as tabelas
    Útil para resolver problemas de esquema ou reiniciar o banco
    
    Returns:
        bool: True se o banco foi recriado com sucesso, False caso contrário
    """
    from app import app, db
    
    try:
        with app.app_context():
            print("⚠️ Apagando todas as tabelas do banco de dados...")
            db.drop_all()
            
            print("🔄 Recriando todas as tabelas...")
            db.create_all()
            
            print("✅ Banco de dados recriado com sucesso!")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao recriar o banco: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando == "all":
            executar_todas_migracoes()
        elif comando == "backup":
            criar_backup_database()
        elif comando == "recreate":
            limpar_e_recriar_banco()
        elif comando == "postgres":
            migrar_para_postgres()
        else:
            print("Comando não reconhecido. Opções disponíveis:")
            print("  all      - Executa todas as migrações")
            print("  backup   - Cria um backup do banco atual")
            print("  recreate - Limpa e recria todo o banco")
            print("  postgres - Migra de SQLite para PostgreSQL")
    else:
        print("Por favor, especifique um comando. Opções disponíveis:")
        print("  all      - Executa todas as migrações")
        print("  backup   - Cria um backup do banco atual")
        print("  recreate - Limpa e recria todo o banco")
        print("  postgres - Migra de SQLite para PostgreSQL")
