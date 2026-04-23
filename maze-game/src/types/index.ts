export type Difficulty = 'easy' | 'medium' | 'hard';

export type Cell = {
  x: number;
  y: number;
  walls: {
    top: boolean;
    right: boolean;
    bottom: boolean;
    left: boolean;
  };
  visited: boolean;
};

export type Position = {
  x: number;
  y: number;
};

export type MazeConfig = {
  rows: number;
  cols: number;
  difficulty: Difficulty;
};

export const DIFFICULTY_CONFIG: Record<Difficulty, { rows: number; cols: number; label: string; color: string }> = {
  easy: { rows: 5, cols: 5, label: '简单', color: '#4CAF50' },
  medium: { rows: 7, cols: 7, label: '中等', color: '#FF9800' },
  hard: { rows: 10, cols: 10, label: '困难', color: '#F44336' },
};
