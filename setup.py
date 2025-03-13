import os
import sys
import subprocess

def install_requirements():
    """Install requirements from requirements.txt."""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Requirements installed successfully!")
    except subprocess.CalledProcessError:
        print("Failed to install requirements. Please run: pip install -r requirements.txt")
        return False
    return True

def check_env_file():
    """Check if .env file exists and is properly configured."""
    if not os.path.exists(".env"):
        print("No .env file found. Creating a template .env file...")
        with open(".env", "w") as f:
            f.write("""# Discord Bot Token (from Discord Developer Portal)
DISCORD_TOKEN=your_bot_token_here

# Channel IDs
WELCOME_CHANNEL_ID=000000000000000000
VERIFICATION_CHANNEL_ID=000000000000000000

# Message IDs
VERIFICATION_MESSAGE_ID=000000000000000000

# Role IDs
VERIFIED_ROLE_ID=000000000000000000
MOD_ROLE_ID=000000000000000000
""")
        print(".env file created. Please edit it with your Discord bot token and other settings.")
        return False
    
    # Check if token is set
    with open(".env", "r") as f:
        content = f.read()
        if "your_bot_token_here" in content or "DISCORD_TOKEN=" not in content:
            print("Please set your Discord bot token in the .env file.")
            return False
    
    return True

def main():
    """Run setup process for the bot."""
    print("=== XGC Crypto Discord Bot Setup ===")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("Error: Python 3.8 or higher is required.")
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Check .env file
    if not check_env_file():
        return
    
    print("\nSetup completed successfully!")
    print("\nTo run the bot, use: python bot.py")
    print("Or double-click the run.bat file (Windows only)")
    
    # Ask if user wants to run the bot now
    response = input("\nDo you want to start the bot now? (y/n): ")
    if response.lower() == "y":
        print("Starting bot...")
        os.system("python bot.py")

if __name__ == "__main__":
    main()
