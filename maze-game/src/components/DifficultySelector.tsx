import React, { useState } from 'react';
import { Difficulty, DIFFICULTY_CONFIG, CUSTOM_SIZE_CONFIG, CustomSize } from '../types';

interface DifficultySelectorProps {
  currentDifficulty: Difficulty;
  customSize: CustomSize;
  onSelect: (difficulty: Difficulty) => void;
  onCustomSizeChange: (size: CustomSize) => void;
  disabled?: boolean;
}

const DifficultySelector: React.FC<DifficultySelectorProps> = ({ 
  currentDifficulty, 
  customSize,
  onSelect, 
  onCustomSizeChange,
  disabled 
}) => {
  const [localRows, setLocalRows] = useState(customSize.rows.toString());
  const [localCols, setLocalCols] = useState(customSize.cols.toString());

  const difficulties: Difficulty[] = ['easy', 'medium', 'hard', 'custom'];

  const getDifficultyIcon = (difficulty: Difficulty): string => {
    switch (difficulty) {
      case 'easy': return '🌱';
      case 'medium': return '🌿';
      case 'hard': return '🌳';
      case 'custom': return '🔥';
      default: return '🎯';
    }
  };

  const handleSizeInput = (type: 'rows' | 'cols', value: string) => {
    const numValue = parseInt(value) || 0;
    
    if (type === 'rows') {
      setLocalRows(value);
      if (numValue >= CUSTOM_SIZE_CONFIG.min && numValue <= CUSTOM_SIZE_CONFIG.max) {
        onCustomSizeChange({ ...customSize, rows: numValue });
      }
    } else {
      setLocalCols(value);
      if (numValue >= CUSTOM_SIZE_CONFIG.min && numValue <= CUSTOM_SIZE_CONFIG.max) {
        onCustomSizeChange({ ...customSize, cols: numValue });
      }
    }
  };

  const handleSizeBlur = (type: 'rows' | 'cols') => {
    const value = type === 'rows' ? localRows : localCols;
    let numValue = parseInt(value) || CUSTOM_SIZE_CONFIG.default;
    
    if (numValue < CUSTOM_SIZE_CONFIG.min) numValue = CUSTOM_SIZE_CONFIG.min;
    if (numValue > CUSTOM_SIZE_CONFIG.max) numValue = CUSTOM_SIZE_CONFIG.max;
    
    if (type === 'rows') {
      setLocalRows(numValue.toString());
      onCustomSizeChange({ ...customSize, rows: numValue });
    } else {
      setLocalCols(numValue.toString());
      onCustomSizeChange({ ...customSize, cols: numValue });
    }
  };

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
                {getDifficultyIcon(difficulty)}
              </span>
              <span>{config.label}</span>
              <span style={{ fontSize: '12px', fontWeight: 'normal' }}>
                {difficulty === 'custom' 
                  ? `自定义 (${CUSTOM_SIZE_CONFIG.min}-${CUSTOM_SIZE_CONFIG.max})` 
                  : `${config.rows}x${config.cols}`}
              </span>
            </button>
          );
        })}
      </div>

      {currentDifficulty === 'custom' && (
        <div style={{
          padding: '20px',
          background: 'linear-gradient(135deg, #F3E5F5, #E1BEE7)',
          borderRadius: '16px',
          border: '3px solid #9C27B0',
          width: '100%',
          maxWidth: '400px',
        }}>
          <div style={{
            fontSize: '18px',
            fontWeight: 'bold',
            color: '#9C27B0',
            marginBottom: '16px',
            textAlign: 'center',
          }}>
            🔥 自定义迷宫尺寸
          </div>
          
          <div style={{
            display: 'flex',
            gap: '20px',
            justifyContent: 'center',
            alignItems: 'center',
            flexWrap: 'wrap',
          }}>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              alignItems: 'center',
            }}>
              <label style={{
                fontSize: '16px',
                fontWeight: 'bold',
                color: '#333',
              }}>
                行数 📏
              </label>
              <input
                type="number"
                min={CUSTOM_SIZE_CONFIG.min}
                max={CUSTOM_SIZE_CONFIG.max}
                value={localRows}
                onChange={(e) => handleSizeInput('rows', e.target.value)}
                onBlur={() => handleSizeBlur('rows')}
                disabled={disabled}
                style={{
                  width: '100px',
                  padding: '12px 16px',
                  fontSize: '20px',
                  fontWeight: 'bold',
                  textAlign: 'center',
                  borderRadius: '12px',
                  border: '3px solid #9C27B0',
                  background: 'white',
                  color: '#9C27B0',
                  cursor: disabled ? 'not-allowed' : 'text',
                }}
              />
            </div>

            <div style={{
              fontSize: '32px',
              fontWeight: 'bold',
              color: '#9C27B0',
            }}>
              ×
            </div>

            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              alignItems: 'center',
            }}>
              <label style={{
                fontSize: '16px',
                fontWeight: 'bold',
                color: '#333',
              }}>
                列数 📐
              </label>
              <input
                type="number"
                min={CUSTOM_SIZE_CONFIG.min}
                max={CUSTOM_SIZE_CONFIG.max}
                value={localCols}
                onChange={(e) => handleSizeInput('cols', e.target.value)}
                onBlur={() => handleSizeBlur('cols')}
                disabled={disabled}
                style={{
                  width: '100px',
                  padding: '12px 16px',
                  fontSize: '20px',
                  fontWeight: 'bold',
                  textAlign: 'center',
                  borderRadius: '12px',
                  border: '3px solid #9C27B0',
                  background: 'white',
                  color: '#9C27B0',
                  cursor: disabled ? 'not-allowed' : 'text',
                }}
              />
            </div>
          </div>

          <div style={{
            fontSize: '12px',
            color: '#7B1FA2',
            textAlign: 'center',
            marginTop: '12px',
            fontStyle: 'italic',
          }}>
            💡 提示：数值越大迷宫越难！范围：{CUSTOM_SIZE_CONFIG.min} - {CUSTOM_SIZE_CONFIG.max}
          </div>
        </div>
      )}
    </div>
  );
};

export default DifficultySelector;
