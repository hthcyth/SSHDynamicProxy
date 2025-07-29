#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration Module
Handles saving and loading of application configuration
"""

import os
import json
import logging
import subprocess
import urllib.request
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("config")

class Config:
    """
    Class to handle application configuration
    """
    
    def __init__(self, config_dir=None):
        """
        Initialize the configuration handler
        
        Args:
            config_dir (str, optional): Directory to store configuration files
        """
        # Set up configuration directory
        if config_dir is None:
            self.config_dir = self._get_default_config_dir()
        else:
            self.config_dir = Path(config_dir)
            
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up file paths
        self.profiles_file = self.config_dir / "profiles.json"
        self.settings_file = self.config_dir / "settings.json"
        self.obfs4proxy_path = self._find_obfs4proxy()  # 添加流量混淆工具路径
        
        logger.info(f"Configuration directory: {self.config_dir}")
        logger.info(f"Profiles file: {self.profiles_file}")
        logger.info(f"Settings file: {self.settings_file}")
        if self.obfs4proxy_path:
            logger.info(f"obfs4proxy found at: {self.obfs4proxy_path}")
        else:
            logger.warning("obfs4proxy not found, traffic obfuscation will be disabled")
            
        # 检查流量混淆所需参数
        if self.obfs4proxy_path:
            try:
                # 检查 obfs4proxy 版本
                result = subprocess.run(
                    [self.obfs4proxy_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    logger.info(f"obfs4proxy version: {version}")
                else:
                    logger.warning(f"obfs4proxy version check failed: {result.stderr.strip()}")
            except Exception as e:
                logger.error(f"Error checking obfs4proxy version: {str(e)}")
    
    def _find_obfs4proxy(self):
        """
        查找系统上的obfs4proxy可执行文件，如果找不到则尝试自动安装
        """
        # 检查常见安装路径
        possible_paths = [
            "/usr/bin/obfs4proxy",
            "/usr/local/bin/obfs4proxy",
            "C:/Program Files/obfs4proxy/obfs4proxy.exe",
            "C:/obfs4proxy/obfs4proxy.exe",
            "d:/erwin/DEV/obfs4proxy/obfs4proxy.exe",
            "d:/erwin/DEV/obfs4proxy.exe",
            "C:/Windows/System32/obfs4proxy.exe",
            "C:/Program Files/Tor/obfs4proxy.exe"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                logger.info(f"Found obfs4proxy at: {path}")
                return path
        
        # 尝试在PATH中查找
        try:
            if self.platform == "Windows":
                result = subprocess.run(
                    ["where", "obfs4proxy"], 
                    capture_output=True, 
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(
                    ["which", "obfs4proxy"], 
                    capture_output=True, 
                    text=True
                )
                
            if result.returncode == 0:
                path = result.stdout.strip().splitlines()[0] if self.platform == "Windows" else result.stdout.strip()
                logger.info(f"Found obfs4proxy in PATH: {path}")
                return path
        except Exception as e:
            logger.error(f"Error searching PATH for obfs4proxy: {str(e)}")
        
        # 如果找不到，尝试自动安装
        logger.warning("obfs4proxy not found, attempting to install...")
        try:
            if self.platform == "Windows":
                # Windows安装逻辑
                install_dir = self.config_dir / "obfs4proxy"
                install_dir.mkdir(exist_ok=True)
                exe_path = install_dir / "obfs4proxy.exe"
                
                if not exe_path.exists():
                    logger.info("Downloading obfs4proxy for Windows...")
                    url = "https://github.com/erwin/SSHDynamicProxy/releases/download/v1.0/obfs4proxy-windows-amd64.exe"
                    urllib.request.urlretrieve(url, exe_path)
                    logger.info(f"Downloaded obfs4proxy to {exe_path}")
                
                return str(exe_path)
            else:
                # Linux/macOS安装逻辑
                logger.info("Attempting to install obfs4proxy via package manager...")
                try:
                    if self.platform == "Linux":
                        subprocess.run(["sudo", "apt-get", "install", "-y", "obfs4proxy"], check=True)
                    elif self.platform == "Darwin":
                        subprocess.run(["brew", "install", "obfs4proxy"], check=True)
                    
                    # 检查安装是否成功
                    result = subprocess.run(["which", "obfs4proxy"], capture_output=True, text=True)
                    if result.returncode == 0:
                        path = result.stdout.strip()
                        logger.info(f"Successfully installed obfs4proxy at {path}")
                        return path
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install obfs4proxy: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error installing obfs4proxy: {str(e)}")
        
        logger.error("obfs4proxy installation failed, traffic obfuscation will be disabled")
        return None
    
    def _get_default_config_dir(self):
        """
        Get the default configuration directory based on the platform
        
        Returns:
            Path: Path to the configuration directory
        """
        # Use AppData on Windows, ~/.config on Linux, ~/Library on macOS
        if os.name == "nt":  # Windows
            base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
            return Path(base_dir) / "SSHDynamicProxy"
        elif os.name == "posix":  # Linux/macOS
            if os.path.exists(os.path.expanduser("~/.config")):
                # Linux
                return Path(os.path.expanduser("~/.config/ssh-dynamic-proxy"))
            else:
                # macOS
                return Path(os.path.expanduser("~/Library/Application Support/SSHDynamicProxy"))
        else:
            # Fallback to current directory
            return Path("./config")
    
    def load_profiles(self):
        """
        Load SSH profiles from the profiles file
        
        Returns:
            list: List of profile dictionaries
        """
        if not self.profiles_file.exists():
            logger.info("Profiles file does not exist, returning empty list")
            return []
            
        try:
            with open(self.profiles_file, "r") as f:
                profiles = json.load(f)
                logger.info(f"Loaded {len(profiles)} profiles")
                return profiles
        except Exception as e:
            logger.error(f"Error loading profiles: {str(e)}")
            return []
    
    def save_profiles(self, profiles):
        """
        Save SSH profiles to the profiles file
        
        Args:
            profiles (list): List of profile dictionaries
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.profiles_file, "w") as f:
                json.dump(profiles, f, indent=2)
                logger.info(f"Saved {len(profiles)} profiles")
                return True
        except Exception as e:
            logger.error(f"Error saving profiles: {str(e)}")
            return False
    
    def load_settings(self):
        """
        Load application settings from the settings file
        
        Returns:
            dict: Settings dictionary
        """
        if not self.settings_file.exists():
            logger.info("Settings file does not exist, returning default settings")
            return self.get_default_settings()
            
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
                logger.info("Settings loaded")
                
                # Merge with defaults to ensure all settings exist
                default_settings = self.get_default_settings()
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                        
                return settings
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            return self.get_default_settings()
    
    def save_settings(self, settings):
        """
        Save application settings to the settings file
        
        Args:
            settings (dict): Settings dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=2)
                logger.info("Settings saved")
                return True
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return False
    
    def get_default_settings(self):
        """
        Get default application settings
        
        Returns:
            dict: Default settings dictionary
        """
        return {
            "auto_connect_last": False,
            "minimize_to_tray": True,
            "start_minimized": False,
            "check_updates": True,
            "theme": "system",
            "log_level": "INFO"
        }
    
    def backup_profiles(self):
        """
        Create a backup of the profiles file
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.profiles_file.exists():
            logger.info("No profiles file to backup")
            return False
            
        try:
            backup_file = self.config_dir / "profiles.backup.json"
            with open(self.profiles_file, "r") as src:
                with open(backup_file, "w") as dst:
                    dst.write(src.read())
            logger.info(f"Profiles backed up to {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Error backing up profiles: {str(e)}")
            return False
    
    def restore_profiles_backup(self):
        """
        Restore profiles from backup
        
        Returns:
            bool: True if successful, False otherwise
        """
        backup_file = self.config_dir / "profiles.backup.json"
        if not backup_file.exists():
            logger.info("No backup file to restore")
            return False
            
        try:
            with open(backup_file, "r") as src:
                with open(self.profiles_file, "w") as dst:
                    dst.write(src.read())
            logger.info("Profiles restored from backup")
            return True
        except Exception as e:
            logger.error(f"Error restoring profiles: {str(e)}")
            return False
    
    def export_profiles(self, export_path):
        """
        Export profiles to a file
        
        Args:
            export_path (str): Path to export the profiles to
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.profiles_file.exists():
            logger.info("No profiles to export")
            return False
            
        try:
            with open(self.profiles_file, "r") as src:
                with open(export_path, "w") as dst:
                    dst.write(src.read())
            logger.info(f"Profiles exported to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting profiles: {str(e)}")
            return False
    
    def import_profiles(self, import_path, merge=True):
        """
        Import profiles from a file
        
        Args:
            import_path (str): Path to import the profiles from
            merge (bool): Whether to merge with existing profiles or replace them
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(import_path, "r") as f:
                imported_profiles = json.load(f)
                
            if merge and self.profiles_file.exists():
                # Merge with existing profiles
                existing_profiles = self.load_profiles()
                
                # Create a set of existing profile names for quick lookup
                existing_names = {p["name"] for p in existing_profiles}
                
                # Add profiles that don't already exist
                for profile in imported_profiles:
                    if profile["name"] not in existing_names:
                        existing_profiles.append(profile)
                        
                # Save merged profiles
                self.save_profiles(existing_profiles)
                logger.info(f"Merged {len(imported_profiles)} imported profiles with existing profiles")
            else:
                # Replace existing profiles
                self.save_profiles(imported_profiles)
                logger.info(f"Imported {len(imported_profiles)} profiles")
                
            return True
        except Exception as e:
            logger.error(f"Error importing profiles: {str(e)}")
            return False


# Test function
def test_config():
    """Test the Config class"""
    config = Config()
    print(f"Config directory: {config.config_dir}")
    print(f"Profiles file: {config.profiles_file}")
    
    # Test saving and loading profiles
    test_profiles = [
        {
            "name": "Test Server",
            "host": "example.com",
            "port": 22,
            "username": "user",
            "local_port": 1080
        }
    ]
    
    config.save_profiles(test_profiles)
    loaded_profiles = config.load_profiles()
    
    print(f"Loaded profiles: {loaded_profiles}")


if __name__ == "__main__":
    test_config()
