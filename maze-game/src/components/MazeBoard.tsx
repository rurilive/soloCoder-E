import React, { useEffect, useRef, useCallback } from 'react';
import { Cell, Position } from '../types';

interface MazeBoardProps {
  grid: Cell[][];
  playerPos: Position;
  goalPos: Position;
  cellSize: number;
}

const MazeBoard: React.FC<MazeBoardProps> = ({ grid, playerPos, goalPos, cellSize }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef({
    offsetX: 0,
    offsetY: 0,
    width: 0,
    height: 0,
  });

  const rows = grid.length;
  const cols = grid[0]?.length || 0;
  const totalWidth = cols * cellSize;
  const totalHeight = rows * cellSize;

  const wallColor = '#2196F3';
  const pathColor = '#FFFDE7';
  const playerColor = '#FF4081';
  const goalColor = '#69F0AE';
  const wallWidth = Math.max(2, cellSize * 0.1);

  const drawMaze = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || grid.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const viewport = viewportRef.current;

    const startCol = Math.max(0, Math.floor(viewport.offsetX / cellSize) - 2);
    const endCol = Math.min(cols, Math.ceil((viewport.offsetX + viewport.width) / cellSize) + 2);
    const startRow = Math.max(0, Math.floor(viewport.offsetY / cellSize) - 2);
    const endRow = Math.min(rows, Math.ceil((viewport.offsetY + viewport.height) / cellSize) + 2);

    ctx.fillStyle = pathColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = wallColor;
    ctx.lineWidth = wallWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    ctx.beginPath();

    for (let y = startRow; y < endRow; y++) {
      for (let x = startCol; x < endCol; x++) {
        const cell = grid[y]?.[x];
        if (!cell) continue;

        const left = x * cellSize;
        const top = y * cellSize;
        const right = left + cellSize;
        const bottom = top + cellSize;

        if (cell.walls.top) {
          ctx.moveTo(left, top);
          ctx.lineTo(right, top);
        }
        if (cell.walls.right) {
          ctx.moveTo(right, top);
          ctx.lineTo(right, bottom);
        }
        if (cell.walls.bottom) {
          ctx.moveTo(left, bottom);
          ctx.lineTo(right, bottom);
        }
        if (cell.walls.left) {
          ctx.moveTo(left, top);
          ctx.lineTo(left, bottom);
        }
      }
    }

    ctx.stroke();

    const goalX = goalPos.x * cellSize + cellSize / 2;
    const goalY = goalPos.y * cellSize + cellSize / 2;
    const goalRadius = cellSize * 0.35;

    ctx.fillStyle = goalColor;
    ctx.beginPath();
    ctx.arc(goalX, goalY, goalRadius, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = '#00C853';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(goalX, goalY, goalRadius, 0, Math.PI * 2);
    ctx.stroke();

    ctx.font = `${cellSize * 0.5}px Arial`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#00C853';
    ctx.fillText('⭐', goalX, goalY);

    const playerX = playerPos.x * cellSize + cellSize / 2;
    const playerY = playerPos.y * cellSize + cellSize / 2;
    const playerRadius = cellSize * 0.35;

    ctx.fillStyle = playerColor;
    ctx.beginPath();
    ctx.arc(playerX, playerY, playerRadius, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = '#F50057';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(playerX, playerY, playerRadius, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = 'white';
    ctx.fillText('🐻', playerX, playerY);
  }, [grid, playerPos, goalPos, cellSize, rows, cols, wallWidth]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const updateViewport = () => {
      viewportRef.current = {
        offsetX: container.scrollLeft,
        offsetY: container.scrollTop,
        width: container.clientWidth,
        height: container.clientHeight,
      };
      drawMaze();
    };

    updateViewport();
    container.addEventListener('scroll', updateViewport);
    window.addEventListener('resize', updateViewport);

    return () => {
      container.removeEventListener('scroll', updateViewport);
      window.removeEventListener('resize', updateViewport);
    };
  }, [drawMaze]);

  useEffect(() => {
    drawMaze();
  }, [drawMaze]);

  const maxContainerSize = Math.min(600, window.innerWidth - 80);
  const containerWidth = Math.min(maxContainerSize, totalWidth);
  const containerHeight = Math.min(maxContainerSize, totalHeight);

  const needsScroll = totalWidth > containerWidth || totalHeight > containerHeight;

  return (
    <div
      ref={containerRef}
      style={{
        width: containerWidth,
        height: containerHeight,
        overflow: needsScroll ? 'auto' : 'visible',
        borderRadius: '16px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
        position: 'relative',
        background: '#FFFDE7',
      }}
    >
      <canvas
        ref={canvasRef}
        width={totalWidth}
        height={totalHeight}
        style={{
          display: 'block',
          imageRendering: 'auto',
        }}
      />
    </div>
  );
};

export default MazeBoard;
