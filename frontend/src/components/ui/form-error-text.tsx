import * as React from 'react';
import { cn } from '@/lib/utils';

export type FormErrorTextProps = React.HTMLAttributes<HTMLParagraphElement>;

export const FormErrorText = React.forwardRef<HTMLParagraphElement, FormErrorTextProps>(
  ({ className, ...props }, ref) => (
    <p ref={ref} role="alert" className={cn('text-sm text-red-600', className)} {...props} />
  )
);
FormErrorText.displayName = 'FormErrorText';
