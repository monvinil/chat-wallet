'use client';

import { useState } from 'react';
import { ArrowUpRight, ArrowDownLeft, RefreshCw, Loader2 } from 'lucide-react';
import Link from 'next/link';

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { useTransactionHistory } from '@/lib/hooks';
import type { Transaction } from '@/lib/api';

function TransactionIcon({ type }: { type: Transaction['type'] }) {
  switch (type) {
    case 'send':
      return <ArrowUpRight className="h-4 w-4 text-red-500" />;
    case 'receive':
      return <ArrowDownLeft className="h-4 w-4 text-green-500" />;
    case 'swap':
      return <RefreshCw className="h-4 w-4 text-blue-500" />;
    default:
      return <ArrowUpRight className="h-4 w-4" />;
  }
}

function TransactionStatus({ status }: { status: Transaction['status'] }) {
  switch (status) {
    case 'confirmed':
      return <Badge variant="default" className="bg-green-500">Confirmed</Badge>;
    case 'pending':
      return <Badge variant="secondary">Pending</Badge>;
    case 'failed':
      return <Badge variant="destructive">Failed</Badge>;
    default:
      return null;
  }
}

function formatDate(dateString: string) {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  } else if (days === 1) {
    return 'Yesterday';
  } else if (days < 7) {
    return date.toLocaleDateString('en-US', { weekday: 'long' });
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
}

function formatAddress(address: string) {
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, refetch, isRefetching } = useTransactionHistory(page);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Transaction History</h1>
          <p className="text-muted-foreground">View your recent transactions</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isRefetching}
          aria-label="Refresh transactions"
        >
          {isRefetching ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-4 p-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : data?.transactions.length ? (
            <div className="divide-y">
              {data.transactions.map((tx) => (
                <div
                  key={tx.id}
                  className="flex items-center justify-between p-4 hover:bg-muted/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                      <TransactionIcon type={tx.type} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium capitalize">{tx.type}</p>
                        <TransactionStatus status={tx.status} />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {tx.type === 'send' ? 'To: ' : 'From: '}
                        <span className="font-mono">
                          {formatAddress(tx.type === 'send' ? tx.to_address : tx.from_address)}
                        </span>
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-medium ${tx.type === 'receive' ? 'text-green-500' : ''}`}>
                      {tx.type === 'receive' ? '+' : '-'}{tx.amount_formatted}
                    </p>
                    <p className="text-sm text-muted-foreground">{formatDate(tx.timestamp)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-12 text-center">
              <RefreshCw className="mx-auto mb-4 h-12 w-12 text-muted-foreground/50" />
              <h3 className="font-semibold">No transactions yet</h3>
              <p className="text-sm text-muted-foreground">
                Your transaction history will appear here
              </p>
              <Button asChild className="mt-4">
                <Link href="/send">Make your first transaction</Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {data && data.total > data.page * data.per_page && (
        <div className="flex justify-center">
          <Button
            variant="outline"
            onClick={() => setPage((prev) => prev + 1)}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading...
              </>
            ) : (
              'Load More'
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
