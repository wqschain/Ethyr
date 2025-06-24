import React, { useState, useEffect } from 'react';
import { Web3 } from 'web3';
import { ShieldCheckIcon, ShieldExclamationIcon, ExclamationTriangleIcon } from '@heroicons/react/24/solid';
import ethyrLogo from '../icons/ethyrlogo2.svg';
import MetallicPaint, { parseLogoImage } from './components/MetallicPaint';
import NodeBackground from './components/NodeBackground';

declare const chrome: any;

interface TokenInfo {
  name: string;
  symbol: string;
  decimals: number;
  total_supply: number;
  market_cap: number;
  price_usd: number;
  price_eth: number;
  volume_24h: number;
  total_liquidity_eth: number;
  main_pool_address: string | null;
  dex_data: Array<{
    dex: string;
    pair_address: string;
    liquidity_eth: number;
    token_reserve: number;
    price_eth: number;
    price_usd: number;
  }>;
  holder_activity: {
    active_addresses: number;
    buy_sell_ratio: string;
    avg_transaction: number;
  };
  whale_analysis: {
    large_transactions: number;
    accumulation_events: number;
    disposal_events: number;
  };
  contract_interactions: {
    defi_interactions: number;
    unique_contracts: number;
    top_contracts: Array<{
      address: string;
      name: string;
      transaction_count: number;
      verified: boolean;
    }>;
  };
  trading_patterns: {
    avg_holding_time: string;
    active_pairs: number;
  };
}

interface TokenHolding {
  contract: string;
  symbol: string;
  name: string;
  balance: number;
}

interface WalletMetrics {
  balance: number;
  total_transactions: number;
  first_tx_timestamp: string | null;
  last_tx_timestamp: string | null;
  unique_interacted_addresses: number;
  incoming_tx_count: number;
  outgoing_tx_count: number;
  failed_tx_count: number;
  total_received_eth: number;
  total_sent_eth: number;
  avg_gas_used: number;
  total_gas_spent_eth: number;
  token_holdings: TokenHolding[];
  nft_holdings: number;
  nft_transactions: number;
  wallet_age_days: number;
}

interface DeFiProtocol {
  interaction_count: number;
  total_value: number;
  last_interaction: string | null;
}

interface DeFiActivity {
  protocols: { [key: string]: DeFiProtocol };
  total_interactions: number;
  total_value_locked: number;
  last_interaction: string | null;
}

interface ScanResult {
  type: string;
  risk_score: number;
  risk_tier: string;
  explanation: string[];
  summary: {
    verified: boolean;
    creator_address: string | null;
    total_transactions: number;
    unique_interactions: number;
    total_value: number;
    is_contract: boolean;
    contract_age_days: number | null;
    mint_events: number | null;
    burn_events: number | null;
    lp_locked: boolean | null;
  };
  features?: {
    verified_contract: boolean;
    owner_address: string | null;
    is_owner_deployer: boolean;
    has_mint_privileges: boolean;
    mint_event_count: number;
    honeypot_result: boolean;
    lp_locked: boolean;
    contract_age_days: number;
    burn_event_count: number;
    transfer_volume_24h: number;
    is_contract: boolean;
  };
  is_contract: boolean;
  is_token: boolean;
  token_info?: TokenInfo;
  wallet_metrics?: WalletMetrics;
  defi_activity?: DeFiActivity;
}

const App: React.FC = () => {
  const [address, setAddress] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'tokens' | 'defi'>('overview');
  const [imageData, setImageData] = useState<ImageData | null>(null);
  const [isScanning, setIsScanning] = useState(false);

  const isValidAddress = (addr: string) => {
    return Web3.utils.isAddress(addr);
  };

  const getRiskIcon = (tier: string) => {
    switch (tier) {
      case 'Safe':
        return <ShieldCheckIcon className="h-8 w-8 text-green-500" />;
      case 'Moderate Risk':
        return <ShieldExclamationIcon className="h-8 w-8 text-yellow-500" />;
      case 'High Risk':
        return <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />;
      default:
        return null;
    }
  };

  const formatDate = (timestamp: string | null) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleDateString();
  };

  const formatNumber = (num: number | null, decimals: number = 4) => {
    if (num === null || isNaN(num)) return 'N/A';
    
    const absNum = Math.abs(num);
    
    // Handle very small numbers
    if (absNum < 0.000001) {
      // For very small numbers, show up to 8 decimal places
      return num.toFixed(8);
    }
    
    // Handle large numbers with suffix
    if (absNum >= 1_000_000_000_000) {
      return `${(num / 1_000_000_000_000).toFixed(2)}T`;
    } else if (absNum >= 1_000_000_000) {
      return `${(num / 1_000_000_000).toFixed(2)}B`;
    } else if (absNum >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(2)}M`;
    } else if (absNum >= 1_000) {
      return `${(num / 1_000).toFixed(2)}K`;
    }
    
    // For numbers between 0.000001 and 1000, show appropriate decimals
    const decimalPlaces = Math.min(
      decimals,
      absNum < 1 ? 6 : // Show more decimals for small numbers
      absNum < 10 ? 4 : // Show fewer decimals as numbers get larger
      absNum < 100 ? 3 :
      2
    );
    
    return num.toFixed(decimalPlaces);
  };

  const formatSupply = (supply: number, decimals: number = 18) => {
    if (supply === null || isNaN(supply)) return 'N/A';
    
    // Convert from raw amount using decimals
    const actualSupply = supply / Math.pow(10, decimals);
    
    // For token supplies, we want to show the full number without decimals
    const absSupply = Math.abs(actualSupply);
    if (absSupply >= 1_000_000_000_000) {
      return `${(actualSupply / 1_000_000_000_000).toFixed(2)}T`;
    } else if (absSupply >= 1_000_000_000) {
      return `${(actualSupply / 1_000_000_000).toFixed(2)}B`;
    } else if (absSupply >= 1_000_000) {
      return `${(actualSupply / 1_000_000).toFixed(2)}M`;
    } else if (absSupply >= 1_000) {
      return `${(actualSupply / 1_000).toFixed(2)}K`;
    }
    
    // For smaller supplies, show the exact number
    return actualSupply.toLocaleString(undefined, {
      maximumFractionDigits: 0
    });
  };

  const handleScan = async () => {
    if (!isValidAddress(address)) {
      setError('Invalid Ethereum address');
      return;
    }
    
    setIsScanning(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ address }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze address');
      }

      const data = await response.json();
      setResult(data);
      setActiveTab('overview');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setTimeout(() => setIsScanning(false), 2000); // Add delay to allow animation to complete
    }
  };

  const renderWalletOverview = () => {
    if (!result?.wallet_metrics) return null;
    const m = result.wallet_metrics;

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="info-card">
            <h4 className="info-card-title">ETH Balance</h4>
            <p className="info-card-content">{formatNumber(m.balance)} ETH</p>
          </div>
          <div className="info-card">
            <h4 className="info-card-title">Wallet Age</h4>
            <p className="info-card-content">{m.wallet_age_days} days</p>
          </div>
        </div>

        <div className="info-card">
          <h4 className="info-card-title">Transaction Activity</h4>
          <div className="info-card-content space-y-2">
            <p>Total Transactions: {m.total_transactions}</p>
            <p>Incoming: {m.incoming_tx_count} | Outgoing: {m.outgoing_tx_count}</p>
            <p>Failed Transactions: {m.failed_tx_count}</p>
            <p>Unique Addresses: {m.unique_interacted_addresses}</p>
          </div>
        </div>

        <div className="info-card">
          <h4 className="info-card-title">Value Flow</h4>
          <div className="info-card-content space-y-2">
            <p>Total Received: {formatNumber(m.total_received_eth)} ETH</p>
            <p>Total Sent: {formatNumber(m.total_sent_eth)} ETH</p>
            <p>Gas Spent: {formatNumber(m.total_gas_spent_eth)} ETH</p>
          </div>
        </div>

        <div className="info-card">
          <h4 className="info-card-title">NFT Activity</h4>
          <div className="info-card-content space-y-2">
            <p>Current Holdings: {m.nft_holdings}</p>
            <p>Total Transactions: {m.nft_transactions}</p>
          </div>
        </div>

        <div className="info-card">
          <h4 className="info-card-title">Important Dates</h4>
          <div className="info-card-content">
            <p>First Transaction: {formatDate(m.first_tx_timestamp)}</p>
          </div>
        </div>
      </div>
    );
  };

  const renderTokenOverview = () => {
    if (!result?.token_info) return null;
    const t = result.token_info;

    return (
      <div className="space-y-4">
        <div className="info-card">
          <h4 className="info-card-title">Token Info</h4>
          <div className="info-card-content space-y-2">
            <p>Name: {t.name}</p>
            <p>Symbol: {t.symbol}</p>
            <p>Total Supply: {formatSupply(t.total_supply, t.decimals)}</p>
          </div>
        </div>

        <div className="info-card">
          <h4 className="info-card-title">Market Data</h4>
          <div className="info-card-content space-y-2">
            <p>Market Cap: ${formatNumber(t.market_cap)}</p>
            <p>Price: ${formatNumber(t.price_usd, 8)} ({formatNumber(t.price_eth, 8)} ETH)</p>
            <p>24h Volume: ${formatNumber(t.volume_24h)}</p>
          </div>
        </div>

        <div className="info-card">
          <h4 className="info-card-title">Trading Info</h4>
          <div className="info-card-content space-y-2">
            <p>Active Trading Pairs: {t.trading_patterns.active_pairs}</p>
            <p>Average Holding Time: {t.trading_patterns.avg_holding_time}</p>
            <p>Total Liquidity: {formatNumber(t.total_liquidity_eth)} ETH</p>
          </div>
        </div>

        <div className="info-card">
          <h4 className="info-card-title">Holder Activity</h4>
          <div className="info-card-content space-y-2">
            <p>Active Addresses: {t.holder_activity.active_addresses}</p>
            <p>Buy/Sell Ratio: {t.holder_activity.buy_sell_ratio}</p>
            <p>Average Transaction: {formatNumber(t.holder_activity.avg_transaction)} tokens</p>
          </div>
        </div>
      </div>
    );
  };

  const renderOverviewTab = () => {
    if (!result) return null;
    
    // First check if it's a contract
    if (result.is_contract) {
      // Then check if it's specifically a token
      if (result.is_token && result.token_info) {
        return renderTokenOverview();
      } else {
        // It's a contract but not a token
        return (
          <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold mb-2 text-gray-100">Contract Overview</h3>
            <div className="space-y-2 text-gray-300">
              <p>Contract Type: {result.type}</p>
              <p>Verified: {result.features?.verified_contract ? 'Yes' : 'No'}</p>
              <p>Age: {result.features?.contract_age_days || 0} days</p>
              <p>Creator: {result.features?.owner_address || 'Unknown'}</p>
              <p>Total Transactions: {formatNumber(result.summary?.total_transactions ?? null)}</p>
            </div>
          </div>
        );
      }
    } else {
      // It's a wallet
      return renderWalletOverview();
    }
  };

  const renderTokensTab = () => {
    if (!result) return null;

    if (result.is_token && result.token_info) {
      const t = result.token_info;
      
      return (
        <div className="space-y-4">
          {/* Holder Activity Section */}
          <div className="p-2 bg-gray-800 rounded-md border border-gray-700">
            <h4 className="text-sm font-medium text-gray-100">Holder Activity (24h)</h4>
            <div className="text-sm text-gray-300">
              <p>Active Addresses: {formatNumber(t.holder_activity?.active_addresses || 0)}</p>
              <p>Buy/Sell Ratio: {t.holder_activity?.buy_sell_ratio || '0:0'}</p>
              <p>Avg Transaction: {formatNumber(t.holder_activity?.avg_transaction || 0)} tokens</p>
            </div>
          </div>

          {/* Whale Analysis Section */}
          <div className="p-2 bg-gray-800 rounded-md border border-gray-700">
            <h4 className="text-sm font-medium text-gray-100">Whale Activity (24h)</h4>
            <div className="text-sm text-gray-300">
              <p>Large Transactions: {formatNumber(t.whale_analysis?.large_transactions || 0)}</p>
              <p>Whale Accumulation: {formatNumber(t.whale_analysis?.accumulation_events || 0)} events</p>
              <p>Whale Disposal: {formatNumber(t.whale_analysis?.disposal_events || 0)} events</p>
            </div>
          </div>

          {/* Contract Interactions Section */}
          <div className="p-2 bg-gray-800 rounded-md border border-gray-700">
            <h4 className="text-sm font-medium text-gray-100">Smart Contract Activity</h4>
            <div className="text-sm text-gray-300">
              <p>DeFi Interactions: {formatNumber(t.contract_interactions?.defi_interactions || 0)}</p>
              <p>Unique Contracts: {formatNumber(t.contract_interactions?.unique_contracts || 0)}</p>
              {t.contract_interactions?.top_contracts && t.contract_interactions.top_contracts.length > 0 && (
                <div className="mt-1">
                  <p className="text-xs text-gray-400">Top Contracts:</p>
                  <ul className="text-xs list-disc list-inside">
                    {t.contract_interactions.top_contracts.map((contract, idx) => (
                      <li key={idx}>
                        {contract.name} ({`${contract.address.slice(0, 6)}...${contract.address.slice(-4)}`}): {contract.transaction_count} txs
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Trading Patterns Section */}
          <div className="p-2 bg-gray-800 rounded-md border border-gray-700">
            <h4 className="text-sm font-medium text-gray-100">Trading Patterns</h4>
            <div className="text-sm text-gray-300">
              <p>Avg Holding Time: {t.trading_patterns?.avg_holding_time || '0s'}</p>
              <p>Active Trading Pairs: {formatNumber(t.trading_patterns?.active_pairs || 0)}</p>
            </div>
          </div>
        </div>
      );
    }

    // For non-token addresses, return null or a message
    return (
      <div className="text-sm text-gray-400 p-2">
        Token analysis is only available for ERC20 token contracts.
      </div>
    );
  };

  const renderDeFiTab = () => {
    if (!result) return null;

    if (result.is_token && result.token_info) {
      // For token contracts, show DEX info
      const t = result.token_info;

      return (
        <div className="space-y-4">
          <div className="p-2 bg-gray-800 rounded-md border border-gray-700">
            <h4 className="text-sm font-medium text-gray-100">DEX Overview</h4>
            <div className="text-sm text-gray-300">
              <p>Price: ${formatNumber(t.price_usd, 8)} (${formatNumber(t.price_eth, 8)} ETH)</p>
              <p>24h Volume: ${formatNumber(t.volume_24h)}</p>
              <p>Total Liquidity: {formatNumber(t.total_liquidity_eth)} ETH</p>
            </div>
          </div>

          <div className="p-2 bg-gray-800 rounded-md border border-gray-700">
            <h4 className="text-sm font-medium text-gray-100">Liquidity Info</h4>
            <div className="text-sm text-gray-300">
              <p>Liquidity Locked: {result.features?.lp_locked ? 'Yes' : 'No'}</p>
              {t.main_pool_address && (
                <p className="truncate">Main Pool: {t.main_pool_address}</p>
              )}
              {t.dex_data && t.dex_data.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium mb-1">DEX Distribution:</p>
                  {t.dex_data.map((dex, idx) => (
                    <div key={idx} className="text-xs">
                      {dex.dex}: {formatNumber(dex.liquidity_eth)} ETH
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    // For non-token addresses, return null or a message
    return (
      <div className="text-sm text-gray-400 p-2">
        DEX analysis is only available for ERC20 token contracts.
      </div>
    );
  };

  useEffect(() => {
    async function loadDefaultImage() {
      try {
        const response = await fetch(ethyrLogo);
        const blob = await response.blob();
        const file = new File([blob], "default.png", { type: blob.type });

        const parsedData = await parseLogoImage(file);
        setImageData(parsedData?.imageData ?? null);
      } catch (err) {
        console.error("Error loading default image:", err);
      }
    }

    loadDefaultImage();
  }, []);

  return (
    <div className="w-popup min-h-[400px] p-4 bg-gray-900 relative">
      <NodeBackground isScanning={isScanning} />
      
      <div className="flex flex-col items-center mb-6 relative z-10">
        <div className="relative w-40 h-40 flex items-center justify-center fade-in">
          <div className="w-36 h-36">
            {imageData && (
              <MetallicPaint 
                imageData={imageData}
                params={{
                  patternScale: 1.8,
                  refraction: 0.018,
                  edge: 1.2,
                  patternBlur: 0.001,
                  liquid: 0.04,
                  speed: 0.15
                }}
              />
            )}
          </div>
          <img 
            src={ethyrLogo}
            alt="Ethyr Logo"
            className="absolute inset-0 w-full h-full object-contain opacity-0 group-[.webgl-error]:opacity-100"
            onError={(e) => {
              e.currentTarget.style.opacity = "1";
            }}
          />
        </div>
        
        <div className="mt-4 fade-in fade-in-delay-1">
          <h1 className="text-3xl font-bold text-center chrome-text">
            Ethyr
          </h1>
        </div>
        
        <p className="text-gray-400 text-center mt-2 max-w-md fade-in fade-in-delay-2">
          Analyze Ethereum addresses, smart contracts, and tokens for security risks and detailed insights using advanced AI detection
        </p>
        
        <div className="space-y-4 w-full mt-6 fade-in fade-in-delay-3">
          <div>
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter Ethereum address"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-500"
            />
          </div>

          <button
            onClick={handleScan}
            disabled={isScanning || !address}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-400 relative overflow-hidden"
          >
            <span className={isScanning ? 'opacity-0' : 'opacity-100'}>
              Scan Address
            </span>
            {isScanning && (
              <span className="absolute inset-0 flex items-center justify-center">
                Scanning...
              </span>
            )}
          </button>

          {error && (
            <div className="p-3 bg-red-900/50 text-red-200 rounded-md border border-red-700">
              {error}
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold text-gray-100">
                    {result.is_token ? 'Token Contract' : result.is_contract ? 'Smart Contract' : 'Wallet'}
                  </h2>
                  <p className="text-sm text-gray-400">Risk Score: <span className="text-blue-400 font-medium">{(result.risk_score * 100).toFixed(1)}%</span></p>
                </div>
                {getRiskIcon(result.risk_tier)}
              </div>

              <div className="analysis-section">
                <h3 className="analysis-title">Analysis</h3>
                <div className="space-y-3">
                  {result.explanation.map((text, idx) => (
                    <p key={idx} className="analysis-text">{text}</p>
                  ))}
                </div>
              </div>

              <div className="flex space-x-2 border-b border-gray-700 mt-6">
                <button
                  className={`px-4 py-2 text-sm font-medium transition-colors duration-200 ${
                    activeTab === 'overview'
                      ? 'border-b-2 border-blue-500 text-blue-400'
                      : 'text-gray-400 hover:text-gray-300 hover:border-b-2 hover:border-gray-600'
                  }`}
                  onClick={() => setActiveTab('overview')}
                >
                  Overview
                </button>
                <button
                  className={`px-4 py-2 text-sm font-medium transition-colors duration-200 ${
                    activeTab === 'tokens'
                      ? 'border-b-2 border-blue-500 text-blue-400'
                      : 'text-gray-400 hover:text-gray-300 hover:border-b-2 hover:border-gray-600'
                  }`}
                  onClick={() => setActiveTab('tokens')}
                >
                  {result.is_token ? 'Holders' : 'Tokens'}
                </button>
                <button
                  className={`px-4 py-2 text-sm font-medium transition-colors duration-200 ${
                    activeTab === 'defi'
                      ? 'border-b-2 border-blue-500 text-blue-400'
                      : 'text-gray-400 hover:text-gray-300 hover:border-b-2 hover:border-gray-600'
                  }`}
                  onClick={() => setActiveTab('defi')}
                >
                  {result.is_token ? 'DEX Info' : 'DeFi'}
                </button>
              </div>

              <div className="mt-4 space-y-4">
                {activeTab === 'overview' && renderOverviewTab()}
                {activeTab === 'tokens' && renderTokensTab()}
                {activeTab === 'defi' && renderDeFiTab()}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App; 