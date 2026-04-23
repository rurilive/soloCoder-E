import { Cell, Position, MazeConfig } from '../types';

export class MazeGenerator {
  private rows: number;
  private cols: number;
  private grid: Cell[][];

  constructor(config: MazeConfig) {
    this.rows = config.rows;
    this.cols = config.cols;
    this.grid = this.initializeGrid();
  }

  private initializeGrid(): Cell[][] {
    const grid: Cell[][] = [];
    for (let y = 0; y < this.rows; y++) {
      const row: Cell[] = [];
      for (let x = 0; x < this.cols; x++) {
        row.push({
          x,
          y,
          walls: { top: true, right: true, bottom: true, left: true },
          visited: false,
        });
      }
      grid.push(row);
    }
    return grid;
  }

  private getNeighbors(cell: Cell): Cell[] {
    const neighbors: Cell[] = [];
    const { x, y } = cell;

    if (y > 0) neighbors.push(this.grid[y - 1][x]);
    if (x < this.cols - 1) neighbors.push(this.grid[y][x + 1]);
    if (y < this.rows - 1) neighbors.push(this.grid[y + 1][x]);
    if (x > 0) neighbors.push(this.grid[y][x - 1]);

    return neighbors.filter(n => !n.visited);
  }

  private removeWalls(current: Cell, next: Cell): void {
    const dx = next.x - current.x;
    const dy = next.y - current.y;

    if (dx === 1) {
      current.walls.right = false;
      next.walls.left = false;
    } else if (dx === -1) {
      current.walls.left = false;
      next.walls.right = false;
    } else if (dy === 1) {
      current.walls.bottom = false;
      next.walls.top = false;
    } else if (dy === -1) {
      current.walls.top = false;
      next.walls.bottom = false;
    }
  }

  generate(): Cell[][] {
    const stack: Cell[] = [];
    const startCell = this.grid[0][0];
    startCell.visited = true;
    stack.push(startCell);

    while (stack.length > 0) {
      const current = stack[stack.length - 1];
      const neighbors = this.getNeighbors(current);

      if (neighbors.length > 0) {
        const next = neighbors[Math.floor(Math.random() * neighbors.length)];
        next.visited = true;
        this.removeWalls(current, next);
        stack.push(next);
      } else {
        stack.pop();
      }
    }

    return this.grid;
  }

  canMove(from: Position, to: Position, grid: Cell[][]): boolean {
    const fromCell = grid[from.y]?.[from.x];
    const toCell = grid[to.y]?.[to.x];

    if (!fromCell || !toCell) return false;

    const dx = to.x - from.x;
    const dy = to.y - from.y;

    if (Math.abs(dx) + Math.abs(dy) !== 1) return false;

    if (dx === 1) return !fromCell.walls.right;
    if (dx === -1) return !fromCell.walls.left;
    if (dy === 1) return !fromCell.walls.bottom;
    if (dy === -1) return !fromCell.walls.top;

    return false;
  }
}
