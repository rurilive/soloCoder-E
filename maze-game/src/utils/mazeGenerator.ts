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

  private getNeighbors(cell: Cell, visited: boolean = false): Cell[] {
    const neighbors: Cell[] = [];
    const { x, y } = cell;
    const directions = [
      { dx: 0, dy: -1, name: 'top' },
      { dx: 1, dy: 0, name: 'right' },
      { dx: 0, dy: 1, name: 'bottom' },
      { dx: -1, dy: 0, name: 'left' },
    ];
    
    const shuffledDirections = [...directions].sort(() => Math.random() - 0.5);

    for (const dir of shuffledDirections) {
      const nx = x + dir.dx;
      const ny = y + dir.dy;
      if (nx >= 0 && nx < this.cols && ny >= 0 && ny < this.rows) {
        const neighbor = this.grid[ny][nx];
        if (visited === neighbor.visited) {
          neighbors.push(neighbor);
        }
      }
    }
    return neighbors;
  }

  private getVisitedNeighbors(cell: Cell): Cell[] {
    const neighbors: Cell[] = [];
    const { x, y } = cell;
    const directions = [
      { dx: 0, dy: -1, name: 'top' },
      { dx: 1, dy: 0, name: 'right' },
      { dx: 0, dy: 1, name: 'bottom' },
      { dx: -1, dy: 0, name: 'left' },
    ];
    
    const shuffledDirections = [...directions].sort(() => Math.random() - 0.5);

    for (const dir of shuffledDirections) {
      const nx = x + dir.dx;
      const ny = y + dir.dy;
      if (nx >= 0 && nx < this.cols && ny >= 0 && ny < this.rows) {
        const neighbor = this.grid[ny][nx];
        if (neighbor.visited) {
          neighbors.push(neighbor);
        }
      }
    }
    return neighbors;
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

  private generatePrimMaze(): void {
    const startCell = this.grid[0][0];
    startCell.visited = true;

    const frontier: Cell[] = [...this.getNeighbors(startCell, false)];

    while (frontier.length > 0) {
      const randomIndex = Math.floor(Math.random() * frontier.length);
      const current = frontier[randomIndex];
      frontier.splice(randomIndex, 1);

      if (current.visited) continue;

      current.visited = true;

      const visitedNeighbors = this.getVisitedNeighbors(current);
      if (visitedNeighbors.length > 0) {
        const neighbor = visitedNeighbors[Math.floor(Math.random() * visitedNeighbors.length)];
        this.removeWalls(current, neighbor);
      }

      const newFrontier = this.getNeighbors(current, false);
      for (const cell of newFrontier) {
        if (!frontier.includes(cell)) {
          frontier.push(cell);
        }
      }
    }
  }

  private generateBranchFactorMaze(): void {
    const stack: Cell[] = [];
    const startCell = this.grid[0][0];
    startCell.visited = true;
    stack.push(startCell);

    while (stack.length > 0) {
      const randomIndex = Math.floor(Math.random() * stack.length);
      const current = stack[randomIndex];
      const neighbors = this.getNeighbors(current, false);

      if (neighbors.length > 0) {
        const numBranches = Math.min(
          neighbors.length,
          Math.floor(Math.random() * 3) + 1
        );

        for (let i = 0; i < numBranches; i++) {
          const nextIndex = Math.floor(Math.random() * neighbors.length);
          const next = neighbors[nextIndex];
          neighbors.splice(nextIndex, 1);

          next.visited = true;
          this.removeWalls(current, next);
          stack.push(next);
        }
      } else {
        stack.splice(randomIndex, 1);
      }
    }
  }

  private addExtraBranches(): void {
    const allCells: Cell[] = [];
    for (let y = 0; y < this.rows; y++) {
      for (let x = 0; x < this.cols; x++) {
        allCells.push(this.grid[y][x]);
      }
    }

    const numExtraPaths = Math.floor((this.rows * this.cols) * 0.08);
    
    for (let i = 0; i < numExtraPaths; i++) {
      const cell = allCells[Math.floor(Math.random() * allCells.length)];
      const neighbors = this.getAllNeighbors(cell);
      
      if (neighbors.length > 0) {
        const neighbor = neighbors[Math.floor(Math.random() * neighbors.length)];
        this.removeWalls(cell, neighbor);
      }
    }
  }

  private getAllNeighbors(cell: Cell): Cell[] {
    const neighbors: Cell[] = [];
    const { x, y } = cell;

    if (y > 0) neighbors.push(this.grid[y - 1][x]);
    if (x < this.cols - 1) neighbors.push(this.grid[y][x + 1]);
    if (y < this.rows - 1) neighbors.push(this.grid[y + 1][x]);
    if (x > 0) neighbors.push(this.grid[y][x - 1]);

    return neighbors;
  }

  private createDeadEnds(): void {
    const totalCells = this.rows * this.cols;
    
    if (totalCells < 100) return;
    
    const wallsToAdd = Math.floor(totalCells * 0.05);
    let added = 0;
    
    for (let attempt = 0; attempt < wallsToAdd * 10 && added < wallsToAdd; attempt++) {
      const x = Math.floor(Math.random() * (this.cols - 2)) + 1;
      const y = Math.floor(Math.random() * (this.rows - 2)) + 1;
      const cell = this.grid[y][x];
      
      const directions = ['top', 'right', 'bottom', 'left'] as const;
      const randomDir = directions[Math.floor(Math.random() * 4)];
      
      if (!cell.walls[randomDir]) {
        cell.walls[randomDir] = true;
        
        if (this.isMazeSolvable()) {
          added++;
        } else {
          cell.walls[randomDir] = false;
        }
      }
    }
  }

  private isMazeSolvable(): boolean {
    const visited = new Set<string>();
    const queue: { x: number; y: number }[] = [{ x: 0, y: 0 }];
    const goalX = this.cols - 1;
    const goalY = this.rows - 1;

    while (queue.length > 0) {
      const current = queue.shift()!;
      const key = `${current.x},${current.y}`;

      if (current.x === goalX && current.y === goalY) {
        return true;
      }

      if (visited.has(key)) continue;
      visited.add(key);

      const cell = this.grid[current.y][current.x];

      if (!cell.walls.top && current.y > 0) {
        queue.push({ x: current.x, y: current.y - 1 });
      }
      if (!cell.walls.right && current.x < this.cols - 1) {
        queue.push({ x: current.x + 1, y: current.y });
      }
      if (!cell.walls.bottom && current.y < this.rows - 1) {
        queue.push({ x: current.x, y: current.y + 1 });
      }
      if (!cell.walls.left && current.x > 0) {
        queue.push({ x: current.x - 1, y: current.y });
      }
    }

    return false;
  }

  private addCyclePaths(): void {
    const numCycles = Math.floor(Math.random() * 3) + 2;
    
    for (let i = 0; i < numCycles; i++) {
      const startX = Math.floor(Math.random() * (this.cols - 3)) + 1;
      const startY = Math.floor(Math.random() * (this.rows - 3)) + 1;
      
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

  generate(): Cell[][] {
    this.grid = this.initializeGrid();

    const algorithm = Math.random();
    
    if (algorithm < 0.4) {
      this.generatePrimMaze();
    } else if (algorithm < 0.7) {
      this.generateBranchFactorMaze();
    } else {
      this.generatePrimMaze();
      this.addExtraBranches();
    }

    if (this.rows * this.cols > 50) {
      this.addCyclePaths();
    }

    if (this.rows * this.cols > 100) {
      this.createDeadEnds();
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
