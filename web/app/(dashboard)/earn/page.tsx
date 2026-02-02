'use client';

import { useState } from 'react';
import {
  TrendingUp,
  Zap,
  Calendar,
  ChevronRight,
  Loader2,
  Info,
  Pause,
  Play,
  Trash2,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import { useYieldStatus, useYieldDeposit, useYieldWithdraw } from '@/lib/hooks';
import { useSchedules, useCreateSchedule, useCancelSchedule, usePauseSchedule, useResumeSchedule } from '@/lib/hooks';
import { useEarningsSummary, useEarningsHistory } from '@/lib/hooks';
import { useWalletBalances } from '@/lib/hooks';

// Mock chart data (will be replaced with real data)
const mockChartData = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  earnings: Math.random() * 0.5 + 0.2,
}));

export default function EarnPage() {
  const { data: yieldStatus, isLoading: yieldLoading } = useYieldStatus();
  const { data: schedules, isLoading: schedulesLoading } = useSchedules();
  const { data: earnings, isLoading: earningsLoading } = useEarningsSummary();
  const { data: balances } = useWalletBalances();

  const depositMutation = useYieldDeposit();
  const withdrawMutation = useYieldWithdraw();
  const createScheduleMutation = useCreateSchedule();
  const cancelScheduleMutation = useCancelSchedule();
  const pauseScheduleMutation = usePauseSchedule();
  const resumeScheduleMutation = useResumeSchedule();

  const [yieldDialogOpen, setYieldDialogOpen] = useState(false);
  const [dcaDialogOpen, setDcaDialogOpen] = useState(false);
  const [dcaAmount, setDcaAmount] = useState('50');
  const [dcaFrequency, setDcaFrequency] = useState<'daily' | 'weekly' | 'biweekly' | 'monthly'>('weekly');
  const [dcaToken, setDcaToken] = useState('ETH');
  const [password, setPassword] = useState('');

  const handleEnableYield = async () => {
    if (!password || !balances?.total_usdc) return;
    await depositMutation.mutateAsync({
      amount: balances.total_usdc,
      password,
    });
    setYieldDialogOpen(false);
    setPassword('');
  };

  const handleCreateDCA = async () => {
    await createScheduleMutation.mutateAsync({
      type: 'dca',
      amount: parseFloat(dcaAmount),
      frequency: dcaFrequency,
      target_token: dcaToken,
    });
    setDcaDialogOpen(false);
  };

  return (
    <div className="space-y-6">
      {/* Earnings Summary */}
      <Card className="bg-gradient-to-br from-green-500/10 via-green-500/5 to-background">
        <CardHeader className="pb-2">
          <CardDescription>Total Earnings</CardDescription>
          {earningsLoading ? (
            <Skeleton className="h-10 w-32" />
          ) : (
            <CardTitle className="text-4xl font-bold text-green-500">
              +{earnings?.all_time_formatted || '$0.00'}
            </CardTitle>
          )}
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Today</p>
              <p className="text-lg font-semibold text-green-500">
                +{earnings?.today_formatted || '$0.00'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">This Month</p>
              <p className="text-lg font-semibold text-green-500">
                +{earnings?.this_month_formatted || '$0.00'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Earnings Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Earnings History</CardTitle>
          <CardDescription>Last 30 days</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockChartData}>
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `$${value.toFixed(2)}`}
                />
                <Tooltip
                  formatter={(value) => [`$${(value as number).toFixed(2)}`, 'Earnings']}
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="earnings"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Yield Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-500" />
              <CardTitle className="text-lg">Yield Earning</CardTitle>
            </div>
            <Badge variant={yieldStatus?.enabled ? 'default' : 'secondary'}>
              {yieldStatus?.enabled ? 'Active' : 'Inactive'}
            </Badge>
          </div>
          <CardDescription>
            Earn up to 8% APY on your USDC with Aave
          </CardDescription>
        </CardHeader>
        <CardContent>
          {yieldLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : yieldStatus?.enabled ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg bg-muted p-4">
                <div>
                  <p className="text-sm text-muted-foreground">Deposited</p>
                  <p className="text-xl font-bold">{yieldStatus.deposited_amount_formatted}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Current APY</p>
                  <p className="text-xl font-bold text-green-500">{yieldStatus.apy}%</p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center text-sm">
                <div className="rounded-lg bg-muted/50 p-2">
                  <p className="text-muted-foreground">Daily</p>
                  <p className="font-medium text-green-500">+${yieldStatus.projected_daily.toFixed(2)}</p>
                </div>
                <div className="rounded-lg bg-muted/50 p-2">
                  <p className="text-muted-foreground">Monthly</p>
                  <p className="font-medium text-green-500">+${yieldStatus.projected_monthly.toFixed(2)}</p>
                </div>
                <div className="rounded-lg bg-muted/50 p-2">
                  <p className="text-muted-foreground">Yearly</p>
                  <p className="font-medium text-green-500">+${yieldStatus.projected_yearly.toFixed(2)}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center">
              <p className="mb-4 text-muted-foreground">
                Your USDC is currently earning 0%. Enable yield to start earning.
              </p>
              <Dialog open={yieldDialogOpen} onOpenChange={setYieldDialogOpen}>
                <DialogTrigger asChild>
                  <Button size="lg">
                    <Zap className="mr-2 h-4 w-4" />
                    Enable Yield
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Enable Yield Earning</DialogTitle>
                    <DialogDescription>
                      Your USDC will be deposited into Aave to earn yield. You can withdraw anytime.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="rounded-lg bg-muted p-4">
                      <div className="flex justify-between">
                        <span>Amount to deposit</span>
                        <span className="font-bold">{balances?.total_usdc_formatted || '$0.00'}</span>
                      </div>
                      <div className="mt-2 flex justify-between text-sm text-muted-foreground">
                        <span>Estimated APY</span>
                        <span className="text-green-500">~8.2%</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="password">Enter password to confirm</Label>
                      <Input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Your wallet password"
                      />
                    </div>
                    <Button
                      className="w-full"
                      onClick={handleEnableYield}
                      disabled={!password || depositMutation.isPending}
                    >
                      {depositMutation.isPending ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Enabling...
                        </>
                      ) : (
                        'Enable Yield'
                      )}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Auto-DCA Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-500" />
              <CardTitle className="text-lg">Auto-Invest (DCA)</CardTitle>
            </div>
            <Dialog open={dcaDialogOpen} onOpenChange={setDcaDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  Add Schedule
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create Auto-Invest Schedule</DialogTitle>
                  <DialogDescription>
                    Automatically buy crypto at regular intervals
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Amount (USDC)</Label>
                    <Input
                      type="number"
                      value={dcaAmount}
                      onChange={(e) => setDcaAmount(e.target.value)}
                      placeholder="50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Frequency</Label>
                    <Select value={dcaFrequency} onValueChange={(v) => setDcaFrequency(v as typeof dcaFrequency)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="biweekly">Every 2 weeks</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Buy</Label>
                    <Select value={dcaToken} onValueChange={setDcaToken}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ETH">Ethereum (ETH)</SelectItem>
                        <SelectItem value="BTC">Bitcoin (WBTC)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="rounded-lg bg-muted p-3 text-sm">
                    <p className="text-muted-foreground">
                      You&apos;ll buy ${dcaAmount} worth of {dcaToken} every {dcaFrequency === 'biweekly' ? '2 weeks' : dcaFrequency.replace('ly', '')}.
                    </p>
                  </div>
                  <Button
                    className="w-full"
                    onClick={handleCreateDCA}
                    disabled={createScheduleMutation.isPending}
                  >
                    {createScheduleMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      'Start Auto-Invest'
                    )}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          <CardDescription>
            Dollar-cost average into ETH or BTC automatically
          </CardDescription>
        </CardHeader>
        <CardContent>
          {schedulesLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : schedules?.length ? (
            <div className="space-y-3">
              {schedules.map((schedule) => (
                <div
                  key={schedule.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <p className="font-medium">
                      ${schedule.amount} → {schedule.target_token}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Every {schedule.frequency === 'biweekly' ? '2 weeks' : schedule.frequency.replace('ly', '')}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Next: {new Date(schedule.next_execution).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={schedule.status === 'active' ? 'default' : 'secondary'}>
                      {schedule.status}
                    </Badge>
                    {schedule.status === 'active' ? (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => pauseScheduleMutation.mutate(schedule.id)}
                      >
                        <Pause className="h-4 w-4" />
                      </Button>
                    ) : (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => resumeScheduleMutation.mutate(schedule.id)}
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive"
                      onClick={() => cancelScheduleMutation.mutate(schedule.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-6 text-center text-muted-foreground">
              <Calendar className="mx-auto mb-2 h-8 w-8 opacity-50" />
              <p>No active schedules</p>
              <p className="text-sm">Set up auto-invest to build wealth over time</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
