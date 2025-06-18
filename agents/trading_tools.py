from typing import Dict, Any, List, Optional
from langchain_community.tools import BaseTool
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class MarketAnalysisTool(BaseTool):
    name: str = "market_analysis"
    description: str = "Analyze market conditions and trends for given assets using quantitative methods"
    
    def _run(self, assets: List[str], timeframe: str = "1d") -> str:
        """Analyze market conditions for given assets using statistical methods."""
        import json  # Add import to top of function
        
        try:
            analysis_results = {}
            
            for asset in assets:
                # Get market data
                ticker = yf.Ticker(asset)
                hist = ticker.history(period="1y")
                
                if hist.empty:
                    analysis_results[asset] = {"error": f"No data available for {asset}"}
                    continue
                
                # Calculate statistical metrics
                returns = hist['Close'].pct_change().dropna()
                
                # Basic statistics
                mean_return = returns.mean()
                std_return = returns.std()
                skewness = stats.skew(returns)
                kurtosis = stats.kurtosis(returns)
                
                # Volatility analysis
                rolling_vol = returns.rolling(window=20).std()
                current_vol = rolling_vol.iloc[-1]
                vol_percentile = (rolling_vol < current_vol).mean()
                
                # Trend analysis
                sma_20 = hist['Close'].rolling(window=20).mean()
                sma_50 = hist['Close'].rolling(window=50).mean()
                current_price = hist['Close'].iloc[-1]
                
                # Technical indicators
                rsi = self._calculate_rsi(hist['Close'])
                macd, signal = self._calculate_macd(hist['Close'])
                
                # Risk metrics
                var_95 = np.percentile(returns, 5)
                max_drawdown = self._calculate_max_drawdown(hist['Close'])
                
                analysis_results[asset] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "current_price": float(current_price),
                    "statistical_metrics": {
                        "mean_return": float(mean_return),
                        "volatility": float(std_return),
                        "skewness": float(skewness),
                        "kurtosis": float(kurtosis),
                        "var_95": float(var_95),
                        "max_drawdown": float(max_drawdown)
                    },
                    "trend_analysis": {
                        "sma_20": float(sma_20.iloc[-1]),
                        "sma_50": float(sma_50.iloc[-1]),
                        "trend_direction": "bullish" if sma_20.iloc[-1] > sma_50.iloc[-1] else "bearish",
                        "price_vs_sma20": "above" if current_price > sma_20.iloc[-1] else "below"
                    },
                    "technical_indicators": {
                        "rsi": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None,
                        "macd": float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None,
                        "macd_signal": float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else None
                    },
                    "volatility_analysis": {
                        "current_volatility": float(current_vol),
                        "volatility_percentile": float(vol_percentile),
                        "volatility_regime": "high" if vol_percentile > 0.8 else "low" if vol_percentile < 0.2 else "normal"
                    },
                    "recommendations": self._generate_recommendations(
                        mean_return, std_return, rsi.iloc[-1], 
                        sma_20.iloc[-1], sma_50.iloc[-1], current_price
                    )
                }
            
            return json.dumps(analysis_results, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Market analysis failed: {str(e)}"})
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Calculate MACD and signal line."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        return macd, signal_line
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown."""
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak
        return float(drawdown.min())
    
    def _generate_recommendations(self, mean_return: float, std_return: float, rsi: float, 
                                 sma_20: float, sma_50: float, current_price: float) -> List[str]:
        """Generate trading recommendations based on analysis."""
        recommendations = []
        
        # RSI analysis
        if rsi and rsi < 30:
            recommendations.append("RSI indicates oversold conditions - potential buying opportunity")
        elif rsi and rsi > 70:
            recommendations.append("RSI indicates overbought conditions - consider taking profits")
        
        # Trend analysis
        if sma_20 > sma_50:
            recommendations.append("Uptrend confirmed by moving averages")
        else:
            recommendations.append("Downtrend confirmed by moving averages")
        
        # Volatility analysis
        if std_return > 0.02:  # High volatility
            recommendations.append("High volatility detected - consider position sizing")
        
        # Return analysis
        if mean_return > 0:
            recommendations.append("Positive expected returns based on historical data")
        else:
            recommendations.append("Negative expected returns - exercise caution")
        
        return recommendations
    
    async def _arun(self, assets: List[str], timeframe: str = "1d") -> str:
        """Async implementation of market analysis."""
        return self._run(assets, timeframe)

class RiskAssessmentTool(BaseTool):
    name: str = "risk_assessment"
    description: str = "Assess risk levels for trading strategies using quantitative risk models"
    
    def _run(self, strategy: Dict[str, Any] = None, market_conditions: Dict[str, Any] = None) -> str:
        """Assess risk for a trading strategy using advanced risk metrics."""
        import json  # Move import to top of function
        
        try:
            # Handle case where arguments might be passed differently by LangChain
            if strategy is None and market_conditions is None:
                # Called without arguments, use defaults
                strategy = {"assets": ["BTC", "ETH"], "position_size": 0.1, "stop_loss": 0.05, "take_profit": 0.1}
                market_conditions = {}
            elif isinstance(strategy, str):
                # Called with a single string argument (might be from LangChain)
                try:
                    strategy = json.loads(strategy)
                    market_conditions = {}
                except:
                    strategy = {"assets": ["BTC", "ETH"], "position_size": 0.1, "stop_loss": 0.05, "take_profit": 0.1}
                    market_conditions = {}
            elif strategy is None:
                strategy = {"assets": ["BTC", "ETH"], "position_size": 0.1, "stop_loss": 0.05, "take_profit": 0.1}
            elif market_conditions is None:
                market_conditions = {}
            
            # Handle case where arguments are missing or empty
            if not strategy:
                strategy = {}
            if not market_conditions:
                market_conditions = {}
            
            # Extract strategy parameters with defaults
            assets = strategy.get('assets', ["BTC", "ETH"])
            position_size = strategy.get('position_size', 0.1)
            stop_loss = strategy.get('stop_loss', 0.05)
            take_profit = strategy.get('take_profit', 0.1)
            
            # Ensure assets is a list
            if not isinstance(assets, list):
                if isinstance(assets, str):
                    assets = [assets]
                else:
                    assets = ["BTC", "ETH"]
            
            risk_metrics = {}
            
            for asset in assets:
                # Get historical data for risk calculation
                ticker = yf.Ticker(asset)
                hist = ticker.history(period="1y")
                
                if hist.empty:
                    risk_metrics[asset] = {"error": f"No data available for {asset}"}
                    continue
                
                returns = hist['Close'].pct_change().dropna()
                current_price = hist['Close'].iloc[-1]
                
                # Calculate risk metrics
                volatility = returns.std()
                var_95 = np.percentile(returns, 5)
                var_99 = np.percentile(returns, 1)
                expected_shortfall = returns[returns <= var_95].mean()
                
                # Position-specific risk
                position_value = current_price * position_size
                max_loss = position_value * stop_loss
                potential_gain = position_value * take_profit
                
                # Risk-adjusted metrics
                sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0
                sortino_ratio = returns.mean() / returns[returns < 0].std() if returns[returns < 0].std() > 0 else 0
                
                # Correlation with market (if multiple assets)
                if len(assets) > 1:
                    try:
                        market_returns = yf.Ticker("^GSPC").history(period="1y")['Close'].pct_change().dropna()
                        correlation = returns.corr(market_returns)
                    except:
                        correlation = 0
                else:
                    correlation = 0
                
                risk_metrics[asset] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "risk_metrics": {
                        "volatility": float(volatility),
                        "var_95": float(var_95),
                        "var_99": float(var_99),
                        "expected_shortfall": float(expected_shortfall),
                        "sharpe_ratio": float(sharpe_ratio),
                        "sortino_ratio": float(sortino_ratio),
                        "market_correlation": float(correlation)
                    },
                    "position_risk": {
                        "position_value": float(position_value),
                        "max_loss": float(max_loss),
                        "potential_gain": float(potential_gain),
                        "risk_reward_ratio": float(potential_gain / max_loss) if max_loss > 0 else 0
                    },
                    "risk_assessment": {
                        "overall_risk": self._calculate_overall_risk(volatility, var_95, correlation),
                        "risk_level": self._categorize_risk_level(volatility, var_95),
                        "recommendations": self._generate_risk_recommendations(
                            volatility, var_95, sharpe_ratio, stop_loss, take_profit
                        )
                    }
                }
            
            return json.dumps(risk_metrics, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Risk assessment failed: {str(e)}"})
    
    def _calculate_overall_risk(self, volatility: float, var_95: float, correlation: float) -> float:
        """Calculate overall risk score (0-1, higher is riskier)."""
        # Normalize metrics to 0-1 scale
        vol_score = min(volatility * 10, 1.0)  # Scale volatility
        var_score = min(abs(var_95) * 5, 1.0)  # Scale VaR
        corr_score = abs(correlation)  # Correlation impact
        
        # Weighted average
        overall_risk = (0.4 * vol_score + 0.4 * var_score + 0.2 * corr_score)
        return float(overall_risk)
    
    def _categorize_risk_level(self, volatility: float, var_95: float) -> str:
        """Categorize risk level based on volatility and VaR."""
        if volatility < 0.01 and abs(var_95) < 0.02:
            return "low"
        elif volatility < 0.02 and abs(var_95) < 0.04:
            return "moderate"
        else:
            return "high"
    
    def _generate_risk_recommendations(self, volatility: float, var_95: float, 
                                     sharpe_ratio: float, stop_loss: float, take_profit: float) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        if volatility > 0.02:
            recommendations.append("High volatility detected - consider reducing position size")
        
        if abs(var_95) > 0.03:
            recommendations.append("High VaR - implement strict stop-loss orders")
        
        if sharpe_ratio < 0.5:
            recommendations.append("Low risk-adjusted returns - reconsider strategy")
        
        if stop_loss > 0.1:
            recommendations.append("Wide stop-loss - consider tighter risk management")
        
        if take_profit / stop_loss < 1.5:
            recommendations.append("Poor risk-reward ratio - adjust take-profit levels")
        
        return recommendations
    
    async def _arun(self, strategy: Dict[str, Any] = None, market_conditions: Dict[str, Any] = None) -> str:
        """Async implementation of risk assessment with flexible input handling."""
        import json  # Move import to top of function
        
        # Handle case where arguments might be passed differently by LangChain
        if strategy is None and market_conditions is None:
            # Called without arguments, use defaults
            strategy = {"assets": ["BTC", "ETH"], "position_size": 0.1, "stop_loss": 0.05, "take_profit": 0.1}
            market_conditions = {}
        elif isinstance(strategy, str):
            # Called with a single string argument (might be from LangChain)
            try:
                strategy = json.loads(strategy)
                market_conditions = {}
            except:
                strategy = {"assets": ["BTC", "ETH"], "position_size": 0.1, "stop_loss": 0.05, "take_profit": 0.1}
                market_conditions = {}
        elif strategy is None:
            strategy = {"assets": ["BTC", "ETH"], "position_size": 0.1, "stop_loss": 0.05, "take_profit": 0.1}
        elif market_conditions is None:
            market_conditions = {}
        
        return self._run(strategy, market_conditions)

class TradeExecutionTool(BaseTool):
    name: str = "trade_execution"
    description: str = "Execute trades based on strategy and risk assessment"
    
    def _run(self, strategy: Dict[str, Any], risk_assessment: Dict[str, Any]) -> str:
        """Execute trades based on strategy and risk assessment."""
        import json  # Add import to top of function
        
        # This would typically connect to a trading platform API
        # For now, return mock execution with enhanced analysis
        execution = {
            "strategy": strategy,
            "risk_assessment": risk_assessment,
            "timestamp": datetime.utcnow().isoformat(),
            "execution": {
                "status": "success",
                "orders": [
                    {
                        "asset": "BTC",
                        "type": "buy",
                        "amount": 0.1,
                        "price": 50000,
                        "risk_score": 0.35,
                        "expected_return": 0.08
                    }
                ],
                "total_value": 5000,
                "fees": 25,
                "risk_metrics": {
                    "portfolio_var": 0.025,
                    "max_drawdown": 0.15,
                    "sharpe_ratio": 1.2
                }
            }
        }
        return json.dumps(execution, indent=2)
    
    async def _arun(self, strategy: Dict[str, Any], risk_assessment: Dict[str, Any]) -> str:
        """Async implementation of trade execution."""
        return self._run(strategy, risk_assessment)

class PortfolioAnalysisTool(BaseTool):
    name: str = "portfolio_analysis"
    description: str = "Analyze current portfolio performance and composition using quantitative methods"
    
    def _run(self, portfolio_id: str) -> str:
        """Analyze portfolio performance with advanced metrics."""
        import json  # Add import to top of function
        
        try:
            # Mock portfolio data - in real implementation, this would come from a database
            portfolio_data = {
                "holdings": [
                    {"asset": "BTC", "amount": 0.5, "value": 25000, "allocation": 0.25},
                    {"asset": "ETH", "amount": 5.0, "value": 75000, "allocation": 0.75}
                ],
                "total_value": 100000
            }
            
            # Calculate portfolio metrics
            returns_data = {}
            for holding in portfolio_data["holdings"]:
                asset = holding["asset"]
                ticker = yf.Ticker(asset)
                hist = ticker.history(period="1y")
                
                if not hist.empty:
                    returns = hist['Close'].pct_change().dropna()
                    returns_data[asset] = {
                        "returns": returns,
                        "weight": holding["allocation"]
                    }
            
            # Portfolio-level calculations
            if returns_data:
                # Weighted portfolio returns
                portfolio_returns = pd.Series(0.0, index=next(iter(returns_data.values()))["returns"].index)
                for asset, data in returns_data.items():
                    portfolio_returns += data["returns"] * data["weight"]
                
                # Portfolio metrics
                portfolio_volatility = portfolio_returns.std()
                portfolio_sharpe = portfolio_returns.mean() / portfolio_returns.std() if portfolio_returns.std() > 0 else 0
                portfolio_var = np.percentile(portfolio_returns, 5)
                portfolio_max_dd = self._calculate_max_drawdown(portfolio_returns.cumsum())
                
                # Diversification analysis
                if len(returns_data) > 1:
                    returns_df = pd.DataFrame({asset: data["returns"] for asset, data in returns_data.items()})
                    correlation_matrix = returns_df.corr()
                    avg_correlation = (correlation_matrix.sum().sum() - len(correlation_matrix)) / (len(correlation_matrix) ** 2 - len(correlation_matrix))
                else:
                    avg_correlation = 1.0
                
                analysis = {
                    "portfolio_id": portfolio_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "performance": {
                        "total_value": portfolio_data["total_value"],
                        "daily_change": float(portfolio_returns.iloc[-1]) if len(portfolio_returns) > 0 else 0,
                        "monthly_change": float(portfolio_returns.tail(30).sum()) if len(portfolio_returns) >= 30 else 0,
                        "yearly_change": float(portfolio_returns.sum()) if len(portfolio_returns) > 0 else 0,
                        "volatility": float(portfolio_volatility),
                        "sharpe_ratio": float(portfolio_sharpe),
                        "var_95": float(portfolio_var),
                        "max_drawdown": float(portfolio_max_dd),
                        "avg_correlation": float(avg_correlation)
                    },
                    "holdings": portfolio_data["holdings"],
                    "diversification_score": self._calculate_diversification_score(avg_correlation, len(returns_data)),
                    "recommendations": self._generate_portfolio_recommendations(
                        portfolio_sharpe, portfolio_volatility, avg_correlation, portfolio_data["holdings"]
                    )
                }
            else:
                analysis = {
                    "portfolio_id": portfolio_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": "Unable to calculate portfolio metrics - insufficient data"
                }
            
            return json.dumps(analysis, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Portfolio analysis failed: {str(e)}"})
    
    def _calculate_max_drawdown(self, cumulative_returns: pd.Series) -> float:
        """Calculate maximum drawdown from cumulative returns."""
        peak = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - peak) / peak
        return float(drawdown.min())
    
    def _calculate_diversification_score(self, avg_correlation: float, num_assets: int) -> float:
        """Calculate diversification score (0-1, higher is better diversified)."""
        # Lower correlation and more assets = better diversification
        correlation_penalty = 1 - abs(avg_correlation)
        asset_diversity = min(num_assets / 10, 1.0)  # Normalize to 0-1
        return float((correlation_penalty + asset_diversity) / 2)
    
    def _generate_portfolio_recommendations(self, sharpe_ratio: float, volatility: float, 
                                          avg_correlation: float, holdings: List[Dict]) -> List[str]:
        """Generate portfolio optimization recommendations."""
        recommendations = []
        
        if sharpe_ratio < 0.5:
            recommendations.append("Low risk-adjusted returns - consider rebalancing portfolio")
        
        if volatility > 0.02:
            recommendations.append("High portfolio volatility - consider adding defensive assets")
        
        if avg_correlation > 0.7:
            recommendations.append("High asset correlation - consider diversifying across asset classes")
        
        if len(holdings) < 3:
            recommendations.append("Low asset count - consider adding more positions for diversification")
        
        return recommendations
    
    async def _arun(self, portfolio_id: str) -> str:
        """Async implementation of portfolio analysis."""
        return self._run(portfolio_id) 