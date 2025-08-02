import { ButtonHTMLAttributes, forwardRef } from 'react';
import { type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';
import { buttonVariants } from './buttonVariants';

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';

export { Button };
