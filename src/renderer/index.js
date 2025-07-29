const { ipcRenderer } = require('electron');
const path = require('path');

// DOM元素
const selectFolderBtn = document.getElementById('select-folder-btn');
const folderList = document.getElementById('folder-list');
const packagesTbody = document.getElementById('packages-tbody');
const packageInfo = document.getElementById('package-info');
const noSelection = document.getElementById('no-selection');
const detailName = document.getElementById('detail-name');
const detailPath = document.getElementById('detail-path');
const detailSize = document.getElementById('detail-size');
const detailModified = document.getElementById('detail-modified');
const detailDescription = document.getElementById('detail-description');
const detailCategory = document.getElementById('detail-category');
const tagsContainer = document.getElementById('tags-container');
const newTagInput = document.getElementById('new-tag-input');
const addTagBtn = document.getElementById('add-tag-btn');
const saveDetailsBtn = document.getElementById('save-details-btn');
const runPackageBtn = document.getElementById('run-package-btn');
const openFolderBtn = document.getElementById('open-folder-btn');
const analyzeAIBtn = document.getElementById('analyze-ai-btn');
const searchInput = document.querySelector('.search-box input');
const searchBtn = document.getElementById('search-btn');
const applyFilterBtn = document.getElementById('apply-filter-btn');
const batchAnalyzeAIBtn = document.getElementById('batch-analyze-ai-btn');

// 全局变量
let selectedPackage = null;
let packages = [];
let tags = [];
let categories = [];
let selectedPackages = [];

// 初始化
function init() {
  // 绑定事件
  bindEvents();

  // 加载分类和标签
  loadCategories();
  loadTags();
}

// 绑定事件
function bindEvents() {
  // 选择文件夹按钮
  selectFolderBtn.addEventListener('click', () => {
    ipcRenderer.send('open-folder-dialog');
  });

  // 保存详情按钮
  saveDetailsBtn.addEventListener('click', savePackageDetails);

  // 运行安装包按钮
  runPackageBtn.addEventListener('click', runPackage);

  // 打开文件夹按钮
  openFolderBtn.addEventListener('click', openPackageFolder);

  // AI分析按钮
  analyzeAIBtn.addEventListener('click', analyzePackageWithAI);

  // 批量AI分析按钮
  batchAnalyzeAIBtn.addEventListener('click', batchAnalyzeWithAI);

  // 添加标签按钮
  addTagBtn.addEventListener('click', addTag);

  // 搜索按钮
  searchBtn.addEventListener('click', searchPackages);

  // 按回车键搜索
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      searchPackages();
    }
  });

  // 应用筛选按钮
  applyFilterBtn.addEventListener('click', applyFilters);

  // 监听主进程事件
  ipcRenderer.on('folder-selected', (event, folderPath, files) => {
    // 清空文件夹列表
    folderList.innerHTML = '';

    // 添加选中的文件夹
    const folderItem = document.createElement('li');
    folderItem.textContent = folderPath;
    folderItem.dataset.path = folderPath;
    folderItem.classList.add('selected');
    folderList.appendChild(folderItem);

    // 显示文件
    packages = files;
    renderPackages(packages);
  });

  ipcRenderer.on('ai-analysis-result', (event, result) => {
    if (selectedPackage && selectedPackage.path === result.path) {
      detailDescription.value = result.description;
      
      // 选择推荐分类
      for (let i = 0; i < detailCategory.options.length; i++) {
        if (detailCategory.options[i].text === result.suggested_category) {
          detailCategory.selectedIndex = i;
          break;
        }
      }

      // 添加推荐标签
      result.suggested_tags.forEach(tag => {
        if (!tags.includes(tag)) {
          tags.push(tag);
          addTagToContainer(tag);
        }
      });

      // 保存更改
      savePackageDetails();
    }
  });

  // 监听批量AI分析结果
  ipcRenderer.on('batch-analyze-result', (event, results) => {
    // 处理批量分析结果
    results.forEach(result => {
      // 查找对应的安装包
      const pkg = packages.find(p => p.path === result.path);
      if (pkg) {
        pkg.description = result.description;
        pkg.category = result.suggested_category;
        pkg.tags = result.suggested_tags;
      }
    });

    // 重新渲染列表
    renderPackages(packages);

    // 显示成功消息
    alert('批量分析完成！');
  });
}

// 批量AI分析函数
function batchAnalyzeWithAI() {
  if (selectedPackages.length === 0) {
    alert('请先选择要分析的安装包！');
    return;
  }

  // 发送选中的安装包到主进程进行批量分析
  ipcRenderer.send('batch-analyze-ai', selectedPackages);

  // 显示加载提示
  alert('批量分析已开始，请稍候...');
}

// 渲染安装包列表
function renderPackages(packages) {
  packagesTbody.innerHTML = '';

  packages.forEach(pkg => {
    const row = document.createElement('tr');
    row.dataset.path = pkg.path;

    // 复选框
    const checkboxCell = document.createElement('td');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.addEventListener('change', (e) => {
      e.stopPropagation();
      if (checkbox.checked) {
        selectedPackages.push(pkg);
      } else {
        selectedPackages = selectedPackages.filter(p => p.path !== pkg.path);
      }
    });
    checkboxCell.appendChild(checkbox);
    row.appendChild(checkboxCell);

    // 名称
    const nameCell = document.createElement('td');
    nameCell.textContent = pkg.name;
    row.appendChild(nameCell);

    // 大小
    const sizeCell = document.createElement('td');
    sizeCell.textContent = formatSize(pkg.size);
    row.appendChild(sizeCell);

    // 修改时间
    const modifiedCell = document.createElement('td');
    modifiedCell.textContent = formatDate(pkg.modifiedTime);
    row.appendChild(modifiedCell);

    // 分类
    const categoryCell = document.createElement('td');
    categoryCell.textContent = pkg.category || '未分类';
    row.appendChild(categoryCell);

    // 标签
    const tagsCell = document.createElement('td');
    if (pkg.tags && pkg.tags.length > 0) {
      tagsCell.textContent = pkg.tags.join(', ');
    } else {
      tagsCell.textContent = '无';
    }
    row.appendChild(tagsCell);

    // 操作
    const actionCell = document.createElement('td');
    const analyzeBtn = document.createElement('button');
    analyzeBtn.textContent = 'AI分析';
    analyzeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      selectPackage(pkg);
      analyzePackageWithAI();
    });
    actionCell.appendChild(analyzeBtn);
    row.appendChild(actionCell);

    // 点击行选中安装包
    row.addEventListener('click', () => {
      selectPackage(pkg);
    });

    packagesTbody.appendChild(row);
  });
}

// 选择安装包
function selectPackage(pkg) {
  selectedPackage = pkg;

  // 显示详情
  packageInfo.classList.remove('hidden');
  noSelection.classList.add('hidden');

  // 填充详情
  detailName.textContent = pkg.name;
  detailPath.textContent = pkg.path;
  detailSize.textContent = formatSize(pkg.size);
  detailModified.textContent = formatDate(pkg.modifiedTime);
  detailDescription.value = pkg.description || '';

  // 清空标签容器
  tagsContainer.innerHTML = '';

  // 添加标签
  if (pkg.tags && pkg.tags.length > 0) {
    pkg.tags.forEach(tag => {
      addTagToContainer(tag);
    });
  }

  // 选择分类
  let categoryFound = false;
  for (let i = 0; i < detailCategory.options.length; i++) {
    if (detailCategory.options[i].text === pkg.category) {
      detailCategory.selectedIndex = i;
      categoryFound = true;
      break;
    }
  }

  if (!categoryFound) {
    detailCategory.selectedIndex = 0;
  }
}

// 保存安装包详情
function savePackageDetails() {
  if (!selectedPackage) return;

  // 更新选中的安装包
  selectedPackage.description = detailDescription.value;
  selectedPackage.category = detailCategory.options[detailCategory.selectedIndex].text;

  // 获取标签
  const tagElements = tagsContainer.querySelectorAll('.tag span');
  selectedPackage.tags = Array.from(tagElements).map(el => el.textContent);

  // 发送到主进程保存
  ipcRenderer.send('save-package-details', selectedPackage);

  // 更新列表
  renderPackages(packages);
}

// 运行安装包
function runPackage() {
  if (!selectedPackage) return;

  ipcRenderer.send('run-package', selectedPackage.path);
}

// 打开安装包所在文件夹
function openPackageFolder() {
  if (!selectedPackage) return;

  ipcRenderer.send('open-folder', path.dirname(selectedPackage.path));
}

// AI分析安装包
function analyzePackageWithAI() {
  if (!selectedPackage) return;

  // 显示加载状态
  analyzeAIBtn.textContent = '分析中...';
  analyzeAIBtn.disabled = true;

  // 发送到主进程进行AI分析
  ipcRenderer.send('analyze-package', selectedPackage);

  // 监听分析结果
  ipcRenderer.once('ai-analysis-result', (event, result) => {
    // 恢复按钮状态
    analyzeAIBtn.textContent = 'AI分析';
    analyzeAIBtn.disabled = false;

    if (selectedPackage && selectedPackage.path === result.path) {
      detailDescription.value = result.description;

      // 选择推荐分类
      let categoryFound = false;
      for (let i = 0; i < detailCategory.options.length; i++) {
        if (detailCategory.options[i].text === result.suggested_category) {
          detailCategory.selectedIndex = i;
          categoryFound = true;
          break;
        }
      }

      if (!categoryFound) {
        // 添加新分类
        const option = document.createElement('option');
        option.textContent = result.suggested_category;
        detailCategory.appendChild(option);
        detailCategory.selectedIndex = detailCategory.options.length - 1;

        // 更新分类列表
        categories.push(result.suggested_category);
      }

      // 添加推荐标签
      result.suggested_tags.forEach(tag => {
        if (!tags.includes(tag)) {
          tags.push(tag);
          addTagToContainer(tag);
        }
      });

      // 保存更改
      savePackageDetails();
    }
  });
}

// 添加标签
function addTag() {
  const tag = newTagInput.value.trim();
  if (tag && !tags.includes(tag)) {
    tags.push(tag);
    addTagToContainer(tag);
    newTagInput.value = '';
  }
}

// 添加标签到容器
function addTagToContainer(tag) {
  const tagElement = document.createElement('div');
  tagElement.classList.add('tag');

  const tagText = document.createElement('span');
  tagText.textContent = tag;
  tagElement.appendChild(tagText);

  const removeBtn = document.createElement('button');
  removeBtn.textContent = '×';
  removeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    tagElement.remove();
    tags = tags.filter(t => t !== tag);
  });
  tagElement.appendChild(removeBtn);

  tagsContainer.appendChild(tagElement);
}

// 搜索安装包
function searchPackages() {
  const query = searchInput.value.toLowerCase().trim();
  if (!query) {
    renderPackages(packages);
    return;
  }

  const filtered = packages.filter(pkg => {
    return (
      pkg.name.toLowerCase().includes(query) ||
      (pkg.description && pkg.description.toLowerCase().includes(query)) ||
      (pkg.category && pkg.category.toLowerCase().includes(query)) ||
      (pkg.tags && pkg.tags.some(tag => tag.toLowerCase().includes(query)))
    );
  });

  renderPackages(filtered);
}

// 应用筛选
function applyFilters() {
  // 这里实现筛选逻辑
  // 为简化示例，我们只是重新渲染列表
  renderPackages(packages);
}

// 加载分类
function loadCategories() {
  // 预设分类
  categories = ['未分类', '办公软件', '设计工具', '开发工具', '娱乐软件', '系统工具'];

  // 清空分类选择
  detailCategory.innerHTML = '';

  // 添加分类
  categories.forEach(category => {
    const option = document.createElement('option');
    option.textContent = category;
    detailCategory.appendChild(option);
  });
}

// 加载标签
function loadTags() {
  // 预设标签
  tags = ['常用', '绿色版', '免费', '开源', '试用版', '付费'];
}

// 格式化大小
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
  else if (bytes < 1073741824) return (bytes / 1048576).toFixed(2) + ' MB';
  else return (bytes / 1073741824).toFixed(2) + ' GB';
}

// 格式化日期
function formatDate(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

// 初始化应用
init();