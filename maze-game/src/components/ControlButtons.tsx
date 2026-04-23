import React from 'react';

interface ControlButtonsProps {
  onMove: (direction: 'up' | 'down' | 'left' | 'right') => void;
  disabled?: boolean;
}

const ControlButtons: React.FC<ControlButtonsProps> = ({ onMove, disabled }) => {
  const buttonStyle: React.CSSProperties = {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    border: 'none',
    fontSize: '32px',
    cursor: disabled ? 'not-allowed' : 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
    opacity: disabled ? 0.5 : 1,
    boxShadow: disabled ? 'none' : '0 6px 16px rgba(0,0,0,0.2)',
  };

  const buttonColors = {
    up: { background: 'linear-gradient(135deg, #FF6B6B, #FF8E8E)', active: '#FF5252' },
    down: { background: 'linear-gradient(135deg, #4ECDC4, #6EE7DE)', active: '#26A69A' },
    left: { background: 'linear-gradient(135deg, #FFE66D, #FFF59D)', active: '#FFD600' },
    right: { background: 'linear-gradient(135deg, #95E1D3, #B2EBF2)', active: '#4DD0E1' },
  };

  const handleButtonClick = (direction: 'up' | 'down' | 'left' | 'right') => {
    if (!disabled) {
      onMove(direction);
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      gap: '16px',
      padding: '24px',
      background: 'rgba(255,255,255,0.8)',
      borderRadius: '24px',
      boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
    }}>
      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#333', marginBottom: '8px' }}>
        🎮 控制按钮
      </div>
      
      <button
        style={{
          ...buttonStyle,
          background: buttonColors.up.background,
        }}
        onClick={() => handleButtonClick('up')}
        disabled={disabled}
        aria-label="向上移动"
      >
        ⬆️
      </button>
      
      <div style={{ display: 'flex', gap: '16px' }}>
        <button
          style={{
            ...buttonStyle,
            background: buttonColors.left.background,
          }}
          onClick={() => handleButtonClick('left')}
          disabled={disabled}
          aria-label="向左移动"
        >
          ⬅️
        </button>
        
        <button
          style={{
            ...buttonStyle,
            background: buttonColors.down.background,
          }}
          onClick={() => handleButtonClick('down')}
          disabled={disabled}
          aria-label="向下移动"
        >
          ⬇️
        </button>
        
        <button
          style={{
            ...buttonStyle,
            background: buttonColors.right.background,
          }}
          onClick={() => handleButtonClick('right')}
          disabled={disabled}
          aria-label="向右移动"
        >
          ➡️
        </button>
      </div>
      
      <div style={{ fontSize: '16px', color: '#666', marginTop: '8px' }}>
        也可以使用键盘方向键 ⌨️
      </div>
    </div>
  );
};

export default ControlButtons;
