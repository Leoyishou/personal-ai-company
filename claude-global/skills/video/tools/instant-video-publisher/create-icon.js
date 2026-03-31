const canvas = require('canvas');
const fs = require('fs');

function createIcon(size) {
  const { createCanvas } = canvas;
  const c = createCanvas(size, size);
  const ctx = c.getContext('2d');
  
  // 背景
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, size, size);
  
  // 播放按钮
  ctx.fillStyle = '#fff';
  ctx.beginPath();
  const centerX = size / 2;
  const centerY = size / 2;
  const triangleSize = size * 0.35;
  ctx.moveTo(centerX - triangleSize * 0.3, centerY - triangleSize * 0.5);
  ctx.lineTo(centerX + triangleSize * 0.5, centerY);
  ctx.lineTo(centerX - triangleSize * 0.3, centerY + triangleSize * 0.5);
  ctx.closePath();
  ctx.fill();
  
  return c.toBuffer('image/png');
}

fs.writeFileSync('public/icon-192.png', createIcon(192));
fs.writeFileSync('public/icon-512.png', createIcon(512));
console.log('Icons created!');
