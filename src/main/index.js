const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

// 确保只有一个实例运行
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    // 当运行第二个实例时，聚焦到主窗口
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  // 创建主窗口
  let mainWindow;

  function createWindow() {
    mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        nodeIntegration: true,
        contextIsolation: false,
      },
      icon: path.join(__dirname, 'assets', 'icon.ico'),
      title: 'PackageSense - 安装包智能管理器'
    });

    mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));

    // 开发环境下打开开发者工具
    // mainWindow.webContents.openDevTools();

    mainWindow.on('closed', () => {
      mainWindow = null;
    });
  }

  app.on('ready', createWindow);

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });

  app.on('activate', () => {
    if (mainWindow === null) {
      createWindow();
    }
  });

  // 递归读取文件夹中的文件
  function readFilesRecursively(folderPath) {
    let files = [];
    try {
      const entries = fs.readdirSync(folderPath);
      entries.forEach(entry => {
        const entryPath = path.join(folderPath, entry);
        const stats = fs.statSync(entryPath);
        if (stats.isDirectory()) {
          // 递归读取子文件夹
          files = files.concat(readFilesRecursively(entryPath));
        } else {
          // 检查是否为安装包或压缩包
          const ext = path.extname(entry).toLowerCase();
          if ([ '.exe', '.msi', '.dmg', '.pkg', '.zip', '.rar', '.7z', '.tar', '.gz' ].includes(ext)) {
            files.push({
              name: entry,
              path: entryPath,
              size: stats.size,
              modifiedTime: stats.mtime
            });
          }
        }
      });
    } catch (error) {
      console.error('递归读取文件夹失败:', error);
    }
    return files;
  }

  // 监听打开文件夹对话框事件
  require('electron').ipcMain.on('open-folder-dialog', () => {
    dialog.showOpenDialog({
      properties: ['openDirectory'],
      filters: [
        { name: '所有文件夹', extensions: ['*'] }
      ]
    }).then(result => {
      if (!result.canceled && result.filePaths.length > 0) {
        const folderPath = result.filePaths[0];
        // 递归读取文件夹中的文件
        try {
          const files = readFilesRecursively(folderPath);
          // 发送文件夹选中事件给渲染进程
          mainWindow.webContents.send('folder-selected', folderPath, files);
        } catch (error) {
          console.error('读取文件夹失败:', error);
        }
      }
    }).catch(err => {
      console.error('打开文件夹对话框失败:', err);
    });
  });

  // 监听批量AI分析事件
  require('electron').ipcMain.on('batch-analyze-ai', (event, packages) => {
    // 这里我们将在主进程中处理批量AI分析
    // 实际实现会调用AI服务
    console.log('批量分析 packages:', packages);
    // 发送分析结果回渲染进程
    // event.reply('batch-analyze-result', results);
  });
}

// 注册应用程序菜单
require('./menu');