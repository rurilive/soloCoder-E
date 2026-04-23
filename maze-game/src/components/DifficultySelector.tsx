import React from 'react';
import { Difficulty, DIFFICULTY_CONFIG } from '../types';

interface DifficultySelectorProps {
  currentDifficulty: Difficulty;
  onSelect: (difficulty: Difficulty) => void;
  disabled?: boolean;
}

const DifficultySelector: React.FC<DifficultySelectorProps> = ({ 
  currentDifficulty, 
  onSelect, 
  disabled 
}) => {
  const difficulties: Difficulty[] = ['easy', 'medium', 'hard'];

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      gap: '16px',
      padding: '20px',
      background: 'rgba(255,255,255,0.9)',
      borderRadius: '20px',
      boxShadow: '0 6px 24px rgba(0,0,0,0.1)',
    }}>
      <div style={{ 
        fontSize: '22px', 
        fontWeight: 'bold', 
        color: '#333',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        🎯 选择难度
      </div>
      
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
        {difficulties.map((difficulty) => {
          const config = DIFFICULTY_CONFIG[difficulty];
          const isSelected = currentDifficulty === difficulty;
          
          return (
            <button
              key={difficulty}
              onClick={() => !disabled && onSelect(difficulty)}
              disabled={disabled}
              style={{
                padding: '16px 32px',
                fontSize: '20px',
                fontWeight: 'bold',
                borderRadius: '16px',
                border: isSelected ? `4px solid ${config.color}` : '3px solid #E0E0E0',
                background: isSelected 
                  ? `linear-gradient(135deg, ${config.color}20, ${config.color}10)` 
                  : 'white',
                color: isSelected ? config.color : '#666',
                cursor: disabled ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: isSelected 
                  ? `0 4px 16px ${config.color}40` 
                  : '0 2px 8px rgba(0,0,0,0.08)',
                opacity: disabled ? 0.6 : 1,
                minWidth: '120px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <span style={{ fontSize: '24px' }}>
                {difficulty === 'easy' ? '🌱' : difficulty === 'medium' ? '🌿' : '🌳'}
              </span>
              <span>{config.label}</span>
              <span style={{ fontSize: '12px', fontWeight: 'normal' }}>
                {config.rows}x{config.cols}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default DifficultySelector;
