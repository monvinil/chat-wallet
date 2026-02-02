'use client';

import Link from 'next/link';
import {
  Wallet,
  TrendingUp,
  Send,
  History,
  Settings,
  LogOut,
  CircleDollarSign,
} from 'lucide-react';
import { NavLink } from './nav-link';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { useAuthStore } from '@/lib/stores/auth';

const navItems = [
  { href: '/wallet', icon: Wallet, label: 'Wallet' },
  { href: '/earn', icon: TrendingUp, label: 'Earn' },
  { href: '/send', icon: Send, label: 'Send' },
  { href: '/history', icon: History, label: 'History' },
];

export function Sidebar() {
  const { logout, user } = useAuthStore();

  return (
    <aside className="hidden md:flex h-screen w-64 flex-col border-r bg-card">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <CircleDollarSign className="h-8 w-8 text-primary" />
        <span className="text-xl font-bold">USDChat</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => (
          <NavLink key={item.href} {...item} />
        ))}
      </nav>

      {/* User section */}
      <div className="border-t p-4">
        <div className="mb-3 truncate text-sm text-muted-foreground">
          {user?.email}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" asChild className="flex-1">
            <Link href="/settings">
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </Link>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="text-destructive hover:text-destructive"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  );
}
