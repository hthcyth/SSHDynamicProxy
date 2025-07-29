const axios = require('axios');
const fs = require('fs');
const path = require('path');

// 配置文件路径
const configPath = path.join(__dirname, '..', '..', 'config.json');

// 读取配置
function readConfig() {
  try {
    if (fs.existsSync(configPath)) {
      const data = fs.readFileSync(configPath, 'utf8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error('读取配置文件失败:', error);
  }
  return { apiKey: '', provider: 'openai', apiSecret: '', appId: '' };
}

// 保存配置
function saveConfig(config) {
  try {
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf8');
    return true;
  } catch (error) {
    console.error('保存配置文件失败:', error);
    return false;
  }
}

// 分析安装包
async function analyzePackage(pkg) {
  const config = readConfig();

  if (!config.apiKey) {
    throw new Error('未配置API密钥');
  }

  // 设置API URL和请求参数
  let apiUrl;
  let headers = {};
  let data = {};

  // 构造提示
  const prompt = `请分析安装包信息并返回JSON：\n信息：文件名=${pkg.name}\n路径：${pkg.path}\n大小：${pkg.size}字节\n修改时间：${pkg.modifiedTime}\n\n请返回以下格式的JSON：\n{\n  "description": "安装包描述",\n  "suggested_category": "推荐分类",\n  "suggested_tags": ["标签1", "标签2"]\n}`;

  // 根据提供商设置API参数
  if (config.provider === 'openai') {
    apiUrl = 'https://api.openai.com/v1/chat/completions';
    headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${config.apiKey}`
    };
    data = {
      model: 'gpt-3.5-turbo',
      messages: [{
        role: 'user',
        content: prompt
      }],
      max_tokens: 500
    };
  } else if (config.provider === 'baidu') {
    apiUrl = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions';
    // 百度API需要在URL中添加access_token
    apiUrl = `${apiUrl}?access_token=${config.apiKey}`;
    headers = {
      'Content-Type': 'application/json'
    };
    data = {
      messages: [{
        role: 'user',
        content: prompt
      }],
      temperature: 0.7
    };
  } else if (config.provider === 'aliyun') {
    apiUrl = 'https://chatapi.aliyun.com/v1/chat/completions';
    headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${config.apiKey}`
    };
    data = {
      model: 'qwen-turbo',
      messages: [{
        role: 'user',
        content: prompt
      }],
      max_tokens: 500
    };
  } else if (config.provider === 'tencent') {
    apiUrl = 'https://api.ai.tencent.com/v1/chat/completions';
    headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${config.apiKey}`,
      'X-TC-AppId': config.appId
    };
    data = {
      model: 'hunyuan-pro',
      messages: [{
        role: 'user',
        content: prompt
      }],
      max_tokens: 500
    };
  } else {
    throw new Error(`不支持的API提供商: ${config.provider}`);
  }

  try {
    // 发送API请求
    const response = await axios.post(apiUrl, data, { headers });

    // 解析响应
    let result;
    if (config.provider === 'openai') {
      result = JSON.parse(response.data.choices[0].message.content);
    } else if (config.provider === 'baidu') {
      result = JSON.parse(response.data.result);
    } else if (config.provider === 'aliyun') {
      result = JSON.parse(response.data.choices[0].message.content);
    } else if (config.provider === 'tencent') {
      result = JSON.parse(response.data.choices[0].message.content);
    }

    // 添加安装包路径
    result.path = pkg.path;

    return result;
  } catch (error) {
    console.error('分析安装包失败:', error);
    throw new Error(`分析安装包失败: ${error.message}`);
  }
}

// 批量分析安装包
async function batchAnalyzePackages(pkgs) {
  const results = [];
  for (const pkg of pkgs) {
    try {
      const result = await analyzePackage(pkg);
      results.push(result);
    } catch (error) {
      console.error(`分析安装包 ${pkg.name} 失败:`, error);
      // 继续分析其他安装包
    }
  }
  return results;
}