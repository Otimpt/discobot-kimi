#!/usr/bin/env python3
"""
Script de Setup para o Discord AI Bot v2
"""

import os
import sys
import subprocess
from pathlib import Path


def print_banner():
    """Printa banner do setup."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           🤖 Discord AI Bot v2 - Setup                        ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""")


def check_python_version():
    """Verifica versão do Python."""
    print("📋 Verificando versão do Python...")
    
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 ou superior é necessário!")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def install_dependencies():
    """Instala dependências."""
    print("\n📦 Instalando dependências...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependências instaladas com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        sys.exit(1)


def create_directories():
    """Cria diretórios necessários."""
    print("\n📁 Criando diretórios...")
    
    dirs = [
        "data",
        "data/uploads",
        "data/backups",
        "data/logs",
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Diretórios criados!")


def setup_config():
    """Configura arquivo de configuração."""
    print("\n⚙️ Configurando...")
    
    if not Path("config.yaml").exists():
        if Path("config-example.yaml").exists():
            import shutil
            shutil.copy("config-example.yaml", "config.yaml")
            print("✅ Arquivo config.yaml criado a partir do exemplo!")
            print("⚠️  Por favor, edite config.yaml com suas configurações.")
        else:
            print("❌ Arquivo config-example.yaml não encontrado!")
            sys.exit(1)
    else:
        print("ℹ️  Arquivo config.yaml já existe.")


def check_env_variables():
    """Verifica variáveis de ambiente."""
    print("\n🔍 Verificando variáveis de ambiente...")
    
    required = ["DISCORD_BOT_TOKEN"]
    optional = ["OPENAI_API_KEY"]
    
    missing_required = [var for var in required if not os.getenv(var)]
    missing_optional = [var for var in optional if not os.getenv(var)]
    
    if missing_required:
        print(f"⚠️  Variáveis obrigatórias não definidas: {', '.join(missing_required)}")
        print("   Você pode definir no arquivo .env ou no config.yaml")
    else:
        print("✅ Todas as variáveis obrigatórias estão definidas!")
    
    if missing_optional:
        print(f"ℹ️  Variáveis opcionais não definidas: {', '.join(missing_optional)}")


def main():
    """Função principal do setup."""
    print_banner()
    
    check_python_version()
    install_dependencies()
    create_directories()
    setup_config()
    check_env_variables()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           ✅ Setup Concluído!                                 ║
║                                                               ║
║   Próximos passos:                                            ║
║   1. Edite config.yaml com suas configurações                 ║
║   2. Ou defina variáveis de ambiente no arquivo .env          ║
║   3. Execute: python bot.py                                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
