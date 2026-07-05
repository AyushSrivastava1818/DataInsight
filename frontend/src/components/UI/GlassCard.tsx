import React from 'react';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
  onClick?: () => void;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className = '',
  hoverEffect = false,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`
        glass-card
        p-6
        transition-all
        duration-300
        ${hoverEffect ? 'hover:-translate-y-1 hover:shadow-xl hover:border-brand-500/20 dark:hover:border-brand-400/20 hover:bg-white/80 dark:hover:bg-slate-900/80 cursor-pointer' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  );
};
