'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

import { useWalletBalances, useTransactionPreview, useTransactionSend } from '@/lib/hooks';
import { toast } from 'sonner';

const chains = [
  { value: 'base-mainnet', label: 'Base' },
  { value: 'arbitrum-mainnet', label: 'Arbitrum' },
  { value: 'ethereum-mainnet', label: 'Ethereum' },
];

export default function SendPage() {
  const router = useRouter();
  const { data: balances } = useWalletBalances();
  const previewMutation = useTransactionPreview();
  const sendMutation = useTransactionSend();

  const [toAddress, setToAddress] = useState('');
  const [amount, setAmount] = useState('');
  const [chain, setChain] = useState('base-mainnet');
  const [password, setPassword] = useState('');
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [successDialogOpen, setSuccessDialogOpen] = useState(false);
  const [txHash, setTxHash] = useState('');

  const handlePreview = async () => {
    if (!toAddress || !amount) return;

    try {
      await previewMutation.mutateAsync({
        to_address: toAddress,
        amount: parseFloat(amount),
        chain,
        token: 'USDC',
      });
      setConfirmDialogOpen(true);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to preview transaction');
    }
  };

  const handleSend = async () => {
    if (!password) return;

    const result = await sendMutation.mutateAsync({
      to_address: toAddress,
      amount: parseFloat(amount),
      chain,
      token: 'USDC',
      password,
    });

    setTxHash(result.transaction_hash);
    setConfirmDialogOpen(false);
    setSuccessDialogOpen(true);
    setPassword('');
  };

  const handleDone = () => {
    setSuccessDialogOpen(false);
    setToAddress('');
    setAmount('');
    router.push('/history');
  };

  const isValidAddress = (addr: string) => {
    return /^0x[a-fA-F0-9]{40}$/.test(addr);
  };

  const preview = previewMutation.data;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Send USDC</CardTitle>
          <CardDescription>
            Send USDC to any address on supported chains
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Chain selector */}
          <div className="space-y-2">
            <Label>Network</Label>
            <Select value={chain} onValueChange={setChain}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {chains.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Recipient address */}
          <div className="space-y-2">
            <Label htmlFor="address">Recipient Address</Label>
            <Input
              id="address"
              placeholder="0x..."
              value={toAddress}
              onChange={(e) => setToAddress(e.target.value)}
            />
            {toAddress && !isValidAddress(toAddress) && (
              <p className="flex items-center gap-1 text-sm text-destructive">
                <AlertCircle className="h-4 w-4" />
                Invalid address format
              </p>
            )}
          </div>

          {/* Amount */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="amount">Amount (USDC)</Label>
              <button
                type="button"
                className="text-xs text-primary hover:underline"
                onClick={() => setAmount(balances?.total_usdc?.toString() || '0')}
              >
                Max: {balances?.total_usdc_formatted || '$0.00'}
              </button>
            </div>
            <Input
              id="amount"
              type="number"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>

          {/* Preview button */}
          <Button
            className="w-full"
            onClick={handlePreview}
            disabled={
              !toAddress ||
              !isValidAddress(toAddress) ||
              !amount ||
              parseFloat(amount) <= 0 ||
              previewMutation.isPending
            }
          >
            {previewMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Calculating...
              </>
            ) : (
              <>
                Preview Transaction
                <ArrowRight className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialogOpen} onOpenChange={setConfirmDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Transaction</DialogTitle>
            <DialogDescription>
              Review and confirm your transaction details
            </DialogDescription>
          </DialogHeader>
          {preview && (
            <div className="space-y-4 py-4">
              <div className="space-y-2 rounded-lg bg-muted p-4">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Amount</span>
                  <span className="font-bold">{preview.amount_formatted}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">To</span>
                  <span className="font-mono text-sm">
                    {toAddress.slice(0, 8)}...{toAddress.slice(-6)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Network</span>
                  <span>{preview.chain_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Gas Fee</span>
                  <span>{preview.estimated_gas_usd}</span>
                </div>
                <div className="border-t pt-2">
                  <div className="flex justify-between font-bold">
                    <span>Total</span>
                    <span>{preview.total_cost_formatted}</span>
                  </div>
                </div>
              </div>

              {!preview.has_sufficient_balance && (
                <p className="flex items-center gap-2 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  Insufficient balance
                </p>
              )}

              {!preview.has_sufficient_gas && (
                <p className="flex items-center gap-2 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  Insufficient gas
                </p>
              )}

              <div className="space-y-2">
                <Label htmlFor="confirm-password">Enter password to confirm</Label>
                <Input
                  id="confirm-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Your wallet password"
                />
              </div>

              <Button
                className="w-full"
                onClick={handleSend}
                disabled={
                  !password ||
                  !preview.has_sufficient_balance ||
                  !preview.has_sufficient_gas ||
                  sendMutation.isPending
                }
              >
                {sendMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Sending...
                  </>
                ) : (
                  'Confirm & Send'
                )}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Success Dialog */}
      <Dialog open={successDialogOpen} onOpenChange={setSuccessDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              Transaction Sent!
            </DialogTitle>
            <DialogDescription>
              Your transaction has been submitted to the network
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="rounded-lg bg-muted p-4">
              <p className="text-sm text-muted-foreground">Transaction Hash</p>
              <p className="break-all font-mono text-sm">{txHash}</p>
            </div>
            <Button className="w-full" onClick={handleDone}>
              View in History
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
