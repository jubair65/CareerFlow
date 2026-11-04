import { useState } from 'react';
import type { InputHTMLAttributes } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface AuthFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  error?: string;
  testId?: string;
  toggleTestId?: string;
}

export function AuthField({
  id,
  label,
  type = 'text',
  error,
  testId,
  toggleTestId,
  className = '',
  ...props
}: AuthFieldProps) {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === 'password';
  const effectiveType = isPassword ? (showPassword ? 'text' : 'password') : type;
  const errorId = `${id}-error`;

  return (
    <div className="space-y-1.5 text-left">
      <label
        htmlFor={id}
        className="block text-xs sm:text-sm font-semibold text-[#253142]"
      >
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={effectiveType}
          data-testid={testId}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
          className={`w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-[#253142] placeholder-[#9ca9b8] transition duration-150 focus:outline-hidden ${
            error
              ? 'border-[#b34a40] focus:ring-2 focus:ring-[#b34a40]/30'
              : 'border-[#d9dbd1] focus:border-[#253142] focus:ring-2 focus:ring-[#f5c84b]/40'
          } ${isPassword ? 'pr-11' : ''} ${className}`}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            data-testid={toggleTestId || `${testId}-toggle`}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            aria-pressed={showPassword}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center justify-center h-7 w-7 rounded-lg text-[#7b8490] hover:text-[#253142] hover:bg-[#eef0e7] transition focus:outline-hidden focus:ring-2 focus:ring-[#f5c84b]/60 cursor-pointer"
          >
            {showPassword ? (
              <EyeOff size={16} className="shrink-0" />
            ) : (
              <Eye size={16} className="shrink-0" />
            )}
          </button>
        )}
      </div>
      {error && (
        <span
          id={errorId}
          data-testid={`${testId}-error`}
          className="block text-xs font-medium text-[#b34a40] mt-1"
        >
          {error}
        </span>
      )}
    </div>
  );
}

