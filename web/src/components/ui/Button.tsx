import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-medium rounded-full min-h-[48px] px-6 transition-all duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-50 disabled:cursor-not-allowed select-none active:scale-[0.98] cursor-pointer';

  const sizeStyles = {
    sm: 'text-sm py-2 px-4 min-h-[44px]',
    md: 'text-base py-3 px-6 min-h-[48px]',
    lg: 'text-lg py-3.5 px-8 min-h-[54px]',
  };

  // High contrast palette:
  // Primary: background #6B9E7A, hover #5A8C69, text #102619 (contrast > 5.5:1)
  // Secondary: background #FAF6EF or soft leaf mint #BFE0C8, text #26362F
  // Outline: border 1.5px solid rgba(38,54,47,0.2), text #26362F
  // Ghost: hover bg rgba(38,54,47,0.06), text #26362F
  // Danger: background #EBA896, text #3A1710
  const variantStyles = {
    primary:
      'bg-[#6B9E7A] hover:bg-[#5A8C69] text-[#0E2317] font-semibold shadow-sm focus-visible:outline-[#2F533B]',
    secondary:
      'bg-[#BFE0C8] hover:bg-[#ACD4B6] text-[#1E3027] font-medium focus-visible:outline-[#6B9E7A]',
    outline:
      'bg-white/80 hover:bg-white text-[#26362F] border border-[#26362F]/15 hover:border-[#26362F]/30 focus-visible:outline-[#6B9E7A]',
    ghost:
      'bg-transparent hover:bg-[#26362F]/8 text-[#26362F] focus-visible:outline-[#6B9E7A]',
    danger:
      'bg-[#EBA896] hover:bg-[#E39783] text-[#3D140D] font-medium focus-visible:outline-[#C86047]',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-5 h-5 mr-2 animate-spin text-current" />
      ) : leftIcon ? (
        <span className="mr-2 inline-flex items-center">{leftIcon}</span>
      ) : null}
      <span>{children}</span>
      {!isLoading && rightIcon && (
        <span className="ml-2 inline-flex items-center">{rightIcon}</span>
      )}
    </button>
  );
};
