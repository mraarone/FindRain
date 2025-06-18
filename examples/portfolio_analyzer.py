# examples/portfolio_analyzer.py
"""
Portfolio Analysis Example

Demonstrates portfolio analysis with AI insights and risk assessment.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np

from financial_platform_sdk import FinancialDataClient, AIAssistant

class PortfolioAnalyzer:
    """Advanced portfolio analyzer with AI insights"""
    
    def __init__(self, api_key: str):
        self.client = FinancialDataClient(api_key)
        self.ai_assistant = AIAssistant(self.client)
        
    async def analyze_portfolio(self, portfolio_id: str) -> Dict[str, Any]:
        """Comprehensive portfolio analysis"""
        # Get portfolio details
        portfolio = await self.client.get_portfolio(portfolio_id)
        
        # Analyze each holding
        analyses = []
        for holding in portfolio['holdings']:
            analysis = await self._analyze_holding(holding)
            analyses.append(analysis)
        
        # Calculate portfolio metrics
        metrics = self._calculate_portfolio_metrics(analyses)
        
        # Get AI insights
        ai_insights = await self._get_ai_insights(portfolio, metrics)
        
        # Risk assessment
        risk_assessment = await self._assess_risk(portfolio, analyses)
        
        return {
            'portfolio': portfolio,
            'holdings_analysis': analyses,
            'metrics': metrics,
            'ai_insights': ai_insights,
            'risk_assessment': risk_assessment,
            'recommendations': await self._generate_recommendations(portfolio, metrics, risk_assessment)
        }
        
    async def _analyze_holding(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual holding"""
        symbol = holding['symbol']
        
        # Get current data
        quote = await self.client.get_quote(symbol)
        
        # Get historical data for performance
        historical = await self.client.get_historical(
            symbol,
            start_date=holding['purchase_date'],
            end_date=datetime.utcnow()
        )
        
        # Calculate performance metrics
        current_value = holding['quantity'] * quote['price']
        cost_basis = holding['quantity'] * holding['purchase_price']
        
        return {
            'symbol': symbol,
            'current_price': quote['price'],
            'current_value': current_value,
            'cost_basis': cost_basis,
            'gain_loss': current_value - cost_basis,
            'gain_loss_pct': ((current_value - cost_basis) / cost_basis) * 100,
            'daily_change': quote['change'],
            'daily_change_pct': quote['changePercent'],
            'volatility': self._calculate_volatility(historical),
            'beta': await self._calculate_beta(symbol),
            'dividend_yield': quote.get('dividendYield', 0)
        }
        
    def _calculate_portfolio_metrics(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall portfolio metrics"""
        total_value = sum(a['current_value'] for a in analyses)
        total_cost = sum(a['cost_basis'] for a in analyses)
        
        # Position weights
        weights = {
            a['symbol']: a['current_value'] / total_value 
            for a in analyses
        }
        
        # Portfolio return
        portfolio_return = ((total_value - total_cost) / total_cost) * 100
        
        # Weighted metrics
        portfolio_beta = sum(
            weights[a['symbol']] * a['beta'] 
            for a in analyses
        )
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_return': portfolio_return,
            'portfolio_beta': portfolio_beta,
            'position_weights': weights,
            'diversification_score': self._calculate_diversification(weights),
            'concentration_risk': max(weights.values()) if weights else 0
        }
        
    async def _get_ai_insights(self, portfolio: Dict, metrics: Dict) -> Dict[str, Any]:
        """Get AI-powered insights"""
        prompt = f"""
        Analyze this investment portfolio:
        
        Portfolio Value: ${metrics['total_value']:,.2f}
        Total Return: {metrics['total_return']:.2f}%
        Beta: {metrics['portfolio_beta']:.2f}
        
        Top Holdings:
        {self._format_holdings(portfolio['holdings'][:5])}
        
        Provide insights on:
        1. Overall portfolio health
        2. Risk assessment
        3. Diversification quality
        4. Potential improvements
        5. Market outlook impact
        """
        
        response = await self.ai_assistant.analyze(prompt)
        return response
        
    def _calculate_volatility(self, historical: List[Dict]) -> float:
        """Calculate price volatility"""
        if len(historical) < 2:
            return 0
            
        prices = [h['close'] for h in historical]
        returns = pd.Series(prices).pct_change().dropna()
        return float(returns.std() * np.sqrt(252))  # Annualized volatility
        
    async def _calculate_beta(self, symbol: str) -> float:
        """Calculate beta against market"""
        # Get market data (using SPY as proxy)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=365)
        
        stock_data = await self.client.get_historical(symbol, start_date, end_date)
        market_data = await self.client.get_historical('SPY', start_date, end_date)
        
        if len(stock_data) < 30 or len(market_data) < 30:
            return 1.0  # Default beta
            
        # Calculate returns
        stock_returns = pd.Series([d['close'] for d in stock_data]).pct_change().dropna()
        market_returns = pd.Series([d['close'] for d in market_data]).pct_change().dropna()
        
        # Calculate beta
        covariance = stock_returns.cov(market_returns)
        market_variance = market_returns.var()
        
        return float(covariance / market_variance) if market_variance > 0 else 1.0
        
    def _calculate_diversification(self, weights: Dict[str, float]) -> float:
        """Calculate diversification score (0-100)"""
        if not weights:
            return 0
            
        # Use Herfindahl-Hirschman Index
        hhi = sum(w**2 for w in weights.values())
        
        # Convert to 0-100 scale (inverse of concentration)
        return (1 - hhi) * 100
        
    async def _assess_risk(self, portfolio: Dict, analyses: List[Dict]) -> Dict[str, Any]:
        """Comprehensive risk assessment"""
        # Calculate Value at Risk (VaR)
        portfolio_volatility = np.sqrt(sum(
            (a['current_value'] / sum(x['current_value'] for x in analyses))**2 * a['volatility']**2
            for a in analyses
        ))
        
        # 95% VaR (1.65 standard deviations)
        var_95 = portfolio_volatility * 1.65 * sum(a['current_value'] for a in analyses) / 100
        
        return {
            'portfolio_volatility': portfolio_volatility,
            'value_at_risk_95': var_95,
            'max_drawdown': await self._calculate_max_drawdown(portfolio),
            'correlation_risk': await self._assess_correlation_risk(portfolio),
            'sector_concentration': self._calculate_sector_concentration(portfolio),
            'risk_score': self._calculate_risk_score(portfolio_volatility, analyses)
        }
        
    async def _calculate_max_drawdown(self, portfolio: Dict) -> float:
        """Calculate maximum drawdown"""
        # Simplified - would need full historical portfolio values
        return 15.5  # Placeholder
        
    async def _assess_correlation_risk(self, portfolio: Dict) -> Dict[str, Any]:
        """Assess correlation between holdings"""
        # Simplified - would calculate correlation matrix
        return {
            'average_correlation': 0.65,
            'highly_correlated_pairs': [
                {'pair': ['AAPL', 'MSFT'], 'correlation': 0.85}
            ]
        }
        
    def _calculate_sector_concentration(self, portfolio: Dict) -> Dict[str, float]:
        """Calculate sector concentration"""
        # Simplified - would need sector data
        return {
            'Technology': 45.5,
            'Healthcare': 20.3,
            'Finance': 15.2,
            'Consumer': 10.5,
            'Other': 8.5
        }
        
    def _calculate_risk_score(self, volatility: float, analyses: List[Dict]) -> float:
        """Calculate overall risk score (0-100)"""
        # Factors: volatility, concentration, beta
        vol_score = min(volatility * 2, 50)  # Max 50 points
        
        # Concentration risk
        max_weight = max(a['current_value'] / sum(x['current_value'] for x in analyses) for a in analyses)
        concentration_score = max_weight * 30  # Max 30 points
        
        # Beta risk
        avg_beta = sum(a['beta'] * a['current_value'] for a in analyses) / sum(a['current_value'] for a in analyses)
        beta_score = min(abs(avg_beta - 1) * 20, 20)  # Max 20 points
        
        return vol_score + concentration_score + beta_score
        
    async def _generate_recommendations(self, portfolio: Dict, metrics: Dict, risk: Dict) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check concentration
        if metrics['concentration_risk'] > 0.25:
            recommendations.append({
                'type': 'diversification',
                'priority': 'high',
                'action': 'Reduce position concentration',
                'details': 'Consider reducing positions that exceed 25% of portfolio'
            })
            
        # Check risk score
        if risk['risk_score'] > 70:
            recommendations.append({
                'type': 'risk_reduction',
                'priority': 'high',
                'action': 'Reduce portfolio risk',
                'details': 'Consider adding defensive positions or reducing volatile holdings'
            })
            
        # Get AI recommendations
        ai_recs = await self._get_ai_recommendations(portfolio, metrics, risk)
        recommendations.extend(ai_recs)
        
        return recommendations
        
    async def _get_ai_recommendations(self, portfolio: Dict, metrics: Dict, risk: Dict) -> List[Dict[str, Any]]:
        """Get AI-powered recommendations"""
        prompt = f"""
        Based on this portfolio analysis:
        - Total Return: {metrics['total_return']:.2f}%
        - Risk Score: {risk['risk_score']:.1f}/100
        - Volatility: {risk['portfolio_volatility']:.2f}%
        - Concentration: Top position is {metrics['concentration_risk']*100:.1f}% of portfolio
        
        Provide 3 specific, actionable recommendations to improve this portfolio.
        """
        
        response = await self.ai_assistant.analyze(prompt)
        
        # Parse AI response into structured recommendations
        # This is simplified - would need proper parsing
        return [
            {
                'type': 'ai_suggestion',
                'priority': 'medium',
                'action': 'AI-generated recommendation',
                'details': response.get('recommendation', 'See AI analysis')
            }
        ]
        
    def _format_holdings(self, holdings: List[Dict]) -> str:
        """Format holdings for display"""
        lines = []
        for h in holdings:
            lines.append(f"- {h['symbol']}: {h['quantity']} shares @ ${h['purchase_price']}")
        return '\n'.join(lines)


