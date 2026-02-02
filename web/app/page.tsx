'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { CircleDollarSign, Loader2 } from 'lucide-react';
import { useAuthStore } from '@/lib/stores/auth';

export default function HomePage() {
  const router = useRouter();
  const { checkAuth } = useAuthStore();

  useEffect(() => {
    // Check auth and redirect
    const isAuth = checkAuth();
    if (isAuth) {
      router.replace('/wallet');
    } else {
      router.replace('/login');
    }
  }, [checkAuth, router]);

  // Show loading while checking auth
  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <CircleDollarSign className="mb-4 h-16 w-16 text-primary animate-pulse" />
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );
}
