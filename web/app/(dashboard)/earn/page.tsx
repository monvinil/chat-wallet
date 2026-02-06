'use client';

import { useState } from 'react';
import {
  TrendingUp,
  Zap,
  Calendar,
  Loader2,
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

const frequencyLabels: Record<string, string> = {
  daily: 'day',
  weekly: 'week',
  biweekly: '2 weeks',
  monthly: 'month',
};

export default function EarnPage() {
  const { data: yieldStatus, isLoading: yieldLoading } = useYieldStatus();
  const { data: schedules, isLoading: schedulesLoading } = useSchedules();
  const { data: earnings, isLoading: earningsLoading } = useEarningsSummary();
  const { data: earningsHistory } = useEarningsHistory();
  const { data: balances } = useWalletBalances();

  const depositMutation = useYieldDeposit();
  const withdrawMutation = useYieldWithdraw();
  const createScheduleMutation = useCreateSchedule();
  const cancelScheduleMutation = useCancelSchedule();
  const pauseScheduleMutation = usePauseSchedule();
  const resumeScheduleMutation = useResumeSchedule();

  const [yieldDialogOpen, setYieldDialogOpen] = useState(false);
  const [dcaDialogOpen, setDcaDialogOpen] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelTargetId, setCancelTargetId] = useState<string | null>(null);
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

  const handleCancelSchedule = async () => {
    if (!cancelTargetId) return;
    await cancelScheduleMutation.mutateAsync(cancelTargetId);
    setCancelDialogOpen(false);
    setCancelTargetId(null);
  };

  // Transform earnings history into chart data
  const chartData = earningsHistory?.items?.map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    earnings: item.amount,
  })) || [];

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
          {chartData.length > 0 ? (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
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
                      borderRadius: '8px',
                    }}
                    wrapperClassName="!bg-card !border-border"
                  />
                  <Line
                    type="monotone"
                    dataKey="earnings"
                    stroke="var(--color-primary)"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex h-48 items-center justify-center text-muted-foreground">
              <p className="text-sm">No earnings data yet. Enable yield to start earning.</p>
            </div>
          )}
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
                      You&apos;ll buy ${dcaAmount} worth of {dcaToken} every {frequencyLabels[dcaFrequency]}.
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
                      ${schedule.amount} &rarr; {schedule.target_token}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Every {frequencyLabels[schedule.frequency] || schedule.frequency}
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
                        aria-label="Pause schedule"
                      >
                        <Pause className="h-4 w-4" />
                      </Button>
                    ) : (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => resumeScheduleMutation.mutate(schedule.id)}
                        aria-label="Resume schedule"
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive"
                      onClick={() => {
                        setCancelTargetId(schedule.id);
                        setCancelDialogOpen(true);
                      }}
                      aria-label="Cancel schedule"
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

      {/* Cancel Confirmation Dialog */}
      <Dialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancel Schedule</DialogTitle>
            <DialogDescription>
              Are you sure you want to cancel this auto-invest schedule? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setCancelDialogOpen(false)}>
              Keep Schedule
            </Button>
            <Button
              variant="destructive"
              onClick={handleCancelSchedule}
              disabled={cancelScheduleMutation.isPending}
            >
              {cancelScheduleMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Cancelling...
                </>
              ) : (
                'Cancel Schedule'
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
