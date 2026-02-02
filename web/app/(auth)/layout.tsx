'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { CircleDollarSign } from 'lucide-react';
import { useAuthStore } from '@/lib/stores/auth';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    // If already authenticated, redirect to wallet
    const isAuth = checkAuth();
    if (isAuth) {
      router.replace('/wallet');
    }
  }, [checkAuth, router]);

  // Don't render auth pages if authenticated
  if (isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-background to-muted p-4">
      {/* Logo */}
      <div className="mb-8 flex items-center gap-2">
        <CircleDollarSign className="h-10 w-10 text-primary" />
        <span className="text-2xl font-bold">USDChat</span>
      </div>

      {/* Auth form container */}
      <div className="w-full max-w-md">
        {children}
      </div>

      {/* Footer */}
      <p className="mt-8 text-center text-sm text-muted-foreground">
        Make your USDC work for you
      </p>
    </div>
  );
}
