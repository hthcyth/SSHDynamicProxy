#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
混淆协议模块
支持多种流量混淆协议，包括obfs4、Shadowsocks和V2Ray
"""

import os
import sys
import subprocess
import socket
import time
import logging
import json
import random
import threading
from abc import ABC, abstractmethod
from pathlib import Path

# 配置日志
logger = logging.getLogger("obfuscation")

class ObfuscationProtocol(ABC):
    """
    混淆协议基类
    所有具体的混淆协议实现都应该继承这个类
    """
    
    def __init__(self, config):
        """
        初始化混淆协议
        
        Args:
            config (dict): 协议配置
        """
        self.config = config
        self.process = None
        self.local_port = None
    
    @abstractmethod
    def start(self):
        """
        启动混淆代理
        
        Returns:
            bool: 是否成功启动
        """
        pass
    
    @abstractmethod
    def stop(self):
        """
        停止混淆代理
        """
        pass
    
    def get_local_port(self):
        """
        获取本地代理端口
        
        Returns:
            int: 本地端口号
        """
        return self.local_port
    
    def _find_available_port(self):
        """
        查找可用的本地端口
        
        Returns:
            int: 可用的端口号
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]


class Obfs4Protocol(ObfuscationProtocol):
    """
    obfs4 混淆协议实现
    使用 obfs4proxy 进行流量混淆
    """
    
    def __init__(self, config):
        """
        初始化 obfs4 混淆协议
        
        Args:
            config (dict): 包含以下字段:
                - bridge (str): 桥接地址 (host:port)
                - cert (str): 证书
                - iat_mode (int, optional): IAT模式 (0 or 1), 默认为 0
        """
        super().__init__(config)
        self.bridge = config.get('bridge')
        self.cert = config.get('cert')
        self.iat_mode = config.get('iat_mode', 0)
        
        # 查找 obfs4proxy 可执行文件
        self.obfs4proxy_path = self._find_obfs4proxy()
        if not self.obfs4proxy_path:
            logger.error("obfs4proxy executable not found")
    
    def _find_obfs4proxy(self):
        """
        查找 obfs4proxy 可执行文件
        
        Returns:
            str: obfs4proxy 可执行文件路径，如果未找到则返回 None
        """
        # 预设路径
        # 获取当前脚本所在目录
        script_dir = Path(__file__).parent.absolute()
        
        paths = [
            str(script_dir / "obfs4proxy"),  # 项目目录中的可执行文件
            str(script_dir / "obfs4proxy.exe"),
            "obfs4proxy",  # 如果在 PATH 中
            "obfs4proxy.exe",
            str(Path.home() / "obfs4proxy"),
            str(Path.home() / "obfs4proxy.exe"),
            str(Path.home() / ".local" / "bin" / "obfs4proxy"),
            "C:/Program Files/obfs4proxy/obfs4proxy.exe",
            "C:/Program Files (x86)/obfs4proxy/obfs4proxy.exe"
        ]
        
        # 检查每个路径
        for path in paths:
            try:
                # 尝试运行 obfs4proxy 版本命令
                result = subprocess.run(
                    [path, "--version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    logger.info(f"Found obfs4proxy at {path}")
                    return path
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        
        return None
    
    def start(self):
        """
        启动 obfs4proxy 进行流量混淆
        
        Returns:
            bool: 是否成功启动
        """
        if not self.obfs4proxy_path:
            logger.error("Cannot start obfs4proxy: executable not found")
            return False
            
        if not self.bridge or not self.cert:
            logger.error("Cannot start obfs4proxy: missing bridge or cert")
            return False
        
        try:
            # 查找可用的本地端口
            self.local_port = self._find_available_port()
            
            # 构建命令
            cmd = [
                self.obfs4proxy_path,
                "client",
                f"socks5://127.0.0.1:{self.local_port}",
                f"obfs4://{self.cert}@{self.bridge}?iat-mode={self.iat_mode}"
            ]
            
            logger.info(f"Starting obfs4proxy: {' '.join(cmd)}")
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待代理准备就绪
            time.sleep(1)
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                logger.error(f"obfs4proxy failed to start: {stderr}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error starting obfs4proxy: {str(e)}")
            return False
    
    def stop(self):
        """
        停止 obfs4proxy 进程
        """
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            finally:
                self.process = None


class ShadowsocksProtocol(ObfuscationProtocol):
    """
    Shadowsocks 混淆协议实现
    使用 shadowsocks-libev 进行流量混淆
    """
    
    def __init__(self, config):
        """
        初始化 Shadowsocks 混淆协议
        
        Args:
            config (dict): 包含以下字段:
                - server (str): 服务器地址
                - server_port (int): 服务器端口
                - password (str): 密码
                - method (str): 加密方法
                - plugin (str, optional): 插件名称
                - plugin_opts (str, optional): 插件选项
        """
        super().__init__(config)
        self.server = config.get('server')
        self.server_port = config.get('server_port')
        self.password = config.get('password')
        self.method = config.get('method', 'aes-256-gcm')
        self.plugin = config.get('plugin', '')
        self.plugin_opts = config.get('plugin_opts', '')
        
        # 查找 ss-local 可执行文件
        self.ss_local_path = self._find_ss_local()
        if not self.ss_local_path:
            logger.error("ss-local executable not found")
    
    def _find_ss_local(self):
        """
        查找 ss-local 可执行文件
        
        Returns:
            str: ss-local 可执行文件路径，如果未找到则返回 None
        """
        # 预设路径
        # 获取当前脚本所在目录
        script_dir = Path(__file__).parent.absolute()
        
        paths = [
            str(script_dir / "ss-local"),  # 项目目录中的可执行文件
            str(script_dir / "ss-local.exe"),
            "ss-local",  # 如果在 PATH 中
            "ss-local.exe",
            str(Path.home() / "ss-local"),
            str(Path.home() / "ss-local.exe"),
            str(Path.home() / ".local" / "bin" / "ss-local"),
            "C:/Program Files/Shadowsocks/ss-local.exe",
            "C:/Program Files (x86)/Shadowsocks/ss-local.exe"
        ]
        
        # 检查每个路径
        for path in paths:
            try:
                # 尝试运行 ss-local 版本命令
                result = subprocess.run(
                    [path, "-h"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 or "shadowsocks" in result.stdout.lower() or "shadowsocks" in result.stderr.lower():
                    logger.info(f"Found ss-local at {path}")
                    return path
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        
        return None
    
    def start(self):
        """
        启动 Shadowsocks 进行流量混淆
        
        Returns:
            bool: 是否成功启动
        """
        if not self.ss_local_path:
            logger.error("Cannot start Shadowsocks: executable not found")
            return False
            
        if not self.server or not self.server_port or not self.password:
            logger.error("Cannot start Shadowsocks: missing server, port or password")
            return False
        
        try:
            # 查找可用的本地端口
            self.local_port = self._find_available_port()
            
            # 构建命令
            cmd = [
                self.ss_local_path,
                "-s", self.server,
                "-p", str(self.server_port),
                "-k", self.password,
                "-m", self.method,
                "-l", str(self.local_port),
                "-b", "127.0.0.1"
            ]
            
            # 添加插件参数（如果有）
            if self.plugin:
                cmd.extend(["-P", self.plugin])
                if self.plugin_opts:
                    cmd.extend(["-G", self.plugin_opts])
            
            logger.info(f"Starting Shadowsocks: {' '.join([c if i < 6 else '****' for i, c in enumerate(cmd)])}")
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待代理准备就绪
            time.sleep(1)
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                logger.error(f"Shadowsocks failed to start: {stderr}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error starting Shadowsocks: {str(e)}")
            return False
    
    def stop(self):
        """
        停止 Shadowsocks 进程
        """
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            finally:
                self.process = None


class V2rayProtocol(ObfuscationProtocol):
    """
    V2Ray 混淆协议实现
    使用 v2ray 进行流量混淆
    """
    
    def __init__(self, config):
        """
        初始化 V2Ray 混淆协议
        
        Args:
            config (dict): 包含以下字段:
                - server (str): 服务器地址
                - server_port (int): 服务器端口
                - uuid (str): UUID
                - alter_id (int, optional): Alter ID, 默认为 0
                - security (str, optional): 加密方法, 默认为 'auto'
                - network (str, optional): 传输协议, 默认为 'tcp'
                - type (str, optional): 伪装类型, 默认为 'none'
                - host (str, optional): 伪装域名
                - path (str, optional): WebSocket 路径
                - tls (bool, optional): 是否启用 TLS, 默认为 False
        """
        super().__init__(config)
        self.server = config.get('server')
        self.server_port = config.get('server_port')
        self.uuid = config.get('uuid')
        self.alter_id = config.get('alter_id', 0)
        self.security = config.get('security', 'auto')
        self.network = config.get('network', 'tcp')
        self.type = config.get('type', 'none')
        self.host = config.get('host', '')
        self.path = config.get('path', '')
        self.tls = config.get('tls', False)
        self.config_file = None
        
        # 查找 v2ray 可执行文件
        self.v2ray_path = self._find_v2ray()
        if not self.v2ray_path:
            logger.error("v2ray executable not found")
    
    def _find_v2ray(self):
        """
        查找 v2ray 可执行文件
        
        Returns:
            str: v2ray 可执行文件路径，如果未找到则返回 None
        """
        # 预设路径
        # 获取当前脚本所在目录
        script_dir = Path(__file__).parent.absolute()
        
        paths = [
            str(script_dir / "v2ray"),  # 项目目录中的可执行文件
            str(script_dir / "v2ray.exe"),
            "v2ray",  # 如果在 PATH 中
            "v2ray.exe",
            str(Path.home() / "v2ray"),
            str(Path.home() / "v2ray.exe"),
            str(Path.home() / ".local" / "bin" / "v2ray"),
            "C:/Program Files/v2ray/v2ray.exe",
            "C:/Program Files (x86)/v2ray/v2ray.exe"
        ]
        
        # 检查每个路径
        for path in paths:
            try:
                # 尝试运行 v2ray 版本命令
                result = subprocess.run(
                    [path, "version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 or "v2ray" in result.stdout.lower():
                    logger.info(f"Found v2ray at {path}")
                    return path
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        
        return None
    
    def _create_config_file(self):
        """
        创建 V2Ray 配置文件
        
        Returns:
            str: 配置文件路径
        """
        # 创建临时配置文件
        config_dir = Path.home() / ".config" / "sshdynamicproxy"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / f"v2ray_config_{random.randint(1000, 9999)}.json"
        
        # 基本配置
        config = {
            "log": {
                "loglevel": "warning"
            },
            "inbounds": [
                {
                    "port": self.local_port,
                    "listen": "127.0.0.1",
                    "protocol": "socks",
                    "settings": {
                        "udp": True
                    }
                }
            ],
            "outbounds": [
                {
                    "protocol": "vmess",
                    "settings": {
                        "vnext": [
                            {
                                "address": self.server,
                                "port": self.server_port,
                                "users": [
                                    {
                                        "id": self.uuid,
                                        "alterId": self.alter_id,
                                        "security": self.security
                                    }
                                ]
                            }
                        ]
                    },
                    "streamSettings": {
                        "network": self.network,
                        "security": "tls" if self.tls else "none"
                    }
                }
            ]
        }
        
        # 添加传输协议特定配置
        if self.network == "ws":
            config["outbounds"][0]["streamSettings"]["wsSettings"] = {
                "path": self.path,
                "headers": {"Host": self.host} if self.host else {}
            }
        elif self.network == "http":
            config["outbounds"][0]["streamSettings"]["httpSettings"] = {
                "path": self.path.split(",") if self.path else ["/"],
                "host": self.host.split(",") if self.host else []
            }
        elif self.network == "tcp" and self.type == "http":
            config["outbounds"][0]["streamSettings"]["tcpSettings"] = {
                "header": {
                    "type": "http",
                    "request": {
                        "version": "1.1",
                        "method": "GET",
                        "path": self.path.split(",") if self.path else ["/"],
                        "headers": {
                            "Host": self.host.split(",") if self.host else [],
                            "User-Agent": [
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"
                            ],
                            "Accept-Encoding": ["gzip, deflate"],
                            "Connection": ["keep-alive"],
                            "Pragma": "no-cache"
                        }
                    }
                }
            }
        
        # 写入配置文件
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return str(config_file)
    
    def start(self):
        """
        启动 V2Ray 进行流量混淆
        
        Returns:
            bool: 是否成功启动
        """
        if not self.v2ray_path:
            logger.error("Cannot start V2Ray: executable not found")
            return False
            
        if not self.server or not self.server_port or not self.uuid:
            logger.error("Cannot start V2Ray: missing server, port or UUID")
            return False
        
        try:
            # 查找可用的本地端口
            self.local_port = self._find_available_port()
            
            # 创建配置文件
            self.config_file = self._create_config_file()
            
            # 构建命令
            cmd = [
                self.v2ray_path,
                "run",
                "-c", self.config_file
            ]
            
            logger.info(f"Starting V2Ray: {' '.join(cmd)}")
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待代理准备就绪
            time.sleep(2)
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                logger.error(f"V2Ray failed to start: {stderr}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error starting V2Ray: {str(e)}")
            return False
    
    def stop(self):
        """
        停止 V2Ray 进程
        """
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            finally:
                self.process = None
                
        # 删除临时配置文件
        if self.config_file and os.path.exists(self.config_file):
            try:
                os.remove(self.config_file)
            except:
                pass


class StunnelProtocol(ObfuscationProtocol):
    """Stunnel 协议实现
    使用 stunnel 进行 TLS 加密
    """
    
    def __init__(self, config):
        """
        初始化 Stunnel 协议
        
        Args:
            config (dict): 包含以下字段:
                - stunnel_local_port (int, optional): 本地端口, 默认为 1081
                - stunnel_remote (str): 远程服务器地址 (host:port)
                - stunnel_verify (bool, optional): 是否验证证书, 默认为 False
                - stunnel_options (str, optional): 额外的 stunnel 选项
        """
        super().__init__(config)
        self.local_port = config.get('stunnel_local_port', 1081)
        self.remote_server = config.get('stunnel_remote', '')
        self.verify = config.get('stunnel_verify', False)
        self.options = config.get('stunnel_options', '')
        self.config_file = None
        self.process = None
        
        # 查找 stunnel 可执行文件
        self.stunnel_path = self._find_stunnel()
        if not self.stunnel_path:
            logger.error("stunnel executable not found")
    
    def _find_stunnel(self):
        """
        查找 stunnel 可执行文件
        
        Returns:
            str: stunnel 可执行文件路径，如果未找到则返回 None
        """
        # 预设路径
        # 获取当前脚本所在目录
        script_dir = Path(__file__).parent.absolute()
        
        paths = [
            str(script_dir / "stunnel"),  # 项目目录中的可执行文件
            str(script_dir / "stunnel.exe"),
            "stunnel",  # 如果在 PATH 中
            "stunnel.exe",
            str(Path.home() / "stunnel"),
            str(Path.home() / "stunnel.exe"),
            str(Path.home() / ".local" / "bin" / "stunnel"),
            "/usr/bin/stunnel",
            "/usr/local/bin/stunnel",
            "C:/Program Files/stunnel/stunnel.exe",
            "C:/Program Files (x86)/stunnel/stunnel.exe"
        ]
        
        # 检查每个路径
        for path in paths:
            try:
                # 尝试运行 stunnel 版本命令
                result = subprocess.run(
                    [path, "-version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 or "stunnel" in result.stdout.lower() or "stunnel" in result.stderr.lower():
                    logger.info(f"Found stunnel at {path}")
                    return path
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        
        return None
    
    def start(self):
        """启动 Stunnel 进行 TLS 加密
        
        Returns:
            bool: 是否成功启动
        """
        if not self.stunnel_path:
            logger.error("Cannot start stunnel: executable not found")
            return False
            
        if not self.remote_server:
            logger.error("Cannot start stunnel: remote server not specified")
            return False
            
        # 创建临时配置文件
        import tempfile
        self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False)
        
        # 生成配置内容
        config_content = f"""
; stunnel configuration for SSH Dynamic Proxy
; Generated by SSHDynamicProxy
client = yes
debug = 5
pid = 

[ssh-proxy]
accept = 127.0.0.1:{self.local_port}
connect = {self.remote_server}
verifyChain = {'yes' if self.verify else 'no'}
{self.options}
"""
        
        # 写入配置文件
        self.config_file.write(config_content)
        self.config_file.close()
        
        # 启动 stunnel 进程
        try:
            logger.info(f"Starting stunnel with config file: {self.config_file.name}")
            self.process = subprocess.Popen(
                [self.stunnel_path, self.config_file.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 检查进程是否成功启动
            time.sleep(1)
            if self.process.poll() is not None:
                stderr = self.process.stderr.read()
                logger.error(f"Failed to start stunnel: {stderr}")
                return False
                
            logger.info(f"Stunnel started successfully on port {self.local_port}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting stunnel: {str(e)}")
            return False
        
    def stop(self):
        """停止 Stunnel 进程"""
        if self.process:
            try:
                logger.info("Stopping stunnel process")
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None
            except Exception as e:
                logger.error(f"Error stopping stunnel: {str(e)}")
                try:
                    self.process.kill()
                except:
                    pass
                self.process = None
                
        # 清理临时配置文件
        if self.config_file and os.path.exists(self.config_file.name):
            try:
                os.unlink(self.config_file.name)
                self.config_file = None
            except Exception as e:
                logger.error(f"Error removing stunnel config file: {str(e)}")



class ObfuscationFactory:
    """
    混淆协议工厂类
    用于创建不同类型的混淆协议实例
    """
    
    @staticmethod
    def create_protocol(protocol_type, config):
        """
        创建混淆协议实例
        
        Args:
            protocol_type (str): 协议类型，如 'obfs4', 'shadowsocks', 'v2ray'
            config (dict): 协议配置
            
        Returns:
            ObfuscationProtocol: 混淆协议实例，如果类型不支持则返回 None
        """
        if protocol_type.lower() == 'obfs4':
            return Obfs4Protocol(config)
        elif protocol_type.lower() == 'shadowsocks':
            return ShadowsocksProtocol(config)
        elif protocol_type.lower() == 'v2ray':
            return V2rayProtocol(config)
        elif protocol_type.lower() == 'stunnel':
            return StunnelProtocol(config)
        else:
            logger.error(f"Unsupported obfuscation protocol: {protocol_type}")
            return None