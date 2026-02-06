'use client';

import { Wallet, TrendingUp, Send, ArrowDownLeft, History } from 'lucide-react';
import { BottomNavLink } from './nav-link';

const navItems = [
  { href: '/wallet', icon: Wallet, label: 'Wallet' },
  { href: '/earn', icon: TrendingUp, label: 'Earn' },
  { href: '/send', icon: Send, label: 'Send' },
  { href: '/receive', icon: ArrowDownLeft, label: 'Receive' },
  { href: '/history', icon: History, label: 'History' },
];

export function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 md:hidden">
      <div className="grid h-16 grid-cols-5">
        {navItems.map((item) => (
          <BottomNavLink key={item.href} {...item} />
        ))}
      </div>
      {/* Safe area for iOS devices with notch */}
      <div className="bg-background" style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }} />
    </nav>
  );
}
