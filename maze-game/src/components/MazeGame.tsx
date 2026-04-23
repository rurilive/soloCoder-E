import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Cell, Position, Difficulty, DIFFICULTY_CONFIG, CUSTOM_SIZE_CONFIG, CustomSize } from '../types';
import { MazeGenerator } from '../utils/mazeGenerator';
import MazeBoard from './MazeBoard';
import ControlButtons from './ControlButtons';
import DifficultySelector from './DifficultySelector';

const MazeGame: React.FC = () => {
  const [difficulty, setDifficulty] = useState<Difficulty>('easy');
  const [customSize, setCustomSize] = useState<CustomSize>({
    rows: CUSTOM_SIZE_CONFIG.default,
    cols: CUSTOM_SIZE_CONFIG.default,
  });
  const [grid, setGrid] = useState<Cell[][]>([]);
  const [playerPos, setPlayerPos] = useState<Position>({ x: 0, y: 0 });
  const [goalPos, setGoalPos] = useState<Position>({ x: 0, y: 0 });
  const [isWon, setIsWon] = useState(false);
  const [moveCount, setMoveCount] = useState(0);
  const [showCelebration, setShowCelebration] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const mazeConfig = useMemo(() => {
    if (difficulty === 'custom') {
      return {
        rows: customSize.rows,
        cols: customSize.cols,
        label: `自定义 (${customSize.rows}×${customSize.cols})`,
        color: DIFFICULTY_CONFIG.custom.color,
      };
    }
    return DIFFICULTY_CONFIG[difficulty];
  }, [difficulty, customSize]);

  const totalCells = mazeConfig.rows * mazeConfig.cols;
  const isLargeMaze = totalCells > 500;
  const isHugeMaze = totalCells > 5000;

  const cellSize = useMemo(() => {
    if (isHugeMaze) {
      return Math.max(10, 15);
    }
    if (isLargeMaze) {
      return Math.max(15, 20);
    }
    const maxWidth = Math.min(600, window.innerWidth - 80);
    return Math.min(35, Math.floor(maxWidth / mazeConfig.cols));
  }, [mazeConfig.cols, isLargeMaze, isHugeMaze]);

  const generateMazeAsync = useCallback(() => {
    return new Promise<Cell[][]>((resolve) => {
      const generator = new MazeGenerator({
        rows: mazeConfig.rows,
        cols: mazeConfig.cols,
        difficulty,
      });

      if (isHugeMaze) {
        requestIdleCallback(() => {
          const result = generator.generate();
          resolve(result);
        });
      } else {
        const result = generator.generate();
        resolve(result);
      }
    });
  }, [difficulty, mazeConfig, isHugeMaze]);

  const initGame = useCallback(async () => {
    setIsGenerating(true);
    
    try {
      const newGrid = await generateMazeAsync();
      setGrid(newGrid);
      setPlayerPos({ x: 0, y: 0 });
      setGoalPos({ x: mazeConfig.cols - 1, y: mazeConfig.rows - 1 });
      setIsWon(false);
      setMoveCount(0);
      setShowCelebration(false);
    } finally {
      setIsGenerating(false);
    }
  }, [generateMazeAsync, mazeConfig]);

  useEffect(() => {
    initGame();
  }, [initGame]);

  const handleMove = useCallback((direction: 'up' | 'down' | 'left' | 'right') => {
    if (isWon || grid.length === 0) return;

    let newPos = { ...playerPos };
    
    switch (direction) {
      case 'up':
        newPos.y -= 1;
        break;
      case 'down':
        newPos.y += 1;
        break;
      case 'left':
        newPos.x -= 1;
        break;
      case 'right':
        newPos.x += 1;
        break;
    }

    const fromCell = grid[playerPos.y]?.[playerPos.x];
    if (!fromCell) return;

    let canMove = false;
    const dx = newPos.x - playerPos.x;
    const dy = newPos.y - playerPos.y;

    if (dx === 1) canMove = !fromCell.walls.right;
    else if (dx === -1) canMove = !fromCell.walls.left;
    else if (dy === 1) canMove = !fromCell.walls.bottom;
    else if (dy === -1) canMove = !fromCell.walls.top;

    if (canMove) {
      setPlayerPos(newPos);
      setMoveCount(prev => prev + 1);

      if (newPos.x === goalPos.x && newPos.y === goalPos.y) {
        setIsWon(true);
        setShowCelebration(true);
      }
    }
  }, [isWon, grid, playerPos, goalPos]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowUp':
        case 'w':
        case 'W':
          e.preventDefault();
          handleMove('up');
          break;
        case 'ArrowDown':
        case 's':
        case 'S':
          e.preventDefault();
          handleMove('down');
          break;
        case 'ArrowLeft':
        case 'a':
        case 'A':
          e.preventDefault();
          handleMove('left');
          break;
        case 'ArrowRight':
        case 'd':
        case 'D':
          e.preventDefault();
          handleMove('right');
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleMove]);

  const handleDifficultyChange = (newDifficulty: Difficulty) => {
    setDifficulty(newDifficulty);
  };

  const handleCustomSizeChange = (size: CustomSize) => {
    setCustomSize(size);
  };

  const celebrationEmojis = ['🎉', '🎊', '🌟', '✨', '🎈', '🏆', '💖', '🌈'];

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '20px',
      fontFamily: "'Comic Sans MS', 'Chalkboard SE', cursive, sans-serif",
      position: 'relative',
      overflow: 'hidden',
    }}>
      {showCelebration && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: 'none',
          zIndex: 100,
        }}>
          {Array.from({ length: 20 }).map((_, i) => (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                fontSize: `${24 + Math.random() * 24}px`,
                animation: `float ${2 + Math.random() * 2}s ease-in-out infinite`,
                animationDelay: `${Math.random() * 2}s`,
              }}
            >
              {celebrationEmojis[Math.floor(Math.random() * celebrationEmojis.length)]}
            </div>
          ))}
        </div>
      )}

      <div style={{
        textAlign: 'center',
        marginBottom: '20px',
        animation: 'bounce 2s infinite',
      }}>
        <h1 style={{
          fontSize: '48px',
          color: 'white',
          textShadow: '3px 3px 6px rgba(0,0,0,0.3)',
          margin: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px',
        }}>
          🧸 迷宫大冒险 🏰
        </h1>
        <p style={{
          fontSize: '20px',
          color: 'rgba(255,255,255,0.9)',
          margin: '8px 0 0 0',
        }}>
          帮助小熊找到星星吧！
        </p>
        {isHugeMaze && (
          <p style={{
            fontSize: '14px',
            color: 'rgba(255,255,255,0.8)',
            margin: '4px 0 0 0',
            fontStyle: 'italic',
          }}>
            ⚡ 超级迷宫模式: {totalCells.toLocaleString()} 个格子
          </p>
        )}
      </div>

      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '24px',
        maxWidth: '100%',
      }}>
        <DifficultySelector 
          currentDifficulty={difficulty}
          customSize={customSize}
          onSelect={handleDifficultyChange}
          onCustomSizeChange={handleCustomSizeChange}
          disabled={isWon || isGenerating}
        />

        <div style={{
          display: 'flex',
          gap: '12px',
          justifyContent: 'center',
          flexWrap: 'wrap',
        }}>
          <div style={{
            background: 'rgba(255,255,255,0.95)',
            padding: '16px 28px',
            borderRadius: '16px',
            boxShadow: '0 6px 20px rgba(0,0,0,0.15)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '20px',
            fontWeight: 'bold',
            color: '#333',
          }}>
            <span>📍</span>
            <span>步数: {moveCount}</span>
          </div>
          
          <div style={{
            background: 'rgba(255,255,255,0.95)',
            padding: '16px 28px',
            borderRadius: '16px',
            boxShadow: '0 6px 20px rgba(0,0,0,0.15)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '20px',
            fontWeight: 'bold',
            color: '#333',
          }}>
            <span>🎯</span>
            <span>难度: {mazeConfig.label}</span>
          </div>
        </div>

        {isGenerating ? (
          <div style={{
            padding: '60px 80px',
            background: 'rgba(255,255,255,0.95)',
            borderRadius: '24px',
            boxShadow: '0 12px 40px rgba(0,0,0,0.2)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '16px',
          }}>
            <div style={{
              fontSize: '48px',
              animation: 'spin 1s linear infinite',
            }}>
              🔄
            </div>
            <div style={{
              fontSize: '24px',
              fontWeight: 'bold',
              color: '#9C27B0',
            }}>
              正在生成迷宫...
            </div>
            {isHugeMaze && (
              <div style={{
                fontSize: '14px',
                color: '#666',
              }}>
                超大迷宫需要一点时间，请耐心等待 ⏳
              </div>
            )}
          </div>
        ) : grid.length > 0 && (
          <div style={{
            padding: '20px',
            background: 'rgba(255,255,255,0.95)',
            borderRadius: '24px',
            boxShadow: '0 12px 40px rgba(0,0,0,0.2)',
          }}>
            <MazeBoard
              grid={grid}
              playerPos={playerPos}
              goalPos={goalPos}
              cellSize={cellSize}
            />
          </div>
        )}

        {!isWon && !isGenerating && (
          <ControlButtons 
            onMove={handleMove} 
            disabled={isWon || isGenerating}
          />
        )}

        <button
          onClick={initGame}
          disabled={isGenerating}
          style={{
            padding: '18px 48px',
            fontSize: '22px',
            fontWeight: 'bold',
            color: 'white',
            background: isGenerating 
              ? '#999' 
              : 'linear-gradient(135deg, #FF6B6B, #FF8E53)',
            border: 'none',
            borderRadius: '50px',
            cursor: isGenerating ? 'not-allowed' : 'pointer',
            boxShadow: isGenerating 
              ? 'none' 
              : '0 8px 24px rgba(255,107,107,0.4)',
            transition: 'all 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            opacity: isGenerating ? 0.6 : 1,
          }}
          onMouseEnter={(e) => {
            if (!isGenerating) {
              e.currentTarget.style.transform = 'scale(1.05)';
              e.currentTarget.style.boxShadow = '0 12px 32px rgba(255,107,107,0.5)';
            }
          }}
          onMouseLeave={(e) => {
            if (!isGenerating) {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.boxShadow = '0 8px 24px rgba(255,107,107,0.4)';
            }
          }}
        >
          {isGenerating ? '⏳ 生成中...' : '🔄 重新开始'}
        </button>

        {isWon && showCelebration && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 200,
          }}>
            <div style={{
              background: 'linear-gradient(135deg, #FFFDE7, #FFF9C4)',
              padding: '40px 60px',
              borderRadius: '32px',
              textAlign: 'center',
              boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
              animation: 'popIn 0.5s ease-out',
              maxWidth: '90%',
            }}>
              <div style={{ fontSize: '80px', marginBottom: '20px' }}>
                🎉🏆🎊
              </div>
              <h2 style={{
                fontSize: '36px',
                color: '#FF6B6B',
                margin: '0 0 16px 0',
                textShadow: '2px 2px 4px rgba(0,0,0,0.1)',
              }}>
                太棒了！
              </h2>
              <p style={{
                fontSize: '24px',
                color: '#666',
                margin: '0 0 8px 0',
              }}>
                你成功帮助小熊找到了星星！
              </p>
              <p style={{
                fontSize: '20px',
                color: '#888',
                margin: '0 0 28px 0',
              }}>
                总共走了 <span style={{ color: '#FF6B6B', fontWeight: 'bold', fontSize: '28px' }}>{moveCount}</span> 步
              </p>
              <button
                onClick={() => {
                  setShowCelebration(false);
                  initGame();
                }}
                style={{
                  padding: '16px 40px',
                  fontSize: '22px',
                  fontWeight: 'bold',
                  color: 'white',
                  background: 'linear-gradient(135deg, #4CAF50, #8BC34A)',
                  border: 'none',
                  borderRadius: '50px',
                  cursor: 'pointer',
                  boxShadow: '0 6px 20px rgba(76,175,80,0.4)',
                  transition: 'all 0.3s ease',
                }}
              >
                🎮 再玩一次
              </button>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
        
        @keyframes float {
          0%, 100% { 
            transform: translateY(0) rotate(0deg);
            opacity: 1;
          }
          50% { 
            transform: translateY(-30px) rotate(180deg);
            opacity: 0.8;
          }
        }
        
        @keyframes popIn {
          0% {
            transform: scale(0.5);
            opacity: 0;
          }
          70% {
            transform: scale(1.1);
          }
          100% {
            transform: scale(1);
            opacity: 1;
          }
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default MazeGame;
