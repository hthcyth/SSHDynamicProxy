# SSH Dynamic Proxy Tool for Windows / Windows SSH动态代理工具

Version 1.1.0

A GUI application to easily set up and manage SSH dynamic proxies (SOCKS) with multiple traffic obfuscation protocols on Windows systems.  
一个用于在Windows系统上轻松设置和管理SSH动态代理(SOCKS)的GUI应用程序，支持多种流量混淆协议。

![SSH Dynamic Proxy Tool Screenshot](screenshot.png)

## Features / 功能特点

- User-friendly GUI for managing SSH dynamic proxy connections  
  友好的GUI界面管理SSH动态代理连接
- Support for both password and key-based authentication  
  支持密码和密钥两种认证方式
- Save and manage multiple SSH server profiles  
  保存和管理多个SSH服务器配置
- Auto-detection of SSH clients (OpenSSH, Git SSH, PuTTY)  
  自动检测SSH客户端(OpenSSH, Git SSH, PuTTY)
- Connection status monitoring  
  连接状态监控
- System tray integration (minimize to tray)  
  系统托盘集成(最小化到托盘)
- Import/export profiles  
  导入/导出配置
- Multiple traffic obfuscation protocols support:  
  支持多种流量混淆协议：
  - Obfs4 protocol (Tor bridge support)  
    Obfs4协议（Tor桥接支持）
  - SSL/TLS encryption via Stunnel  
    通过Stunnel实现SSL/TLS加密
  - Shadowsocks protocol  
    Shadowsocks协议
  - V2Ray protocol  
    V2Ray协议

## Requirements / 系统要求

- Windows 10/11  
  Windows 10/11操作系统
- Python 3.7+ (if running from source)  
  Python 3.7+(如果从源代码运行)
- SSH client:  
  SSH客户端:
  - Windows 10/11 built-in OpenSSH client  
    Windows 10/11内置OpenSSH客户端
  - Git for Windows SSH client  
    Git for Windows的SSH客户端
  - PuTTY's plink.exe  
    PuTTY的plink.exe
- For traffic obfuscation:  
  流量混淆要求:
  - obfs4proxy (included with Tor Browser or available separately)  
    obfs4proxy(包含在Tor浏览器中或可单独安装)
  - stunnel (for SSL/TLS encryption)  
    stunnel(用于SSL/TLS加密)

## Obfuscation Protocols / 混淆协议

### Local Protocol Applications / 本地协议应用

For better portability and ease of use, you can place all protocol executables (obfs4proxy, Shadowsocks, V2Ray, stunnel) directly in the project directory. This approach offers several advantages:  
为了更好的便携性和易用性，您可以将所有协议可执行文件(obfs4proxy, Shadowsocks, V2Ray, stunnel)直接放在项目目录下。这种方法有以下几个优点：

- No need to modify system PATH  
  无需修改系统PATH
- Easy to backup and transfer to another computer  
  易于备份和转移到其他计算机
- Avoids conflicts with other installed versions  
  避免与其他已安装版本冲突
- Simplifies deployment in restricted environments  
  简化在受限环境中的部署

### Obfs4 Configuration / Obfs4配置

#### Installation / 安装
1. Download obfs4proxy from Tor Browser or install separately  
   从Tor浏览器下载obfs4proxy或单独安装
2. Place the obfs4proxy executable in the project directory (d:\DEV\SSHDynamicProxy) or ensure it is in your system PATH  
   将obfs4proxy可执行文件放在项目目录(d:\DEV\SSHDynamicProxy)下，或确保它在系统PATH中

#### Usage / 使用方法
1. In the GUI, when creating or editing a profile, select "Obfs4" as the obfuscation protocol  
   在GUI中创建或编辑配置文件时，选择"Obfs4"作为混淆协议
2. Configure the obfs4 settings (bridge address, cert, etc.)  
   配置obfs4设置（桥接地址、证书等）
3. The application will automatically manage the obfs4proxy process  
   应用程序将自动管理obfs4proxy进程

### Shadowsocks Configuration / Shadowsocks配置

#### Installation / 安装
1. Ensure Python is installed with pip  
   确保已安装带有pip的Python
2. Download the Shadowsocks executable and place it in the project directory (d:\DEV\SSHDynamicProxy) or let the application automatically install the required Shadowsocks package  
   下载Shadowsocks可执行文件并放在项目目录(d:\DEV\SSHDynamicProxy)下，或让应用程序自动安装所需的Shadowsocks包

#### Usage / 使用方法
1. In the GUI, when creating or editing a profile, select "Shadowsocks" as the obfuscation protocol  
   在GUI中创建或编辑配置文件时，选择"Shadowsocks"作为混淆协议
2. Configure the Shadowsocks settings (server, port, password, method)  
   配置Shadowsocks设置（服务器、端口、密码、加密方法）
3. The application will automatically manage the Shadowsocks process  
   应用程序将自动管理Shadowsocks进程

### V2Ray Configuration / V2Ray配置

#### Installation / 安装
1. Download V2Ray from the official website  
   从官方网站下载V2Ray
2. Place the V2Ray executable in the project directory (d:\DEV\SSHDynamicProxy) or ensure it is in your system PATH  
   将V2Ray可执行文件放在项目目录(d:\DEV\SSHDynamicProxy)下，或确保它在系统PATH中

#### Usage / 使用方法
1. In the GUI, when creating or editing a profile, select "V2Ray" as the obfuscation protocol  
   在GUI中创建或编辑配置文件时，选择"V2Ray"作为混淆协议
2. Configure the V2Ray settings (server, port, UUID, etc.)  
   配置V2Ray设置（服务器、端口、UUID等）
3. The application will automatically manage the V2Ray process  
   应用程序将自动管理V2Ray进程

## Stunnel Configuration / Stunnel配置

### Installation / 安装
1. Download stunnel from https://www.stunnel.org  
   从https://www.stunnel.org下载stunnel
2. Install with default options or extract the portable version  
   使用默认选项安装或解压便携版
3. Place the stunnel executable in the project directory (d:\DEV\SSHDynamicProxy) or ensure it is in your system PATH  
   将stunnel可执行文件放在项目目录(d:\DEV\SSHDynamicProxy)下，或确保它在系统PATH中

### Example Configuration / 示例配置
```ini
; stunnel configuration for SSH Dynamic Proxy
; Global settings
cert = stunnel.pem
pid = stunnel.pid
client = yes
debug = 7
output = stunnel.log

[ssh-tunnel]
accept = 127.0.0.1:4433
connect = your-ssh-server.com:443
verifyChain = yes
CAfile = ca-cert.pem
checkHost = your-ssh-server.com
sslVersion = TLSv1.2
ciphers = HIGH:!aNULL:!MD5:!RC4
options = NO_SSLv2
options = NO_SSLv3
options = NO_TLSv1
options = NO_TLSv1.1
```

### Usage / 使用方法
1. In the GUI, when creating or editing a profile, select "Stunnel" as the obfuscation protocol  
   在GUI中创建或编辑配置文件时，选择"Stunnel"作为混淆协议
2. Configure the stunnel settings (local port, remote server, etc.)  
   配置stunnel设置（本地端口、远程服务器等）
3. The application will automatically manage the stunnel process  
   应用程序将自动管理stunnel进程

[Rest of the original README content remains unchanged...]
