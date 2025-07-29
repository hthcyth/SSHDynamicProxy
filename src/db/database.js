const Database = require('better-sqlite3');
const path = require('path');

// 数据库路径
const dbPath = path.join(__dirname, '..', '..', 'packagesense.db');

// 创建数据库连接
const db = new Database(dbPath);

// 初始化数据库
function initDatabase() {
  // 创建安装包表
  db.exec(`
    CREATE TABLE IF NOT EXISTS packages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      path TEXT NOT NULL UNIQUE,
      size INTEGER NOT NULL,
      modified_time INTEGER NOT NULL,
      description TEXT,
      category TEXT,
      created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
    )
  `);

  // 创建分类表
  db.exec(`
    CREATE TABLE IF NOT EXISTS categories (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE,
      parent_id INTEGER
    )
  `);

  // 创建标签表
  db.exec(`
    CREATE TABLE IF NOT EXISTS tags (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE
    )
  `);

  // 创建安装包-标签关联表
  db.exec(`
    CREATE TABLE IF NOT EXISTS package_tags (
      package_id INTEGER,
      tag_id INTEGER,
      PRIMARY KEY (package_id, tag_id),
      FOREIGN KEY (package_id) REFERENCES packages(id),
      FOREIGN KEY (tag_id) REFERENCES tags(id)
    )
  `);

  // 插入预设分类
  const defaultCategories = ['办公软件', '设计工具', '开发工具', '娱乐软件', '系统工具'];
  const insertCategory = db.prepare('INSERT OR IGNORE INTO categories (name) VALUES (?)');
  defaultCategories.forEach(category => {
    insertCategory.run(category);
  });

  // 插入预设标签
  const defaultTags = ['常用', '绿色版', '免费', '开源', '试用版', '付费'];
  const insertTag = db.prepare('INSERT OR IGNORE INTO tags (name) VALUES (?)');
  defaultTags.forEach(tag => {
    insertTag.run(tag);
  });
}

// 保存安装包信息
function savePackage(pkg) {
  const insert = db.prepare(`
    INSERT OR REPLACE INTO packages (
      name, path, size, modified_time, description, category
    ) VALUES (?, ?, ?, ?, ?, ?)
  `);

  const result = insert.run(
    pkg.name,
    pkg.path,
    pkg.size,
    pkg.modifiedTime,
    pkg.description,
    pkg.category
  );

  // 保存标签
  if (pkg.tags && pkg.tags.length > 0) {
    // 先删除旧的标签关联
    const deleteTags = db.prepare('DELETE FROM package_tags WHERE package_id = ?');
    deleteTags.run(result.lastInsertRowid);

    // 插入新的标签关联
    const insertTag = db.prepare('INSERT or ignore into tags (name) values (?)');
    const getTagId = db.prepare('select id from tags where name = ?');
    const insertPackageTag = db.prepare('insert into package_tags (package_id, tag_id) values (?, ?)');

    pkg.tags.forEach(tag => {
      insertTag.run(tag);
      const tagId = getTagId.get(tag).id;
      insertPackageTag.run(result.lastInsertRowid, tagId);
    });
  }

  return result;
}

// 获取安装包信息
function getPackageByPath(path) {
  const get = db.prepare('SELECT * FROM packages WHERE path = ?');
  return get.get(path);
}

// 获取所有安装包
function getAllPackages() {
  const get = db.prepare('SELECT * FROM packages');
  return get.all();
}

// 搜索安装包
function searchPackages(query) {
  const search = db.prepare(`
    SELECT * FROM packages
    WHERE name LIKE ? OR description LIKE ? OR category LIKE ?
  `);
  return search.all(`%${query}%`, `%${query}%`, `%${query}%`);
}

// 导出函数
module.exports = {
  initDatabase,
  savePackage,
  getPackageByPath,
  getAllPackages,
  searchPackages
};

// 初始化数据库
initDatabase();