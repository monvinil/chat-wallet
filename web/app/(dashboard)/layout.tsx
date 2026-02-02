'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar, BottomNav, Header } from '@/components/common';
import { useAuthStore } from '@/lib/stores/auth';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    // Check auth status on mount
    const isAuth = checkAuth();
    if (!isAuth) {
      router.replace('/login');
    }
  }, [checkAuth, router]);

  // Don't render anything while checking auth
  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Mobile header */}
        <Header />

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 pb-20 md:p-6 md:pb-6">
          {children}
        </main>

        {/* Mobile bottom nav */}
        <BottomNav />
      </div>
    </div>
  );
}
