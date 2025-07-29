#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSH Dynamic Proxy Tool for Windows
A GUI application to easily set up SSH dynamic proxies (SOCKS)
"""

import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import subprocess
from datetime import datetime
import ttkthemes  # 添加主题支持

from ssh_proxy import SSHProxy
from config import Config

class SSHDynamicProxyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SSH动态代理工具")
        self.root.geometry("720x580")  # 增加窗口尺寸
        self.root.resizable(True, True)
        
        # 应用现代化主题
        self.style = ttkthemes.ThemedStyle(self.root)
        self.style.set_theme("arc")  # 使用现代化主题
        self.style.configure('TButton', padding=6, font=('Segoe UI', 10))
        self.style.configure('TLabel', font=('Segoe UI', 10))
        self.style.configure('TFrame', background=self.style.lookup('TFrame', 'background'))
        
        # 设置主窗口背景色
        self.root.configure(bg=self.style.lookup('TFrame', 'background'))
        
        # 设置图标
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
            
        # Initialize variables
        self.config = Config()
        self.profiles = self.config.load_profiles()
        self.active_connections = {}
        self.ssh_proxy = SSHProxy()
        
        # Create GUI elements
        self.create_menu()
        self.create_widgets()
        
        # Load profiles into the listbox
        self.load_profiles_to_listbox()
        
        # Create tray icon
        self.create_tray_icon()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Profile", command=self.new_profile)
        file_menu.add_command(label="Import Profiles", command=self.import_profiles)
        file_menu.add_command(label="Export Profiles", command=self.export_profiles)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_widgets(self):
        """Create the main application widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Profile list
        profile_frame = ttk.LabelFrame(main_frame, text="SSH Profiles", padding="5")
        profile_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Profile listbox with scrollbar
        self.profile_listbox = tk.Listbox(profile_frame, selectmode=tk.SINGLE, activestyle='dotbox')
        self.profile_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.profile_listbox.bind('<<ListboxSelect>>', self.on_profile_select)
        
        scrollbar = ttk.Scrollbar(profile_frame, orient=tk.VERTICAL, command=self.profile_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.profile_listbox.config(yscrollcommand=scrollbar.set)
        
        # Profile buttons
        profile_btn_frame = ttk.Frame(profile_frame, padding="5")
        profile_btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(profile_btn_frame, text="Add", command=self.new_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(profile_btn_frame, text="Edit", command=self.edit_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(profile_btn_frame, text="Delete", command=self.delete_profile).pack(side=tk.LEFT, padx=2)
        
        # Right side - Profile details and connection
        details_frame = ttk.LabelFrame(main_frame, text="Profile Details", padding="5")
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Profile details
        self.details_text = tk.Text(details_frame, height=10, width=40, state=tk.DISABLED)
        self.details_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Connection buttons
        conn_btn_frame = ttk.Frame(details_frame)
        conn_btn_frame.pack(fill=tk.X, pady=5)
        
        self.connect_btn = ttk.Button(conn_btn_frame, text="Connect", command=self.connect_profile)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = ttk.Button(conn_btn_frame, text="Disconnect", command=self.disconnect_profile, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        # 状态栏框架
        status_frame = ttk.LabelFrame(self.root, text="连接状态", padding="5")
        status_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # 状态栏样式
        self.status_text = tk.Text(status_frame, height=6, 
                                 font=('Segoe UI', 9), 
                                 bg="#f0f0f0", fg="#333")
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.status_text.config(state=tk.DISABLED)
        
        # 连接状态指示器
        status_indicator_frame = ttk.Frame(status_frame)
        status_indicator_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.status_indicator = ttk.Label(status_indicator_frame, text="●", 
                                        foreground="#aaa", font=('Segoe UI', 14))
        self.status_indicator.pack(side=tk.LEFT, padx=(10, 5))
        
        # SOCKS5地址标签
        self.socks5_label = ttk.Label(status_indicator_frame, text="SOCKS5: 未连接", 
                                     font=('Segoe UI', 9, 'bold'))
        self.socks5_label.pack(side=tk.LEFT, padx=5)
        
        # 添加初始状态消息
        self.update_status("应用已启动。准备连接...")
        
        # 版权信息
        copyright_frame = ttk.Frame(self.root)
        copyright_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        ttk.Label(copyright_frame, text="© 2025 SSH动态代理工具 v1.1.0", 
                 font=('Segoe UI', 8), foreground="#777").pack(side=tk.RIGHT)
    
    def load_profiles_to_listbox(self):
        """Load saved profiles into the listbox"""
        self.profile_listbox.delete(0, tk.END)
        for profile in self.profiles:
            self.profile_listbox.insert(tk.END, profile['name'])
    
    def on_profile_select(self, event):
        """Handle profile selection from listbox"""
        if not self.profile_listbox.curselection():
            return
            
        index = self.profile_listbox.curselection()[0]
        profile = self.profiles[index]
        
        # Update details text
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        details = f"Name: {profile['name']}\n"
        details += f"Host: {profile['host']}\n"
        details += f"Port: {profile['port']}\n"
        details += f"Username: {profile['username']}\n"
        details += f"Authentication: {'Key' if profile.get('key_path') else 'Password'}\n"
        if profile.get('key_path'):
            details += f"Key Path: {profile['key_path']}\n"
        details += f"Local Port: {profile['local_port']}\n"
        if profile.get('description'):
            details += f"\nDescription: {profile['description']}\n"
            
        self.details_text.insert(tk.END, details)
        self.details_text.config(state=tk.DISABLED)
        
        # Update button states
        profile_name = profile['name']
        if profile_name in self.active_connections:
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
        else:
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
    
    def new_profile(self):
        """Create a new SSH profile"""
        dialog = ProfileDialog(self.root, "New SSH Profile")
        if dialog.result:
            self.profiles.append(dialog.result)
            self.config.save_profiles(self.profiles)
            self.load_profiles_to_listbox()
            self.update_status(f"Profile '{dialog.result['name']}' created.")
    
    def edit_profile(self):
        """Edit the selected profile"""
        if not self.profile_listbox.curselection():
            messagebox.showinfo("Info", "Please select a profile to edit.")
            return
            
        index = self.profile_listbox.curselection()[0]
        profile = self.profiles[index]
        
        # Check if profile is connected
        if profile['name'] in self.active_connections:
            messagebox.showwarning("Warning", "Please disconnect the profile before editing.")
            return
            
        dialog = ProfileDialog(self.root, "Edit SSH Profile", profile)
        if dialog.result:
            self.profiles[index] = dialog.result
            self.config.save_profiles(self.profiles)
            self.load_profiles_to_listbox()
            self.update_status(f"Profile '{dialog.result['name']}' updated.")
    
    def delete_profile(self):
        """Delete the selected profile"""
        if not self.profile_listbox.curselection():
            messagebox.showinfo("Info", "Please select a profile to delete.")
            return
            
        index = self.profile_listbox.curselection()[0]
        profile = self.profiles[index]
        
        # Check if profile is connected
        if profile['name'] in self.active_connections:
            messagebox.showwarning("Warning", "Please disconnect the profile before deleting.")
            return
            
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the profile '{profile['name']}'?")
        if confirm:
            del self.profiles[index]
            self.config.save_profiles(self.profiles)
            self.load_profiles_to_listbox()
            self.update_status(f"Profile '{profile['name']}' deleted.")
    
    def connect_profile(self):
        """Connect to the selected SSH profile"""
        if not self.profile_listbox.curselection():
            messagebox.showinfo("Info", "Please select a profile to connect.")
            return
            
        index = self.profile_listbox.curselection()[0]
        profile = self.profiles[index]
        
        # Check if already connected
        if profile['name'] in self.active_connections:
            messagebox.showinfo("Info", f"Profile '{profile['name']}' is already connected.")
            return
            
        # Get password if needed
        password = None
        if not profile.get('key_path'):
            password = simpledialog.askstring("Password", 
                                             f"Enter password for {profile['username']}@{profile['host']}:", 
                                             show='*')
            if password is None:  # User cancelled
                return
        
        # Start connection in a separate thread
        self.update_status(f"Connecting to {profile['host']}...")
        
        def connect_thread():
            try:
                # 获取混淆协议配置（如果有）
                obfs_protocol = profile.get('obfs_protocol', 'none')
                obfs_config = {}
                
                # 根据不同的混淆协议设置配置
                if obfs_protocol == 'obfs4':
                    obfs_config = {
                        'bridge': profile.get('obfs_bridge', ''),
                        'cert': profile.get('obfs_cert', '')
                    }
                elif obfs_protocol == 'stunnel':
                    obfs_config = {
                        'local_port': profile.get('stunnel_local_port', '1081'),
                        'remote': profile.get('stunnel_remote', ''),
                        'verify': profile.get('stunnel_verify', False),
                        'options': profile.get('stunnel_options', '')
                    }
                elif obfs_protocol == 'shadowsocks':
                    obfs_config = {
                        'server': profile.get('ss_server', ''),
                        'port': profile.get('ss_port', '8388'),
                        'password': profile.get('ss_password', ''),
                        'method': profile.get('ss_method', 'aes-256-gcm')
                    }
                elif obfs_protocol == 'v2ray':
                    obfs_config = {
                        'server': profile.get('v2ray_server', ''),
                        'port': profile.get('v2ray_port', '1080'),
                        'uuid': profile.get('v2ray_uuid', ''),
                        'alter_id': profile.get('v2ray_alter_id', '0'),
                        'security': profile.get('v2ray_security', 'auto')
                    }
                
                # 调用修改后的connect方法
                result = self.ssh_proxy.connect(
                    profile['host'],
                    profile['port'],
                    profile['username'],
                    profile['local_port'],
                    password=password,
                    key_path=profile.get('key_path'),
                    obfs_protocol=obfs_protocol if obfs_protocol != 'none' else None,
                    obfs_config=obfs_config
                )
                
                # 处理返回结果：可能是单个进程，也可能是(ssh_process, obfs_protocol_instance)
                if isinstance(result, tuple):
                    ssh_process = result[0]
                    obfs_protocol_instance = result[1]
                else:
                    ssh_process = result
                    obfs_protocol_instance = None
                
                if ssh_process:
                    self.active_connections[profile['name']] = {
                        'ssh_process': ssh_process,
                        'obfs_protocol_instance': obfs_protocol_instance,
                        'profile': profile,
                        'started': datetime.now()
                    }
                    
                    # Update UI from main thread
                    self.root.after(0, lambda: self.update_connection_status(profile['name'], True))
            except Exception as e:
                # Update UI from main thread
                self.root.after(0, lambda: self.handle_connection_error(profile['name'], str(e)))
        
        thread = threading.Thread(target=connect_thread)
        thread.daemon = True
        thread.start()
    
    def disconnect_profile(self):
        """Disconnect the selected SSH profile"""
        if not self.profile_listbox.curselection():
            messagebox.showinfo("Info", "Please select a profile to disconnect.")
            return
            
        index = self.profile_listbox.curselection()[0]
        profile = self.profiles[index]
        
        # Check if connected
        if profile['name'] not in self.active_connections:
            messagebox.showinfo("Info", f"Profile '{profile['name']}' is not connected.")
            return
            
        # Terminate the SSH and obfs processes
        connection = self.active_connections[profile['name']]
        self.ssh_proxy.disconnect(
            connection['ssh_process'], 
            connection.get('obfs_protocol_instance')
        )
        
        # Remove from active connections
        del self.active_connections[profile['name']]
        
        # Update UI
        self.update_connection_status(profile['name'], False)
    
    def update_connection_status(self, profile_name, is_connected):
        """更新连接状态UI"""
        if is_connected:
            port = self.active_connections[profile_name]['profile']['local_port']
            self.update_status(f"已连接到 {profile_name}。SOCKS5代理地址: socks5://127.0.0.1:{port}")
            # 更新状态指示器和SOCKS5标签
            self.status_indicator.config(foreground="#4CAF50")  # 绿色表示活动
            self.socks5_label.config(text=f"SOCKS5: 127.0.0.1:{port}")
        else:
            self.update_status(f"已断开与 {profile_name} 的连接。")
            # 如果没有活动连接，恢复默认状态
            if not self.active_connections:
                self.status_indicator.config(foreground="#aaa")  # 灰色表示未活动
                self.socks5_label.config(text="SOCKS5: 未连接")
            
        # 更新按钮状态（如果当前选中此配置文件）
        if self.profile_listbox.curselection():
            index = self.profile_listbox.curselection()[0]
            selected_profile = self.profiles[index]
            
            if selected_profile['name'] == profile_name:
                if is_connected:
                    self.connect_btn.config(state=tk.DISABLED)
                    self.disconnect_btn.config(state=tk.NORMAL)
                else:
                    self.connect_btn.config(state=tk.NORMAL)
                    self.disconnect_btn.config(state=tk.DISABLED)
                    
        # 更新系统托盘图标状态
        if hasattr(self, 'tray'):
            self.update_tray_icon()
            
    def create_tray_icon(self):
        """Create system tray icon"""
        try:
            from PIL import Image, ImageDraw
            import pystray
            
            # Create tray icon image
            image = Image.new('RGB', (64, 64), 'black')
            dc = ImageDraw.Draw(image)
            dc.rectangle((16, 16, 48, 48), fill='green')
            
            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem('显示窗口', self.show_app),
                pystray.MenuItem('退出', self.quit_app)
            )
            
            # Create tray icon
            self.tray = pystray.Icon("SSHProxy", image, "SSH动态代理", menu)
            
            # Start tray in separate thread
            threading.Thread(target=self.tray.run, daemon=True).start()
        except ImportError:
            logger.error("System tray requires pystray and Pillow installed")
            
    def show_app(self, icon=None, item=None):
        """Show application window"""
        self.root.deiconify()
        self.root.lift()
        
    def hide_app(self, event=None):
        """Hide application to system tray"""
        if hasattr(self, 'tray'):
            self.root.withdraw()
            
    def quit_app(self, icon=None, item=None):
        """Quit application"""
        # Disconnect all active connections
        for name in list(self.active_connections.keys()):
            self.disconnect_profile_by_name(name)
            
        # Close application
        self.root.destroy()
        if hasattr(self, 'tray'):
            self.tray.stop()
            
    def disconnect_profile_by_name(self, profile_name):
        """Disconnect profile by name"""
        if profile_name in self.active_connections:
            connection = self.active_connections[profile_name]
            self.ssh_proxy.disconnect(connection['process'])
            del self.active_connections[profile_name]
            
    def update_tray_icon(self):
        """Update tray icon based on connection status"""
        if not hasattr(self, 'tray'):
            return
            
        from PIL import Image, ImageDraw
        
        # Create new icon
        color = 'green' if self.active_connections else 'gray'
        image = Image.new('RGB', (64, 64), 'black')
        dc = ImageDraw.Draw(image)
        dc.rectangle((16, 16, 48, 48), fill=color)
        
        # Update tray icon
        self.tray.icon = image
        self.tray.title = f"SSH动态代理 ({len(self.active_connections)}个活动连接)"
        
    def on_closing(self):
        """Handle window closing event - always minimize to tray"""
        self.hide_app()
    
    def handle_connection_error(self, profile_name, error_msg):
        """Handle connection errors"""
        self.update_status(f"Error connecting to {profile_name}: {error_msg}")
        messagebox.showerror("Connection Error", f"Failed to connect to {profile_name}:\n{error_msg}")
    
    def update_status(self, message):
        """Update the status text area with a timestamped message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_msg = f"[{timestamp}] {message}\n"
        
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, status_msg)
        self.status_text.see(tk.END)  # Scroll to the end
        self.status_text.config(state=tk.DISABLED)
    
    def import_profiles(self):
        """Import profiles from a JSON file"""
        file_path = filedialog.askopenfilename(
            title="Import Profiles",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            if self.config.import_profiles(file_path):
                self.profiles = self.config.load_profiles()
                self.load_profiles_to_listbox()
                self.update_status(f"Profiles imported from {file_path}")
            else:
                messagebox.showerror("Import Error", "Failed to import profiles. Check the log for details.")
    
    def export_profiles(self):
        """Export profiles to a JSON file"""
        file_path = filedialog.asksaveasfilename(
            title="Export Profiles",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            if self.config.export_profiles(file_path):
                self.update_status(f"Profiles exported to {file_path}")
            else:
                messagebox.showerror("Export Error", "Failed to export profiles. Check the log for details.")
    
    def show_documentation(self):
        """Show the documentation"""
        doc_text = """
SSH Dynamic Proxy Tool Documentation

This tool allows you to create and manage SSH dynamic proxy connections (SOCKS proxies) with optional traffic obfuscation.

How to use:
1. Create a new SSH profile with your server details
2. Select an obfuscation protocol if needed (None, Obfs4, Stunnel, Shadowsocks, V2Ray)
3. Configure the protocol-specific settings
4. Select the profile and click Connect
5. Enter your password if required
6. The SOCKS proxy will be available at localhost:port
7. Configure your applications to use the SOCKS proxy

Obfuscation Protocols:
- None: Direct SSH connection without obfuscation
- Obfs4: Uses Tor's obfs4proxy to obfuscate traffic (requires obfs4proxy in PATH)
- Stunnel: Encrypts traffic using SSL/TLS (requires stunnel in PATH)
- Shadowsocks: Uses Shadowsocks protocol for obfuscation
- V2Ray: Uses V2Ray protocol for obfuscation (requires V2Ray in PATH)

For more information, visit the project website.
        """
        
        doc_window = tk.Toplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("500x400")
        
        text = tk.Text(doc_window, wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, doc_text)
        text.config(state=tk.DISABLED)
    
    def show_about(self):
        """Show the about dialog"""
        about_text = """
SSH Dynamic Proxy Tool for Windows

Version 1.1.0

A tool to create and manage SSH dynamic proxies (SOCKS) with support for
multiple traffic obfuscation protocols (Obfs4, Stunnel, Shadowsocks, V2Ray).

© 2025
        """
        messagebox.showinfo("About", about_text)


class ProfileDialog:
    """Dialog for creating or editing SSH profiles"""
    def __init__(self, parent, title, profile=None):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x450")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create form
        self.create_form(profile)
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def create_form(self, profile):
        """Create the profile form"""
        frame = ttk.Frame(self.dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Profile name
        ttk.Label(frame, text="Profile Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=profile['name'] if profile else "")
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Host
        ttk.Label(frame, text="SSH Host:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.host_var = tk.StringVar(value=profile['host'] if profile else "")
        ttk.Entry(frame, textvariable=self.host_var, width=30).grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Port
        ttk.Label(frame, text="SSH Port:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.StringVar(value=str(profile['port']) if profile else "22")
        ttk.Entry(frame, textvariable=self.port_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Username
        ttk.Label(frame, text="Username:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar(value=profile['username'] if profile else "")
        ttk.Entry(frame, textvariable=self.username_var, width=30).grid(row=3, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Authentication method
        ttk.Label(frame, text="Authentication:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.auth_var = tk.StringVar(value="key" if profile and profile.get('key_path') else "password")
        
        auth_frame = ttk.Frame(frame)
        auth_frame.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(auth_frame, text="Password", variable=self.auth_var, value="password", 
                       command=self.toggle_key_path).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(auth_frame, text="Key File", variable=self.auth_var, value="key",
                       command=self.toggle_key_path).pack(side=tk.LEFT)
        
        # Key path
        self.key_frame = ttk.Frame(frame)
        self.key_frame.grid(row=5, column=0, columnspan=2, sticky=tk.W+tk.E, pady=5)
        
        ttk.Label(self.key_frame, text="Key File Path:").pack(side=tk.LEFT, padx=(0, 5))
        self.key_path_var = tk.StringVar(value=profile.get('key_path', "") if profile else "")
        ttk.Entry(self.key_frame, textvariable=self.key_path_var, width=30).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(self.key_frame, text="Browse...", command=self.browse_key).pack(side=tk.LEFT, padx=(5, 0))
        
        # Local port
        ttk.Label(frame, text="Local Port:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.local_port_var = tk.StringVar(value=str(profile['local_port']) if profile else "1080")
        ttk.Entry(frame, textvariable=self.local_port_var, width=10).grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # Traffic Obfuscation Section
        obfs_section = ttk.LabelFrame(frame, text="Traffic Obfuscation", padding=5)
        obfs_section.grid(row=7, column=0, columnspan=2, sticky=tk.W+tk.E, pady=5)
        
        # Protocol selection
        self.obfs_protocol_var = tk.StringVar(value=profile.get('obfs_protocol', 'none') if profile else 'none')
        
        protocol_frame = ttk.Frame(obfs_section)
        protocol_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(protocol_frame, text="Protocol:").pack(side=tk.LEFT, padx=(0,10))
        ttk.Radiobutton(protocol_frame, text="None", variable=self.obfs_protocol_var, 
                       value="none", command=self.toggle_obfs_fields).pack(side=tk.LEFT, padx=(0,10))
        ttk.Radiobutton(protocol_frame, text="Obfs4", variable=self.obfs_protocol_var, 
                       value="obfs4", command=self.toggle_obfs_fields).pack(side=tk.LEFT, padx=(0,10))
        ttk.Radiobutton(protocol_frame, text="Stunnel", variable=self.obfs_protocol_var, 
                       value="stunnel", command=self.toggle_obfs_fields).pack(side=tk.LEFT, padx=(0,10))
        ttk.Radiobutton(protocol_frame, text="Shadowsocks", variable=self.obfs_protocol_var, 
                       value="shadowsocks", command=self.toggle_obfs_fields).pack(side=tk.LEFT, padx=(0,10))
        ttk.Radiobutton(protocol_frame, text="V2Ray", variable=self.obfs_protocol_var, 
                       value="v2ray", command=self.toggle_obfs_fields).pack(side=tk.LEFT)
        
        # Obfs4 fields container (initially hidden)
        self.obfs4_fields_frame = ttk.Frame(obfs_section)
        
        # Bridge address
        bridge_frame = ttk.Frame(self.obfs4_fields_frame)
        bridge_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(bridge_frame, text="Bridge Address:").pack(side=tk.LEFT, padx=(0,5))
        self.obfs_bridge_var = tk.StringVar(value=profile.get('obfs_bridge', '') if profile else '')
        bridge_entry = ttk.Entry(bridge_frame, textvariable=self.obfs_bridge_var)
        bridge_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Certificate
        cert_frame = ttk.Frame(self.obfs4_fields_frame)
        cert_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cert_frame, text="Certificate:").pack(side=tk.LEFT, padx=(0,5))
        self.obfs_cert_var = tk.StringVar(value=profile.get('obfs_cert', '') if profile else '')
        cert_entry = ttk.Entry(cert_frame, textvariable=self.obfs_cert_var)
        cert_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Stunnel fields container (initially hidden)
        self.stunnel_fields_frame = ttk.Frame(obfs_section)
        
        # Stunnel configuration
        stunnel_config_frame = ttk.LabelFrame(self.stunnel_fields_frame, text="Stunnel Configuration", padding=5)
        stunnel_config_frame.pack(fill=tk.X, pady=5)
        
        # Local port
        ttk.Label(stunnel_config_frame, text="Local Port:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.stunnel_local_port_var = tk.StringVar(value=profile.get('stunnel_local_port', '1081') if profile else '1081')
        ttk.Entry(stunnel_config_frame, textvariable=self.stunnel_local_port_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Remote server
        ttk.Label(stunnel_config_frame, text="Remote Server:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.stunnel_remote_var = tk.StringVar(value=profile.get('stunnel_remote', '') if profile else '')
        ttk.Entry(stunnel_config_frame, textvariable=self.stunnel_remote_var, width=30).grid(row=1, column=1, sticky=tk.W+tk.E, pady=2)
        
        # Verify certificate
        self.stunnel_verify_var = tk.BooleanVar(value=profile.get('stunnel_verify', False) if profile else False)
        ttk.Checkbutton(stunnel_config_frame, text="Verify Certificate", 
                       variable=self.stunnel_verify_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Additional options
        ttk.Label(stunnel_config_frame, text="Extra Options:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.stunnel_options_var = tk.StringVar(value=profile.get('stunnel_options', '') if profile else '')
        ttk.Entry(stunnel_config_frame, textvariable=self.stunnel_options_var).grid(row=3, column=1, sticky=tk.W+tk.E, pady=2)
        
        # Test connection button
        ttk.Button(stunnel_config_frame, text="Test Configuration", 
                  command=self.test_stunnel_config).grid(row=4, column=0, columnspan=2, pady=5)

        # Shadowsocks fields container (initially hidden)
        self.shadowsocks_fields_frame = ttk.Frame(obfs_section)
        
        # Shadowsocks configuration
        ss_config_frame = ttk.LabelFrame(self.shadowsocks_fields_frame, text="Shadowsocks Configuration", padding=5)
        ss_config_frame.pack(fill=tk.X, pady=5)
        
        # Server
        ttk.Label(ss_config_frame, text="Server:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ss_server_var = tk.StringVar(value=profile.get('ss_server', '') if profile else '')
        ttk.Entry(ss_config_frame, textvariable=self.ss_server_var, width=30).grid(row=0, column=1, sticky=tk.W+tk.E, pady=2)
        
        # Port
        ttk.Label(ss_config_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ss_port_var = tk.StringVar(value=profile.get('ss_port', '8388') if profile else '8388')
        ttk.Entry(ss_config_frame, textvariable=self.ss_port_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Password
        ttk.Label(ss_config_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.ss_password_var = tk.StringVar(value=profile.get('ss_password', '') if profile else '')
        ttk.Entry(ss_config_frame, textvariable=self.ss_password_var, width=30, show='*').grid(row=2, column=1, sticky=tk.W+tk.E, pady=2)
        
        # Encryption method
        ttk.Label(ss_config_frame, text="Method:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.ss_method_var = tk.StringVar(value=profile.get('ss_method', 'aes-256-gcm') if profile else 'aes-256-gcm')
        methods = ['aes-256-gcm', 'aes-128-gcm', 'chacha20-ietf-poly1305', 'aes-256-cfb', 'aes-128-cfb']
        method_combo = ttk.Combobox(ss_config_frame, textvariable=self.ss_method_var, values=methods, width=20)
        method_combo.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # V2Ray fields container (initially hidden)
        self.v2ray_fields_frame = ttk.Frame(obfs_section)
        
        # V2Ray configuration
        v2ray_config_frame = ttk.LabelFrame(self.v2ray_fields_frame, text="V2Ray Configuration", padding=5)
        v2ray_config_frame.pack(fill=tk.X, pady=5)
        
        # Server
        ttk.Label(v2ray_config_frame, text="Server:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.v2ray_server_var = tk.StringVar(value=profile.get('v2ray_server', '') if profile else '')
        ttk.Entry(v2ray_config_frame, textvariable=self.v2ray_server_var, width=30).grid(row=0, column=1, sticky=tk.W+tk.E, pady=2)
        
        # Port
        ttk.Label(v2ray_config_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.v2ray_port_var = tk.StringVar(value=profile.get('v2ray_port', '1080') if profile else '1080')
        ttk.Entry(v2ray_config_frame, textvariable=self.v2ray_port_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # UUID
        ttk.Label(v2ray_config_frame, text="UUID:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.v2ray_uuid_var = tk.StringVar(value=profile.get('v2ray_uuid', '') if profile else '')
        ttk.Entry(v2ray_config_frame, textvariable=self.v2ray_uuid_var, width=30).grid(row=2, column=1, sticky=tk.W+tk.E, pady=2)
        
        # Alter ID
        ttk.Label(v2ray_config_frame, text="Alter ID:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.v2ray_alter_id_var = tk.StringVar(value=profile.get('v2ray_alter_id', '0') if profile else '0')
        ttk.Entry(v2ray_config_frame, textvariable=self.v2ray_alter_id_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Security
        ttk.Label(v2ray_config_frame, text="Security:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.v2ray_security_var = tk.StringVar(value=profile.get('v2ray_security', 'auto') if profile else 'auto')
        security_options = ['auto', 'aes-128-gcm', 'chacha20-poly1305', 'none']
        security_combo = ttk.Combobox(v2ray_config_frame, textvariable=self.v2ray_security_var, values=security_options, width=20)
        security_combo.grid(row=4, column=1, sticky=tk.W, pady=2)

        # Initially show/hide based on selection
        self.toggle_obfs_fields()
        
        # Adjust dialog size and position
        self.dialog.geometry("550x650")
        self.center_dialog()
        
        # Make dialog resizable with minimum size
        self.dialog.resizable(True, True)
        self.dialog.minsize(550, 550)
        
        # Configure grid weights for better resizing
        frame.grid_rowconfigure(9, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
        # Add scrollbar functionality
        self.setup_scrollbar(frame)
        
        # Help text
        help_text = ttk.Label(obfs_section, 
                            text="Note: Select an obfuscation protocol to bypass network restrictions.\n" +
                                 "- Obfs4: Get bridge info from Tor Project\n" +
                                 "- Stunnel: Configure SSL/TLS encryption\n" +
                                 "- Shadowsocks: Configure server and encryption method\n" +
                                 "- V2Ray: Configure server and protocol settings",
                            font=('Segoe UI', 8),
                            foreground="#666",
                            justify=tk.LEFT)
        help_text.pack(anchor=tk.W, pady=(5,0), fill=tk.X)
        
        # Description
        ttk.Label(frame, text="Description:").grid(row=9, column=0, sticky=tk.W+tk.N, pady=5)
        self.description_var = tk.Text(frame, width=30, height=4)
        self.description_var.grid(row=9, column=1, sticky=tk.W+tk.E, pady=5)
        if profile and profile.get('description'):
            self.description_var.insert(tk.END, profile['description'])
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        # Initial state of key path frame
        self.toggle_key_path()
    
    def toggle_key_path(self):
        """Show or hide the key path field based on authentication method"""
        if self.auth_var.get() == "key":
            self.key_frame.grid()
        else:
            self.key_frame.grid_remove()
    
    def toggle_obfs_fields(self):
        """Show or hide the obfs fields based on protocol selection"""
        # Hide all fields first
        self.obfs4_fields_frame.pack_forget()
        self.stunnel_fields_frame.pack_forget()
        self.shadowsocks_fields_frame.pack_forget()
        self.v2ray_fields_frame.pack_forget()
        
        # Show appropriate fields based on selection
        protocol = self.obfs_protocol_var.get()
        if protocol == "obfs4":
            self.obfs4_fields_frame.pack(fill=tk.X, expand=True)
            self.dialog.geometry("550x650")
        elif protocol == "stunnel":
            self.stunnel_fields_frame.pack(fill=tk.X, expand=True)
            self.dialog.geometry("550x650")
        elif protocol == "shadowsocks":
            self.shadowsocks_fields_frame.pack(fill=tk.X, expand=True)
            self.dialog.geometry("550x650")
        elif protocol == "v2ray":
            self.v2ray_fields_frame.pack(fill=tk.X, expand=True)
            self.dialog.geometry("550x650")
        else:
            self.dialog.geometry("550x550")
            
        self.center_dialog()
        
    def test_stunnel_config(self):
        """Test the stunnel configuration"""
        try:
            local_port = int(self.stunnel_local_port_var.get())
            if local_port < 1 or local_port > 65535:
                raise ValueError("Invalid local port")
                
            if not self.stunnel_remote_var.get().strip():
                raise ValueError("Remote server is required")
                
            # Generate temporary config file
            config = f"""
[ssh-proxy]
client = yes
accept = 127.0.0.1:{local_port}
connect = {self.stunnel_remote_var.get().strip()}
verifyChain = {'yes' if self.stunnel_verify_var.get() else 'no'}
{self.stunnel_options_var.get()}
"""
            
            # Save to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                f.write(config)
                temp_path = f.name
                
            # Test config
            result = subprocess.run(["stunnel", "-test", temp_path], capture_output=True, text=True)
            
            if result.returncode == 0:
                messagebox.showinfo("Success", "Stunnel configuration is valid")
            else:
                messagebox.showerror("Error", f"Stunnel configuration error:\n{result.stderr}")
                
            # Clean up
            os.unlink(temp_path)
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to test stunnel config: {str(e)}")

    def save(self):
        """Save the profile data"""
        # Validate inputs
        if not self.name_var.get().strip():
            messagebox.showerror("Error", "Profile name is required.")
            return
            
        if not self.host_var.get().strip():
            messagebox.showerror("Error", "SSH host is required.")
            return
            
        if not self.username_var.get().strip():
            messagebox.showerror("Error", "Username is required.")
            return
            
        try:
            port = int(self.port_var.get())
            if port < 1 or port > 65535:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "SSH port must be a valid number between 1 and 65535.")
            return
            
        try:
            local_port = int(self.local_port_var.get())
            if local_port < 1 or local_port > 65535:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Local port must be a valid number between 1 and 65535.")
            return
            
        if self.auth_var.get() == "key" and not self.key_path_var.get().strip():
            messagebox.showerror("Error", "Key file path is required when using key authentication.")
            return
            
        # Create profile data
        self.result = {
            'name': self.name_var.get().strip(),
            'host': self.host_var.get().strip(),
            'port': port,
            'username': self.username_var.get().strip(),
            'local_port': local_port,
            'description': self.description_var.get("1.0", tk.END).strip()
        }
        
        if self.auth_var.get() == "key":
            self.result['key_path'] = self.key_path_var.get().strip()
        
        # Add obfs data based on selected protocol
        protocol = self.obfs_protocol_var.get()
        if protocol == "obfs4":
            self.result['obfs_protocol'] = 'obfs4'
            self.result['obfs_bridge'] = self.obfs_bridge_var.get().strip()
            self.result['obfs_cert'] = self.obfs_cert_var.get().strip()
        elif protocol == "stunnel":
            self.result['obfs_protocol'] = 'stunnel'
            self.result['stunnel_local_port'] = self.stunnel_local_port_var.get().strip()
            self.result['stunnel_remote'] = self.stunnel_remote_var.get().strip()
            self.result['stunnel_verify'] = self.stunnel_verify_var.get()
            self.result['stunnel_options'] = self.stunnel_options_var.get().strip()
        elif protocol == "shadowsocks":
            self.result['obfs_protocol'] = 'shadowsocks'
            self.result['ss_server'] = self.ss_server_var.get().strip()
            self.result['ss_port'] = self.ss_port_var.get().strip()
            self.result['ss_password'] = self.ss_password_var.get().strip()
            self.result['ss_method'] = self.ss_method_var.get().strip()
        elif protocol == "v2ray":
            self.result['obfs_protocol'] = 'v2ray'
            self.result['v2ray_server'] = self.v2ray_server_var.get().strip()
            self.result['v2ray_port'] = self.v2ray_port_var.get().strip()
            self.result['v2ray_uuid'] = self.v2ray_uuid_var.get().strip()
            self.result['v2ray_alter_id'] = self.v2ray_alter_id_var.get().strip()
            self.result['v2ray_security'] = self.v2ray_security_var.get().strip()
        
        self.dialog.destroy()
        
    def setup_scrollbar(self, frame):
        """Setup scrollbar for the dialog"""
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def check_scroll(event):
            if scrollable_frame.winfo_reqheight() > canvas.winfo_height():
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            else:
                scrollbar.pack_forget()
        
        canvas.bind("<Configure>", check_scroll)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
    def center_dialog(self):
        """Center the dialog on screen"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def browse_key(self):
        """Browse for SSH key file"""
        file_path = filedialog.askopenfilename(
            title="Select SSH Private Key",
            filetypes=[
                ("All Files", "*.*"),
                ("Private Key Files", "*.pem *.ppk *.key"),
                ("OpenSSH Private Key", "*.pem"),
                ("PuTTY Private Key", "*.ppk")
            ]
        )
        
        if file_path:
            self.key_path_var.set(file_path)
    
    # 此处已删除重复的save方法
    
    def cancel(self):
        """Cancel the dialog"""
        self.dialog.destroy()


import socket
import sys

def check_single_instance(port=18888):
    """检查是否已有实例运行"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", port))
        return True
    except socket.error:
        messagebox.showerror("错误", "程序已在运行中")
        return False

def main():
    # 检查是否已有实例运行
    if not check_single_instance():
        sys.exit(1)
        
    root = tk.Tk()
    app = SSHDynamicProxyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
