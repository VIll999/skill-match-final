import os
import re

def update_models_for_mysql():
    models_dir = "src/models"
    if not os.path.exists(models_dir):
        print(f"Models directory {models_dir} not found")
        return
        
    for filename in os.listdir(models_dir):
        if filename.endswith(".py"):
            filepath = os.path.join(models_dir, filename)
            with open(filepath, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # PostgreSQL to MySQL replacements
            replacements = {
                'from sqlalchemy.dialects.postgresql import UUID': 'from sqlalchemy import String',
                'UUID(as_uuid=True)': 'String(36)',
                'server_default=text("uuid_generate_v4()")': 'server_default=text("(UUID())")',
                'JSONB': 'JSON',
                'postgresql.JSONB': 'JSON',
                'postgresql.UUID': 'String(36)',
            }
            
            for old, new in replacements.items():
                content = content.replace(old, new)
            
            if content != original_content:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"Updated {filename} for MySQL compatibility")

update_models_for_mysql()