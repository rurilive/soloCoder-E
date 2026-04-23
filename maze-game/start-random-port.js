const { exec } = require('child_process');
const net = require('net');

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.on('error', reject);
    server.listen(0, () => {
      const port = server.address().port;
      server.close(() => {
        resolve(port);
      });
    });
  });
}

async function startServer() {
  try {
    const port = await findFreePort();
    console.log(`🎯 随机分配端口: ${port}`);
    console.log(`🚀 启动迷宫游戏服务器...`);
    console.log(`🌐 访问地址: http://localhost:${port}`);
    console.log('');
    
    const env = { ...process.env, PORT: port.toString() };
    
    const child = exec('npm start', { env });
    
    child.stdout.pipe(process.stdout);
    child.stderr.pipe(process.stderr);
    
    child.on('exit', (code) => {
      console.log(`服务器退出，代码: ${code}`);
    });
    
    child.on('error', (err) => {
      console.error('启动服务器时出错:', err);
    });
    
  } catch (error) {
    console.error('查找可用端口时出错:', error);
    process.exit(1);
  }
}

startServer();
