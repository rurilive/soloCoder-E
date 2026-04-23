import { Cell, Position, MazeConfig } from '../types';

type SimpleCell = {
  x: number;
  y: number;
  walls: { top: boolean; right: boolean; bottom: boolean; left: boolean };
};

type FastGrid = SimpleCell[][];

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
    const grid: Cell[][] = new Array(this.rows);
    for (let y = 0; y < this.rows; y++) {
      grid[y] = new Array(this.cols);
      for (let x = 0; x < this.cols; x++) {
        grid[y][x] = {
          x,
          y,
          walls: { top: true, right: true, bottom: true, left: true },
          visited: false,
        };
      }
    }
    return grid;
  }

  private getNeighborsFast(
    cell: Cell,
    visitedStatus: boolean,
    dirOrder: number[]
  ): Cell[] {
    const neighbors: Cell[] = [];
    const { x, y } = cell;
    const dirs = [
      { dx: 0, dy: -1 },
      { dx: 1, dy: 0 },
      { dx: 0, dy: 1 },
      { dx: -1, dy: 0 },
    ];

    for (const dirIdx of dirOrder) {
      const dir = dirs[dirIdx];
      const nx = x + dir.dx;
      const ny = y + dir.dy;
      if (nx >= 0 && nx < this.cols && ny >= 0 && ny < this.rows) {
        const neighbor = this.grid[ny][nx];
        if (neighbor.visited === visitedStatus) {
          neighbors.push(neighbor);
        }
      }
    }
    return neighbors;
  }

  private getRandomDirOrder(): number[] {
    const order = [0, 1, 2, 3];
    for (let i = order.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [order[i], order[j]] = [order[j], order[i]];
    }
    return order;
  }

  private removeWallsFast(current: Cell, next: Cell): void {
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

  private generatePrimFast(): void {
    const startCell = this.grid[0][0];
    startCell.visited = true;

    const frontier: Cell[] = [];
    const frontierSet = new Set<string>();

    const addToFrontier = (cell: Cell) => {
      const key = `${cell.x},${cell.y}`;
      if (!frontierSet.has(key)) {
        frontierSet.add(key);
        frontier.push(cell);
      }
    };

    const initialDirs = this.getRandomDirOrder();
    const initialNeighbors = this.getNeighborsFast(startCell, false, initialDirs);
    for (const n of initialNeighbors) {
      addToFrontier(n);
    }

    while (frontier.length > 0) {
      const randomIndex = Math.floor(Math.random() * frontier.length);
      const current = frontier[randomIndex];
      
      frontier[randomIndex] = frontier[frontier.length - 1];
      frontier.pop();
      frontierSet.delete(`${current.x},${current.y}`);

      if (current.visited) continue;

      current.visited = true;

      const dirs = this.getRandomDirOrder();
      const visitedNeighbors = this.getNeighborsFast(current, true, dirs);
      
      if (visitedNeighbors.length > 0) {
        const neighbor = visitedNeighbors[Math.floor(Math.random() * visitedNeighbors.length)];
        this.removeWallsFast(current, neighbor);
      }

      const newDirs = this.getRandomDirOrder();
      const newFrontier = this.getNeighborsFast(current, false, newDirs);
      for (const cell of newFrontier) {
        addToFrontier(cell);
      }
    }
  }

  private generateBranchFactorFast(): void {
    const stack: Cell[] = [];
    const startCell = this.grid[0][0];
    startCell.visited = true;
    stack.push(startCell);

    while (stack.length > 0) {
      const randomIndex = Math.floor(Math.random() * stack.length);
      const current = stack[randomIndex];
      
      const dirs = this.getRandomDirOrder();
      const neighbors = this.getNeighborsFast(current, false, dirs);

      if (neighbors.length > 0) {
        const numBranches = Math.min(
          neighbors.length,
          Math.floor(Math.random() * 3) + 1
        );

        for (let i = 0; i < numBranches && neighbors.length > 0; i++) {
          const nextIndex = Math.floor(Math.random() * neighbors.length);
          const next = neighbors[nextIndex];
          
          neighbors[nextIndex] = neighbors[neighbors.length - 1];
          neighbors.pop();

          next.visited = true;
          this.removeWallsFast(current, next);
          stack.push(next);
        }
      } else {
        stack[randomIndex] = stack[stack.length - 1];
        stack.pop();
      }
    }
  }

  private addExtraBranchesFast(): void {
    const totalCells = this.rows * this.cols;
    const numExtraPaths = Math.floor(totalCells * 0.06);

    for (let i = 0; i < numExtraPaths; i++) {
      const x = Math.floor(Math.random() * this.cols);
      const y = Math.floor(Math.random() * this.rows);
      const cell = this.grid[y][x];

      const dirs = this.getRandomDirOrder();
      const directions = [
        { dx: 0, dy: -1, wall: 'top' as const, opposite: 'bottom' as const },
        { dx: 1, dy: 0, wall: 'right' as const, opposite: 'left' as const },
        { dx: 0, dy: 1, wall: 'bottom' as const, opposite: 'top' as const },
        { dx: -1, dy: 0, wall: 'left' as const, opposite: 'right' as const },
      ];

      for (const dirIdx of dirs) {
        const dir = directions[dirIdx];
        const nx = x + dir.dx;
        const ny = y + dir.dy;
        
        if (nx >= 0 && nx < this.cols && ny >= 0 && ny < this.rows) {
          const neighbor = this.grid[ny][nx];
          if (cell.walls[dir.wall]) {
            cell.walls[dir.wall] = false;
            neighbor.walls[dir.opposite] = false;
            break;
          }
        }
      }
    }
  }

  private addCyclePathsFast(): void {
    const numCycles = Math.floor(Math.random() * 4) + 3;

    for (let i = 0; i < numCycles; i++) {
      const startX = Math.floor(Math.random() * Math.max(1, this.cols - 4)) + 1;
      const startY = Math.floor(Math.random() * Math.max(1, this.rows - 4)) + 1;

      const directions = [
        { dx: 0, dy: -1, wall: 'top' as const, opposite: 'bottom' as const },
        { dx: 1, dy: 0, wall: 'right' as const, opposite: 'left' as const },
        { dx: 0, dy: 1, wall: 'bottom' as const, opposite: 'top' as const },
        { dx: -1, dy: 0, wall: 'left' as const, opposite: 'right' as const },
      ];

      for (const dir of directions) {
        const nx = startX + dir.dx;
        const ny = startY + dir.dy;

        if (nx >= 0 && nx < this.cols && ny >= 0 && ny < this.rows) {
          const cell = this.grid[startY][startX];
          const neighbor = this.grid[ny][nx];

          if (cell.walls[dir.wall] && Math.random() > 0.5) {
            cell.walls[dir.wall] = false;
            neighbor.walls[dir.opposite] = false;
          }
        }
      }
    }
  }

  private isLargeMaze(): boolean {
    return this.rows * this.cols > 500;
  }

  private isHugeMaze(): boolean {
    return this.rows * this.cols > 5000;
  }

  generate(): Cell[][] {
    this.grid = this.initializeGrid();
    const isLarge = this.isLargeMaze();
    const isHuge = this.isHugeMaze();

    const algorithm = Math.random();

    if (isHuge) {
      this.generateBranchFactorFast();
    } else if (algorithm < 0.5) {
      this.generatePrimFast();
    } else {
      this.generateBranchFactorFast();
    }

    if (!isHuge) {
      if (this.rows * this.cols > 50) {
        this.addCyclePathsFast();
      }
      
      if (this.rows * this.cols > 100 && !isLarge) {
        this.addExtraBranchesFast();
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
