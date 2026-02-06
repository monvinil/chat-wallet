'use client';

import { ArrowUpRight, ArrowDownLeft, TrendingUp, Wallet, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import Link from 'next/link';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { useWalletBalances } from '@/lib/hooks';
import { useEarningsSummary } from '@/lib/hooks';
import { useYieldStatus } from '@/lib/hooks';
import { useAuthStore } from '@/lib/stores/auth';
import { toast } from 'sonner';

export default function WalletPage() {
  const { user } = useAuthStore();
  const { data: balances, isLoading: balancesLoading } = useWalletBalances();
  const { data: earnings, isLoading: earningsLoading } = useEarningsSummary();
  const { data: yieldStatus } = useYieldStatus();
  const [copied, setCopied] = useState(false);

  const copyAddress = async () => {
    if (!user?.evm_address) return;
    try {
      await navigator.clipboard.writeText(user.evm_address);
      setCopied(true);
      toast.success('Address copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy address');
    }
  };

  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  return (
    <div className="space-y-6">
      {/* Total Balance Card */}
      <Card className="bg-gradient-to-br from-primary/10 via-primary/5 to-background">
        <CardHeader className="pb-2">
          <CardDescription>Total Balance</CardDescription>
          {balancesLoading ? (
            <Skeleton className="h-10 w-48" />
          ) : (
            <CardTitle className="text-4xl font-bold">
              {balances?.total_usdc_formatted || '$0.00'}
            </CardTitle>
          )}
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Wallet className="h-4 w-4" />
            <span className="font-mono">{user?.evm_address ? formatAddress(user.evm_address) : '...'}</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={copyAddress}
              aria-label="Copy address to clipboard"
            >
              {copied ? (
                <Check className="h-3 w-3 text-green-500" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </Button>
          </div>

          {/* Quick actions */}
          <div className="mt-4 flex gap-2">
            <Button asChild className="flex-1">
              <Link href="/send">
                <ArrowUpRight className="mr-2 h-4 w-4" />
                Send
              </Link>
            </Button>
            <Button asChild variant="outline" className="flex-1">
              <Link href="/receive">
                <ArrowDownLeft className="mr-2 h-4 w-4" />
                Receive
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Today's Earnings */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardDescription>Today&apos;s Earnings</CardDescription>
            <Link href="/earn" className="text-sm text-primary hover:underline">
              View details
            </Link>
          </div>
          {earningsLoading ? (
            <Skeleton className="h-8 w-24" />
          ) : (
            <CardTitle className="flex items-center gap-2 text-2xl text-green-500">
              +{earnings?.today_formatted || '$0.00'}
              <TrendingUp className="h-5 w-5" />
            </CardTitle>
          )}
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xs text-muted-foreground">This Week</p>
              {earningsLoading ? (
                <Skeleton className="mx-auto h-5 w-16" />
              ) : (
                <p className="font-medium text-green-500">+{earnings?.this_week_formatted || '$0.00'}</p>
              )}
            </div>
            <div>
              <p className="text-xs text-muted-foreground">This Month</p>
              {earningsLoading ? (
                <Skeleton className="mx-auto h-5 w-16" />
              ) : (
                <p className="font-medium text-green-500">+{earnings?.this_month_formatted || '$0.00'}</p>
              )}
            </div>
            <div>
              <p className="text-xs text-muted-foreground">All Time</p>
              {earningsLoading ? (
                <Skeleton className="mx-auto h-5 w-16" />
              ) : (
                <p className="font-medium text-green-500">+{earnings?.all_time_formatted || '$0.00'}</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chain Balances */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Balances by Chain</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {balancesLoading ? (
            <>
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </>
          ) : balances?.balances.length ? (
            balances.balances.map((chain) => (
              <div
                key={chain.chain}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                    <span className="text-sm font-bold">{chain.chain_name.charAt(0)}</span>
                  </div>
                  <div>
                    <p className="font-medium">{chain.chain_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {chain.native_balance.toFixed(4)} {chain.native_symbol}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium">{chain.usdc_balance_formatted}</p>
                  <Badge variant="secondary" className="text-xs">
                    USDC
                  </Badge>
                </div>
              </div>
            ))
          ) : (
            <div className="py-8 text-center text-muted-foreground">
              <p>No balances yet</p>
              <p className="text-sm">Deposit USDC to get started</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* CTA to enable yield - only show when yield is not active */}
      {!yieldStatus?.enabled && (
        <Card className="border-dashed">
          <CardContent className="py-6">
            <div className="text-center">
              <TrendingUp className="mx-auto mb-2 h-8 w-8 text-primary" />
              <h3 className="font-semibold">Start earning on your USDC</h3>
              <p className="mb-4 text-sm text-muted-foreground">
                Enable yield to earn up to 8% APY automatically
              </p>
              <Button asChild>
                <Link href="/earn">
                  Enable Yield
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
