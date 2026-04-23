import React, { useEffect, useRef, useCallback, useMemo } from 'react';
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
  const animationRef = useRef<number | undefined>(undefined);

  const rows = grid.length;
  const cols = grid[0]?.length || 0;
  const rawTotalWidth = cols * cellSize;
  const rawTotalHeight = rows * cellSize;

  const maxContainerSize = useMemo(() => {
    return Math.min(600, window.innerWidth - 80);
  }, []);

  const { scale, displayWidth, displayHeight } = useMemo(() => {
    const scaleX = maxContainerSize / rawTotalWidth;
    const scaleY = maxContainerSize / rawTotalHeight;
    
    const scale = Math.min(scaleX, scaleY, 1);
    
    return {
      scale,
      displayWidth: rawTotalWidth * scale,
      displayHeight: rawTotalHeight * scale,
    };
  }, [rawTotalWidth, rawTotalHeight, maxContainerSize]);

  const wallColor = '#2196F3';
  const pathColor = '#FFFDE7';
  const playerColor = '#FF4081';
  const goalColor = '#69F0AE';
  const wallWidth = Math.max(1, cellSize * 0.1);

  const drawMaze = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || grid.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const devicePixelRatio = window.devicePixelRatio || 1;
    const canvasWidth = Math.ceil(displayWidth);
    const canvasHeight = Math.ceil(displayHeight);

    canvas.width = canvasWidth * devicePixelRatio;
    canvas.height = canvasHeight * devicePixelRatio;
    canvas.style.width = `${canvasWidth}px`;
    canvas.style.height = `${canvasHeight}px`;

    ctx.scale(devicePixelRatio * scale, devicePixelRatio * scale);

    ctx.fillStyle = pathColor;
    ctx.fillRect(0, 0, rawTotalWidth, rawTotalHeight);

    ctx.strokeStyle = wallColor;
    ctx.lineWidth = wallWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    ctx.beginPath();

    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
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
  }, [grid, playerPos, goalPos, cellSize, rows, cols, wallWidth, scale, displayWidth, displayHeight, rawTotalWidth, rawTotalHeight]);

  useEffect(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    
    animationRef.current = requestAnimationFrame(() => {
      drawMaze();
    });

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [drawMaze]);

  useEffect(() => {
    const handleResize = () => {
      drawMaze();
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [drawMaze]);

  return (
    <div
      ref={containerRef}
      style={{
        width: Math.ceil(displayWidth),
        height: Math.ceil(displayHeight),
        borderRadius: '16px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
        position: 'relative',
        background: '#FFFDE7',
        overflow: 'hidden',
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          display: 'block',
          imageRendering: 'auto',
        }}
      />
      {scale < 1 && (
        <div
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            background: 'rgba(0,0,0,0.6)',
            color: 'white',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 'bold',
          }}
        >
          {Math.round(scale * 100)}%
        </div>
      )}
    </div>
  );
};

export default MazeBoard;
