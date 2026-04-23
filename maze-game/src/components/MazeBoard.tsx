import React from 'react';
import { Cell, Position } from '../types';

interface MazeBoardProps {
  grid: Cell[][];
  playerPos: Position;
  goalPos: Position;
  cellSize: number;
}

const MazeBoard: React.FC<MazeBoardProps> = ({ grid, playerPos, goalPos, cellSize }) => {
  const wallColor = '#2196F3';
  const pathColor = '#FFFDE7';
  const playerColor = '#FF4081';
  const goalColor = '#69F0AE';

  return (
    <svg
      width={grid[0].length * cellSize}
      height={grid.length * cellSize}
      style={{ borderRadius: '16px', boxShadow: '0 8px 32px rgba(0,0,0,0.15)' }}
    >
      {grid.map((row, y) =>
        row.map((cell, x) => {
          const isPlayer = x === playerPos.x && y === playerPos.y;
          const isGoal = x === goalPos.x && y === goalPos.y;
          
          return (
            <g key={`${x}-${y}`}>
              <rect
                x={x * cellSize}
                y={y * cellSize}
                width={cellSize}
                height={cellSize}
                fill={pathColor}
              />
              
              {cell.walls.top && (
                <line
                  x1={x * cellSize}
                  y1={y * cellSize}
                  x2={(x + 1) * cellSize}
                  y2={y * cellSize}
                  stroke={wallColor}
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              )}
              {cell.walls.right && (
                <line
                  x1={(x + 1) * cellSize}
                  y1={y * cellSize}
                  x2={(x + 1) * cellSize}
                  y2={(y + 1) * cellSize}
                  stroke={wallColor}
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              )}
              {cell.walls.bottom && (
                <line
                  x1={x * cellSize}
                  y1={(y + 1) * cellSize}
                  x2={(x + 1) * cellSize}
                  y2={(y + 1) * cellSize}
                  stroke={wallColor}
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              )}
              {cell.walls.left && (
                <line
                  x1={x * cellSize}
                  y1={y * cellSize}
                  x2={x * cellSize}
                  y2={(y + 1) * cellSize}
                  stroke={wallColor}
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              )}
              
              {isGoal && (
                <g>
                  <circle
                    cx={x * cellSize + cellSize / 2}
                    cy={y * cellSize + cellSize / 2}
                    r={cellSize * 0.35}
                    fill={goalColor}
                    stroke="#00C853"
                    strokeWidth="3"
                  />
                  <text
                    x={x * cellSize + cellSize / 2}
                    y={y * cellSize + cellSize / 2 + 5}
                    textAnchor="middle"
                    fontSize={cellSize * 0.4}
                    fill="#00C853"
                  >
                    ⭐
                  </text>
                </g>
              )}
              
              {isPlayer && (
                <g>
                  <circle
                    cx={x * cellSize + cellSize / 2}
                    cy={y * cellSize + cellSize / 2}
                    r={cellSize * 0.35}
                    fill={playerColor}
                    stroke="#F50057"
                    strokeWidth="3"
                  />
                  <text
                    x={x * cellSize + cellSize / 2}
                    y={y * cellSize + cellSize / 2 + 5}
                    textAnchor="middle"
                    fontSize={cellSize * 0.4}
                    fill="white"
                  >
                    🐻
                  </text>
                </g>
              )}
            </g>
          );
        })
      )}
    </svg>
  );
};

export default MazeBoard;
