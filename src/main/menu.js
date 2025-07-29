const { app, Menu } = require('electron');

// 创建应用程序菜单
function createMenu() {
  const template = [
    {
      label: '文件',
      submenu: [
        {
          label: '选择文件夹',
          accelerator: 'Ctrl+O',
          click: () => {
            // 在这里实现选择文件夹的逻辑
            require('electron').ipcMain.emit('open-folder-dialog');
          }
        },
        {
          type: 'separator'
        },
        {
          label: '退出',
          accelerator: 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: '编辑',
      submenu: [
        {
          label: '撤销',
          accelerator: 'Ctrl+Z',
          role: 'undo'
        },
        {
          label: '重做',
          accelerator: 'Ctrl+Y',
          role: 'redo'
        },
        {
          type: 'separator'
        },
        {
          label: '剪切',
          accelerator: 'Ctrl+X',
          role: 'cut'
        },
        {
          label: '复制',
          accelerator: 'Ctrl+C',
          role: 'copy'
        },
        {
          label: '粘贴',
          accelerator: 'Ctrl+V',
          role: 'paste'
        },
        {
          label: '全选',
          accelerator: 'Ctrl+A',
          role: 'selectAll'
        }
      ]
    },
    {
      label: '视图',
      submenu: [
        {
          label: '刷新',
          accelerator: 'F5',
          click: () => {
            // 在这里实现刷新的逻辑
            require('electron').ipcMain.emit('refresh-view');
          }
        },
        {
          type: 'separator'
        },
        {
          label: '切换开发者工具',
          accelerator: 'Ctrl+Shift+I',
          click: (item, focusedWindow) => {
            if (focusedWindow) {
              focusedWindow.webContents.toggleDevTools();
            }
          }
        }
      ]
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '关于',
          click: () => {
            // 在这里实现关于对话框的逻辑
            require('electron').ipcMain.emit('open-about-dialog');
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

module.exports = createMenu();