from app import app, db
from models import Usuario
import sys

def upgrade_db():
    """Atualiza o esquema do banco de dados"""
    with app.app_context():
        print("Atualizando esquema do banco de dados...")
        db.create_all()  # Isso não vai alterar tabelas existentes
        
        # Aplicar migrações
        print("Verificando se é necessário aplicar migrações...")
        try:
            # Verificar se os novos campos existem
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('usuario')]
            
            # Se não existir coluna telefone, executar ALTER TABLE
            if 'telefone' not in columns:
                print("Adicionando novos campos ao modelo Usuario...")
                
                # SQLite tem limitações com ALTER TABLE, então verificamos o banco
                if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                    # Para SQLite, precisamos fazer manualmente
                    try:
                        with db.engine.connect() as conn:
                            conn.execute("ALTER TABLE usuario ADD COLUMN telefone VARCHAR(20)")
                            conn.execute("ALTER TABLE usuario ADD COLUMN data_nascimento DATE")
                            conn.execute("ALTER TABLE usuario ADD COLUMN sexo VARCHAR(1)")
                            conn.execute("ALTER TABLE usuario ADD COLUMN cidade VARCHAR(100)")
                            conn.commit()
                        print("Campos adicionados com sucesso!")
                    except Exception as e:
                        print(f"Erro ao adicionar campos no SQLite: {e}")
                        print("Você pode precisar recriar o banco manualmente.")
                else:
                    # Para PostgreSQL e outros
                    try:
                        with db.engine.connect() as conn:
                            conn.execute("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS telefone VARCHAR(20)")
                            conn.execute("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS data_nascimento DATE")
                            conn.execute("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS sexo VARCHAR(1)")
                            conn.execute("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS cidade VARCHAR(100)")
                            conn.commit()
                        print("Campos adicionados com sucesso!")
                    except Exception as e:
                        print(f"Erro ao adicionar campos: {e}")
            else:
                print("Campos já existem na tabela. Nenhuma migração necessária.")
        except Exception as e:
            print(f"Erro ao verificar ou aplicar migrações: {e}")
    
    print("Processo concluído!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        print("Downgrade não implementado. Execute manualmente se necessário.")
    else:
        upgrade_db()
