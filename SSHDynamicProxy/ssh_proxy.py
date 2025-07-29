#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSH Proxy Module
Handles SSH connections and dynamic proxy setup
"""

import os
import sys
import subprocess
import platform
import shlex
import logging
import socket
import time
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ssh_proxy")

class SSHProxy:
    """
    Class to handle SSH connections and dynamic proxy setup
    """
    
    def __init__(self):
        """Initialize the SSH proxy handler"""
        self.platform = platform.system()
        self.ssh_command = self._get_ssh_command()
        logger.info(f"Platform detected: {self.platform}")
        logger.info(f"SSH command: {self.ssh_command}")
    
    def _get_ssh_command(self):
        """
        Get the appropriate SSH command based on the platform
        Returns the path to the SSH executable
        """
        if self.platform == "Windows":
            # Check for OpenSSH in Windows 10/11
            openssh_path = Path("C:/Windows/System32/OpenSSH/ssh.exe")
            if openssh_path.exists():
                return str(openssh_path)
                
            # Check for Git's SSH
            git_ssh_path = Path("C:/Program Files/Git/usr/bin/ssh.exe")
            if git_ssh_path.exists():
                return str(git_ssh_path)
                
            # Check for PuTTY's plink
            plink_path = Path("C:/Program Files/PuTTY/plink.exe")
            if plink_path.exists():
                return str(plink_path)
                
            # Default to 'ssh', assuming it's in PATH
            return "ssh"
        else:
            # For Linux/macOS, use the system SSH
            return "ssh"
    
    def connect(self, host, port, username, local_port, password=None, key_path=None, 
               obfs_protocol=None, obfs_config=None):
        """
        Establish an SSH connection with dynamic port forwarding
        支持多种流量混淆技术和SSL/TLS隧道
        
        Args:
            host (str): SSH server hostname or IP
            port (int): SSH server port
            username (str): SSH username
            local_port (int): Local port for the SOCKS proxy
            password (str, optional): SSH password
            key_path (str, optional): Path to SSH private key
            obfs_protocol (str): 混淆协议类型，如 'obfs4', 'shadowsocks', 'v2ray'，None表示不启用混淆
            obfs_config (dict): 混淆协议配置
            
        Returns:
            tuple: (SSH process, Obfuscation protocol) 如果启用混淆
            or
            subprocess.Popen: SSH process 如果不启用混淆
        """
        obfs_protocol_instance = None
        obfs_port = None
        
        try:
            # 如果需要流量混淆，先启动混淆代理
            if obfs_protocol and obfs_config:
                logger.info(f"Starting traffic obfuscation using {obfs_protocol} protocol...")
                
                # 导入混淆协议工厂
                from obfuscation import ObfuscationFactory
                
                # 创建混淆协议实例
                obfs_protocol_instance = ObfuscationFactory.create_protocol(obfs_protocol, obfs_config)
                
                if obfs_protocol_instance and obfs_protocol_instance.start():
                    obfs_port = obfs_protocol_instance.get_local_port()
                    logger.info(f"Obfuscation proxy started on port {obfs_port}")
                else:
                    logger.error(f"Failed to start {obfs_protocol} obfuscation proxy")
                    raise Exception(f"Failed to start {obfs_protocol} obfuscation proxy")

                
                # 已在前面的代码中处理了错误情况
                logger.info(f"Obfuscation proxy running on port {obfs_port}")
            
            # Build the SSH command
            cmd = []
            
            # 如果使用stunnel协议，修改连接参数
            if obfs_protocol == 'stunnel':
                # 通过本地stunnel端口连接
                host = "127.0.0.1"
                port = int(obfs_config.get('local_port', 4433))
            
            # 如果启用了混淆，修改SSH命令通过混淆代理连接
            if obfs_protocol_instance:
                # 使用ProxyCommand通过混淆代理连接
                proxy_cmd = f"connect -S 127.0.0.1:{obfs_port} %h %p"
                base_cmd = [
                    self.ssh_command,
                    "-o", f"ProxyCommand={proxy_cmd}",
                    "-D", f"127.0.0.1:{local_port}",
                    "-p", str(port),
                    f"{username}@{host}",
                    "-N"  # No command execution
                ]
            else:
                # 标准SSH命令
                if self.platform == "Windows" and "plink" in self.ssh_command and password:
                    base_cmd = [
                        self.ssh_command,
                        "-ssh",
                        "-D", f"127.0.0.1:{local_port}",
                        "-P", str(port),
                        "-l", username,
                        "-pw", password,
                        host,
                        "-N"  # No command execution
                    ]
                else:
                    base_cmd = [
                        self.ssh_command,
                        "-D", f"127.0.0.1:{local_port}",
                        "-p", str(port),
                        f"{username}@{host}",
                        "-N"  # No command execution
                    ]
            
            # 添加额外选项
            cmd = base_cmd.copy()
                
            # 添加密钥文件（如果指定）
            if key_path:
                cmd.insert(1, "-i")
                cmd.insert(2, key_path)
            
            # 添加更好的连接选项
            cmd.insert(1, "-o")
            cmd.insert(2, "ServerAliveInterval=60")
            cmd.insert(3, "-o")
            cmd.insert(4, "ServerAliveCountMax=3")
            cmd.insert(1, "-C")  # 压缩
            cmd.insert(1, "-q")  # 安静模式
            
            # 日志记录命令（不包括密码）
            log_cmd = cmd.copy()
            if password and "-pw" in log_cmd:
                pw_index = log_cmd.index("-pw")
                log_cmd[pw_index + 1] = "********"
            logger.info(f"Executing SSH command: {' '.join(log_cmd)}")
            
            # 启动SSH进程
            if self.platform == "Windows":
                # Windows系统
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                # Unix-like系统
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # 检查进程是否启动成功
            if process.poll() is not None:
                # 进程立即终止
                stdout, stderr = process.communicate()
                error_msg = stderr.decode('utf-8', errors='replace')
                logger.error(f"SSH process failed to start: {error_msg}")
                raise Exception(f"SSH connection failed: {error_msg}")
            
            logger.info(f"SSH connection established to {host}:{port}")
            # 返回结果：如果启用了混淆，返回元组；否则只返回SSH进程
            if obfs_protocol_instance:
                return (process, obfs_protocol_instance)
            else:
                return process
            
        except Exception as e:
            logger.error(f"Error establishing SSH connection: {str(e)}")
            # 清理混淆进程
            if obfs_protocol_instance:
                obfs_protocol_instance.stop()
            raise
    
    def start_obfs_proxy(self, bridge, cert, iat_mode=0):
        """
        启动obfs4proxy进行流量混淆
        
        Args:
            bridge (str): 桥接地址 (host:port)
            cert (str): 证书
            iat_mode (int): IAT模式 (0 or 1)
            
        Returns:
            tuple: (进程对象, 本地端口)
        """
        try:
            # 查找可用的本地端口
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', 0))
                obfs_port = s.getsockname()[1]
            
            # 构建命令
            cmd = [
                "obfs4proxy",
                "client",
                f"socks5://127.0.0.1:{obfs_port}",
                f"obfs4://{cert}@{bridge}?iat-mode={iat_mode}"
            ]
            
            logger.info(f"Starting obfs4proxy: {' '.join(cmd)}")
            
            # 启动进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待代理准备就绪
            time.sleep(1)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logger.error(f"obfs4proxy failed to start: {stderr}")
                return (None, None)
            
            return (process, obfs_port)
        except Exception as e:
            logger.error(f"Error starting obfs4proxy: {str(e)}")
            return (None, None)
    
    def stop_obfs_proxy(self, process):
        """停止obfs4proxy进程"""
        if process:
            try:
                process.terminate()
                process.wait(timeout=3)
            except:
                try:
                    process.kill()
                except:
                    pass
    
    def start_health_check(self, process, local_port, callback=None, interval=30):
        """
        Start health check for the SSH tunnel
        
        Args:
            process (subprocess.Popen): The SSH process
            local_port (int): Local port of the tunnel
            callback (function): Callback to notify health status changes
            interval (int): Health check interval in seconds
        """
        self.health_check_active = True
        
        def health_check_thread():
            while self.health_check_active:
                time.sleep(interval)
                if not self.check_tunnel_health(local_port):
                    logger.warning(f"Tunnel health check failed on port {local_port}")
                    if callback:
                        callback(False)
                    # Attempt reconnect
                    try:
                        logger.info("Attempting to reconnect...")
                        new_process = self.connect(
                            process.args['host'],
                            process.args['port'],
                            process.args['username'],
                            local_port,
                            password=process.args.get('password'),
                            key_path=process.args.get('key_path')
                        )
                        if new_process:
                            process = new_process
                            if callback:
                                callback(True)
                    except Exception as e:
                        logger.error(f"Reconnect failed: {str(e)}")
                elif callback:
                    callback(True)
        
        threading.Thread(target=health_check_thread, daemon=True).start()
    
    def stop_health_check(self):
        """Stop the health check thread"""
        self.health_check_active = False
    
    def check_tunnel_health(self, local_port):
        """
        Check if the SSH tunnel is healthy by testing the local SOCKS port
        
        Args:
            local_port (int): Local port of the tunnel
            
        Returns:
            bool: True if tunnel is responsive, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect(('127.0.0.1', local_port))
                return True
        except:
            return False
    
    def disconnect(self, processes):
        """
        Disconnect SSH and clean up processes
        
        Args:
            processes: SSH process or (SSH process, Obfuscation protocol) tuple
        """
        try:
            if isinstance(processes, tuple):
                ssh_process, obfs_protocol_instance = processes
                # 先关闭SSH进程
                if ssh_process and ssh_process.poll() is None:
                    # 先尝试停止健康检查（如果存在）
                    if hasattr(self, 'health_check_active'):
                        self.stop_health_check()
                    logger.info("Terminating SSH connection...")
                    
                    if self.platform == "Windows":
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(ssh_process.pid)])
                    else:
                        ssh_process.terminate()
                        ssh_process.wait(timeout=5)
                    
                    logger.info("SSH connection terminated")
                
                # 再关闭混淆协议实例
                if obfs_protocol_instance:
                    logger.info("Stopping obfuscation proxy...")
                    obfs_protocol_instance.stop()
                    logger.info("Obfuscation proxy terminated")
            else:
                # 只有SSH进程
                ssh_process = processes
                if ssh_process and ssh_process.poll() is None:
                    # 先尝试停止健康检查（如果存在）
                    if hasattr(self, 'health_check_active'):
                        self.stop_health_check()
                    logger.info("Terminating SSH connection...")
                    
                    if self.platform == "Windows":
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(ssh_process.pid)])
                    else:
                        ssh_process.terminate()
                        ssh_process.wait(timeout=5)
                    
                    logger.info("SSH connection terminated")
                    
        except Exception as e:
            logger.error(f"Error disconnecting SSH: {str(e)}")
            # 尝试强制终止进程
            try:
                if isinstance(processes, tuple):
                    ssh_process, _ = processes
                    if ssh_process and ssh_process.poll() is None:
                        ssh_process.kill()
                elif processes and processes.poll() is None:
                    processes.kill()
            except:
                pass
    
    def check_connection(self, process):
        """
        Check if an SSH connection is still active
        
        Args:
            process (subprocess.Popen): The SSH process to check
            
        Returns:
            bool: True if the connection is active, False otherwise
        """
        if process is None:
            return False
            
        return process.poll() is None
    
    def get_connection_info(self, process, local_port):
        """
        Get information about the SSH connection
        
        Args:
            process (subprocess.Popen): The SSH process
            local_port (int): The local port used for the SOCKS proxy
            
        Returns:
            dict: Connection information
        """
        if not self.check_connection(process):
            return {
                "status": "disconnected",
                "local_port": local_port
            }
            
        return {
            "status": "connected",
            "local_port": local_port,
            "pid": process.pid
        }


# Test function
def test_ssh_proxy():
    """Test the SSHProxy class"""
    proxy = SSHProxy()
    print(f"SSH command: {proxy.ssh_command}")
    print(f"Platform: {proxy.platform}")


if __name__ == "__main__":
    test_ssh_proxy()
