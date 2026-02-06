'use client';

import { useState } from 'react';
import { Copy, Check, QrCode } from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useWalletAddress } from '@/lib/hooks';
import { useAuthStore } from '@/lib/stores/auth';
import { toast } from 'sonner';

const chains = [
  { value: 'base-mainnet', label: 'Base', description: 'Fastest & cheapest' },
  { value: 'arbitrum-mainnet', label: 'Arbitrum', description: 'Low fees' },
  { value: 'ethereum-mainnet', label: 'Ethereum', description: 'Mainnet' },
];

export default function ReceivePage() {
  const { user } = useAuthStore();
  const [selectedChain, setSelectedChain] = useState('base-mainnet');
  const { data: addressData, isLoading } = useWalletAddress(selectedChain);
  const [copied, setCopied] = useState(false);

  const copyAddress = async () => {
    const address = addressData?.address || user?.evm_address;
    if (!address) return;
    try {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      toast.success('Address copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy address');
    }
  };

  const address = addressData?.address || user?.evm_address || '';
  const selectedChainLabel = chains.find(c => c.value === selectedChain)?.label || '';

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Receive USDC</CardTitle>
          <CardDescription>
            Send USDC to the address below to deposit into your wallet
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Chain selector */}
          <Tabs value={selectedChain} onValueChange={setSelectedChain}>
            <TabsList className="grid w-full grid-cols-3">
              {chains.map((chain) => (
                <TabsTrigger key={chain.value} value={chain.value}>
                  {chain.label}
                </TabsTrigger>
              ))}
            </TabsList>
            {chains.map((chain) => (
              <TabsContent key={chain.value} value={chain.value}>
                <p className="text-sm text-muted-foreground">{chain.description}</p>
              </TabsContent>
            ))}
          </Tabs>

          {/* QR Code */}
          <div className="flex justify-center">
            {isLoading ? (
              <Skeleton className="h-48 w-48" />
            ) : addressData?.qr_code ? (
              <div className="rounded-lg border bg-white p-4">
                <img
                  src={`data:image/png;base64,${addressData.qr_code}`}
                  alt={`QR code for your ${selectedChainLabel} deposit address`}
                  className="h-40 w-40"
                />
              </div>
            ) : (
              <div className="flex h-48 w-48 items-center justify-center rounded-lg border bg-muted">
                <QrCode className="h-16 w-16 text-muted-foreground" />
              </div>
            )}
          </div>

          {/* Address */}
          <div className="space-y-2">
            <p className="text-sm font-medium">Your {selectedChainLabel} Address</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 break-all rounded-lg bg-muted p-3 text-sm">
                {isLoading ? <Skeleton className="h-5 w-full" /> : address}
              </code>
              <Button
                variant="outline"
                size="icon"
                onClick={copyAddress}
                disabled={isLoading}
                aria-label="Copy address to clipboard"
              >
                {copied ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          {/* USDC Contract info */}
          {addressData?.usdc_contract && (
            <div className="rounded-lg bg-muted/50 p-3 text-sm">
              <p className="font-medium">USDC Contract</p>
              <code className="text-xs text-muted-foreground">{addressData.usdc_contract}</code>
            </div>
          )}

          {/* Warning */}
          <div className="rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-4 text-sm">
            <p className="font-medium text-yellow-600 dark:text-yellow-500">Important</p>
            <p className="text-muted-foreground">
              Only send USDC on the {selectedChainLabel} network to this address.
              Sending other tokens or using the wrong network may result in permanent loss of funds.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
