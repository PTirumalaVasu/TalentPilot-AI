import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { FormErrorText } from '@/components/ui/form-error-text';
import { useAuth } from '@/lib/auth/AuthContext';
import { login, type ApiErrorBody } from '@/lib/api/authApi';

const loginSchema = z.object({
  email: z
    .string()
    .trim()
    .min(1, 'Email is required')
    .email('Enter a valid email address'),
  password: z.string().trim().min(1, 'Password is required'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

const GENERIC_ERROR = 'Something went wrong, please try again.';

export function Login() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [formError, setFormError] = useState<string | null>(null);

  async function onSubmit(values: LoginFormValues) {
    setFormError(null);
    try {
      const { role, user_id } = await login(values.email, values.password);
      signIn(role, user_id);
      navigate(role === 'HR_ADMIN' ? '/hr/dashboard' : '/employee/content', { replace: true });
    } catch (err) {
      if (axios.isAxiosError<ApiErrorBody>(err) && err.response?.status === 401) {
        setFormError(err.response.data.message ?? GENERIC_ERROR);
      } else {
        setFormError(GENERIC_ERROR);
      }
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4 font-sans">
      <Card className="w-full max-w-sm">
        <CardContent className="p-8">
          <div className="mb-6 text-center">
            <div className="mb-1 text-lg font-bold text-gray-900">TalentPilot-AI</div>
            <p className="text-sm text-gray-500">Sign in to continue</p>
          </div>

          {formError && (
            <FormErrorText className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-red-700">
              {formError}
            </FormErrorText>
          )}

          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                aria-invalid={errors.email ? 'true' : 'false'}
                className="mt-1"
                {...register('email')}
              />
              {errors.email && <FormErrorText>{errors.email.message}</FormErrorText>}
            </div>

            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                aria-invalid={errors.password ? 'true' : 'false'}
                className="mt-1"
                {...register('password')}
              />
              {errors.password && <FormErrorText>{errors.password.message}</FormErrorText>}
            </div>

            <Button type="submit" className="w-full font-semibold" disabled={isSubmitting}>
              {isSubmitting ? 'Signing in…' : 'Sign In'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
