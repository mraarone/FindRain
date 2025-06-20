# api/utils/greeks.py
"""
Greeks calculation engine for options pricing and risk analysis.
Implements Black-Scholes model and various numerical methods for accurate Greeks computation.
"""

import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize_scalar, brentq
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class OptionParameters:
    """Parameters for option calculations"""
    spot_price: float
    strike_price: float
    time_to_expiry: float  # In years
    volatility: float      # Annualized
    risk_free_rate: float
    dividend_yield: float = 0.0
    option_type: str = 'call'  # 'call' or 'put'
    
    def validate(self):
        """Validate parameters"""
        if self.spot_price <= 0:
            raise ValueError("Spot price must be positive")
        if self.strike_price <= 0:
            raise ValueError("Strike price must be positive")
        if self.time_to_expiry < 0:
            raise ValueError("Time to expiry cannot be negative")
        if self.volatility < 0:
            raise ValueError("Volatility cannot be negative")
        if self.option_type not in ['call', 'put']:
            raise ValueError("Option type must be 'call' or 'put'")

@dataclass
class Greeks:
    """Container for option Greeks"""
    price: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    # Second-order Greeks
    vanna: Optional[float] = None
    charm: Optional[float] = None
    vomma: Optional[float] = None
    veta: Optional[float] = None
    speed: Optional[float] = None
    zomma: Optional[float] = None
    color: Optional[float] = None
    ultima: Optional[float] = None
    # Other metrics
    lambda_: Optional[float] = None  # Leverage
    dual_delta: Optional[float] = None
    dual_gamma: Optional[float] = None

class GreeksCalculator:
    """Main Greeks calculation engine"""
    
    def __init__(self, precision: int = 6):
        self.precision = precision
        
    def calculate_greeks(
        self,
        params: OptionParameters,
        calculate_second_order: bool = False,
        method: str = 'analytical'
    ) -> Greeks:
        """
        Calculate option Greeks using specified method.
        
        Args:
            params: Option parameters
            calculate_second_order: Whether to calculate second-order Greeks
            method: 'analytical' or 'numerical'
            
        Returns:
            Greeks object with calculated values
        """
        params.validate()
        
        if method == 'analytical':
            greeks = self._calculate_analytical_greeks(params)
        else:
            greeks = self._calculate_numerical_greeks(params)
            
        if calculate_second_order:
            self._add_second_order_greeks(greeks, params)
            
        return greeks
    
    def _calculate_analytical_greeks(self, params: OptionParameters) -> Greeks:
        """Calculate Greeks using analytical Black-Scholes formulas"""
        S = params.spot_price
        K = params.strike_price
        T = params.time_to_expiry
        r = params.risk_free_rate
        q = params.dividend_yield
        sigma = params.volatility
        
        # Handle edge cases
        if T == 0:
            return self._calculate_expiry_greeks(params)
        
        if sigma == 0:
            return self._calculate_zero_vol_greeks(params)
        
        # Calculate d1 and d2
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Pre-calculate common terms
        exp_qT = np.exp(-q * T)
        exp_rT = np.exp(-r * T)
        sqrt_T = np.sqrt(T)
        
        # Calculate option price
        if params.option_type == 'call':
            price = S * exp_qT * norm.cdf(d1) - K * exp_rT * norm.cdf(d2)
            delta = exp_qT * norm.cdf(d1)
            theta_base = (-S * norm.pdf(d1) * sigma * exp_qT / (2 * sqrt_T)
                         - r * K * exp_rT * norm.cdf(d2)
                         + q * S * exp_qT * norm.cdf(d1))
        else:  # put
            price = K * exp_rT * norm.cdf(-d2) - S * exp_qT * norm.cdf(-d1)
            delta = -exp_qT * norm.cdf(-d1)
            theta_base = (-S * norm.pdf(d1) * sigma * exp_qT / (2 * sqrt_T)
                         + r * K * exp_rT * norm.cdf(-d2)
                         - q * S * exp_qT * norm.cdf(-d1))
        
        # Common Greeks
        gamma = norm.pdf(d1) * exp_qT / (S * sigma * sqrt_T)
        vega = S * norm.pdf(d1) * sqrt_T * exp_qT / 100  # Divided by 100 for 1% change
        theta = theta_base / 365  # Convert to per day
        
        # Rho (per 1% change)
        if params.option_type == 'call':
            rho = K * T * exp_rT * norm.cdf(d2) / 100
        else:
            rho = -K * T * exp_rT * norm.cdf(-d2) / 100
        
        # Lambda (leverage)
        lambda_ = delta * S / price if price != 0 else 0
        
        return Greeks(
            price=round(price, self.precision),
            delta=round(delta, self.precision),
            gamma=round(gamma, self.precision),
            theta=round(theta, self.precision),
            vega=round(vega, self.precision),
            rho=round(rho, self.precision),
            lambda_=round(lambda_, self.precision)
        )
    
    def _calculate_numerical_greeks(self, params: OptionParameters) -> Greeks:
        """Calculate Greeks using finite difference method"""
        # Base price
        price = self._black_scholes_price(params)
        
        # Small changes for finite differences
        h_price = params.spot_price * 0.001  # 0.1% change
        h_vol = 0.001  # 0.1% vol change
        h_time = 1 / 365  # 1 day
        h_rate = 0.0001  # 1 basis point
        
        # Delta - first derivative with respect to spot
        params_up = OptionParameters(**params.__dict__)
        params_up.spot_price += h_price
        price_up = self._black_scholes_price(params_up)
        
        params_down = OptionParameters(**params.__dict__)
        params_down.spot_price -= h_price
        price_down = self._black_scholes_price(params_down)
        
        delta = (price_up - price_down) / (2 * h_price)
        
        # Gamma - second derivative with respect to spot
        gamma = (price_up - 2 * price + price_down) / (h_price ** 2)
        
        # Theta - derivative with respect to time
        if params.time_to_expiry > h_time:
            params_theta = OptionParameters(**params.__dict__)
            params_theta.time_to_expiry -= h_time
            price_theta = self._black_scholes_price(params_theta)
            theta = (price_theta - price) / 365  # Per day
        else:
            theta = 0
        
        # Vega - derivative with respect to volatility
        params_vega = OptionParameters(**params.__dict__)
        params_vega.volatility += h_vol
        price_vega = self._black_scholes_price(params_vega)
        vega = (price_vega - price) / 100  # Per 1% change
        
        # Rho - derivative with respect to interest rate
        params_rho = OptionParameters(**params.__dict__)
        params_rho.risk_free_rate += h_rate
        price_rho = self._black_scholes_price(params_rho)
        rho = (price_rho - price) / 100  # Per 1% change
        
        # Lambda
        lambda_ = delta * params.spot_price / price if price != 0 else 0
        
        return Greeks(
            price=round(price, self.precision),
            delta=round(delta, self.precision),
            gamma=round(gamma, self.precision),
            theta=round(theta, self.precision),
            vega=round(vega, self.precision),
            rho=round(rho, self.precision),
            lambda_=round(lambda_, self.precision)
        )
    
    def _add_second_order_greeks(self, greeks: Greeks, params: OptionParameters):
        """Calculate and add second-order Greeks"""
        S = params.spot_price
        K = params.strike_price
        T = params.time_to_expiry
        r = params.risk_free_rate
        q = params.dividend_yield
        sigma = params.volatility
        
        if T == 0 or sigma == 0:
            return
        
        # Recalculate d1 and d2
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        exp_qT = np.exp(-q * T)
        sqrt_T = np.sqrt(T)
        
        # Vanna - derivative of delta with respect to volatility
        greeks.vanna = -exp_qT * norm.pdf(d1) * d2 / sigma
        
        # Charm (delta decay) - derivative of delta with respect to time
        if params.option_type == 'call':
            greeks.charm = exp_qT * (q * norm.cdf(d1) - norm.pdf(d1) * 
                                    (2 * (r - q) * T - d2 * sigma * sqrt_T) / 
                                    (2 * T * sigma * sqrt_T)) / 365
        else:
            greeks.charm = exp_qT * (-q * norm.cdf(-d1) - norm.pdf(d1) * 
                                     (2 * (r - q) * T - d2 * sigma * sqrt_T) / 
                                     (2 * T * sigma * sqrt_T)) / 365
        
        # Vomma (volga) - derivative of vega with respect to volatility
        greeks.vomma = greeks.vega * d1 * d2 / (sigma * 100)
        
        # Veta - derivative of vega with respect to time
        greeks.veta = -S * exp_qT * norm.pdf(d1) * sqrt_T * (
            q + (r - q) * d1 / (sigma * sqrt_T) - 
            (1 + d1 * d2) / (2 * T)
        ) / (100 * 365)
        
        # Speed - third derivative with respect to spot
        greeks.speed = -gamma * (1 + d1 / (sigma * sqrt_T)) / S
        
        # Zomma - derivative of gamma with respect to volatility
        greeks.zomma = gamma * (d1 * d2 - 1) / sigma
        
        # Color (gamma decay) - derivative of gamma with respect to time
        greeks.color = exp_qT * norm.pdf(d1) / (2 * S * T * sigma * sqrt_T) * (
            2 * q * T + 1 + d1 * (2 * (r - q) * T - d2 * sigma * sqrt_T) / (sigma * sqrt_T)
        ) / 365
        
        # Ultima - third derivative with respect to volatility
        greeks.ultima = -greeks.vega * (d1 * d2 * (1 - d1 * d2) + d1 ** 2 + d2 ** 2) / (sigma ** 2 * 100)
        
        # Dual delta - derivative with respect to strike
        if params.option_type == 'call':
            greeks.dual_delta = -np.exp(-r * T) * norm.cdf(d2)
        else:
            greeks.dual_delta = np.exp(-r * T) * norm.cdf(-d2)
        
        # Dual gamma - second derivative with respect to strike
        greeks.dual_gamma = np.exp(-r * T) * norm.pdf(d2) / (K * sigma * sqrt_T)
        
        # Round all second-order Greeks
        for attr in ['vanna', 'charm', 'vomma', 'veta', 'speed', 'zomma', 'color', 'ultima', 'dual_delta', 'dual_gamma']:
            value = getattr(greeks, attr)
            if value is not None:
                setattr(greeks, attr, round(value, self.precision))
    
    def _black_scholes_price(self, params: OptionParameters) -> float:
        """Calculate Black-Scholes option price"""
        S = params.spot_price
        K = params.strike_price
        T = params.time_to_expiry
        r = params.risk_free_rate
        q = params.dividend_yield
        sigma = params.volatility
        
        if T == 0:
            if params.option_type == 'call':
                return max(S - K, 0)
            else:
                return max(K - S, 0)
        
        if sigma == 0:
            if params.option_type == 'call':
                return max(S * np.exp(-q * T) - K * np.exp(-r * T), 0)
            else:
                return max(K * np.exp(-r * T) - S * np.exp(-q * T), 0)
        
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if params.option_type == 'call':
            price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
        
        return price
    
    def _calculate_expiry_greeks(self, params: OptionParameters) -> Greeks:
        """Calculate Greeks at expiration"""
        S = params.spot_price
        K = params.strike_price
        
        if params.option_type == 'call':
            price = max(S - K, 0)
            delta = 1.0 if S > K else 0.0
        else:
            price = max(K - S, 0)
            delta = -1.0 if S < K else 0.0
        
        return Greeks(
            price=price,
            delta=delta,
            gamma=0.0,
            theta=0.0,
            vega=0.0,
            rho=0.0,
            lambda_=0.0
        )
    
    def _calculate_zero_vol_greeks(self, params: OptionParameters) -> Greeks:
        """Calculate Greeks when volatility is zero"""
        S = params.spot_price
        K = params.strike_price
        T = params.time_to_expiry
        r = params.risk_free_rate
        q = params.dividend_yield
        
        forward = S * np.exp((r - q) * T)
        discount = np.exp(-r * T)
        
        if params.option_type == 'call':
            if forward > K:
                price = (forward - K) * discount
                delta = np.exp(-q * T)
                rho = -T * price / 100
            else:
                price = 0
                delta = 0
                rho = 0
        else:
            if forward < K:
                price = (K - forward) * discount
                delta = -np.exp(-q * T)
                rho = T * price / 100
            else:
                price = 0
                delta = 0
                rho = 0
        
        return Greeks(
            price=price,
            delta=delta,
            gamma=0.0,
            theta=-r * price / 365 if price > 0 else 0.0,
            vega=0.0,
            rho=rho,
            lambda_=delta * S / price if price > 0 else 0.0
        )
    
    def calculate_implied_volatility(
        self,
        option_price: float,
        params: OptionParameters,
        method: str = 'newton',
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ) -> float:
        """
        Calculate implied volatility from option price.
        
        Args:
            option_price: Market price of the option
            params: Option parameters (volatility will be solved for)
            method: 'newton' or 'brent'
            max_iterations: Maximum iterations for Newton's method
            tolerance: Convergence tolerance
            
        Returns:
            Implied volatility
        """
        if method == 'newton':
            return self._iv_newton(option_price, params, max_iterations, tolerance)
        elif method == 'brent':
            return self._iv_brent(option_price, params, tolerance)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _iv_newton(
        self,
        option_price: float,
        params: OptionParameters,
        max_iterations: int,
        tolerance: float
    ) -> float:
        """Newton-Raphson method for implied volatility"""
        # Initial guess using Brenner-Subrahmanyam approximation
        S = params.spot_price
        K = params.strike_price
        T = params.time_to_expiry
        
        initial_vol = np.sqrt(2 * np.pi / T) * option_price / S
        vol = max(initial_vol, 0.1)
        
        for i in range(max_iterations):
            params.volatility = vol
            greeks = self.calculate_greeks(params)
            
            price_diff = greeks.price - option_price
            
            if abs(price_diff) < tolerance:
                return vol
            
            # Vega is already per 1% change, so multiply by 100
            if greeks.vega == 0:
                break
                
            vol = vol - price_diff / (greeks.vega * 100)
            vol = max(vol, 0.001)  # Keep volatility positive
            
            # Prevent explosion
            if vol > 5:
                vol = 5
        
        # If Newton fails, fall back to Brent
        return self._iv_brent(option_price, params, tolerance)
    
    def _iv_brent(
        self,
        option_price: float,
        params: OptionParameters,
        tolerance: float
    ) -> float:
        """Brent's method for implied volatility"""
        def objective(vol):
            params.volatility = vol
            return self._black_scholes_price(params) - option_price
        
        try:
            # Find bounds
            low_vol = 0.001
            high_vol = 5.0
            
            # Ensure bounds bracket the solution
            f_low = objective(low_vol)
            f_high = objective(high_vol)
            
            if f_low * f_high > 0:
                # Try to expand bounds
                if abs(f_low) < abs(f_high):
                    return low_vol
                else:
                    return high_vol
            
            result = brentq(objective, low_vol, high_vol, xtol=tolerance)
            return result
            
        except Exception as e:
            logger.error(f"Brent's method failed: {e}")
            return 0.3  # Default fallback
    
    def calculate_portfolio_greeks(
        self,
        positions: List[Tuple[OptionParameters, float]],
        calculate_second_order: bool = False
    ) -> Greeks:
        """
        Calculate aggregate Greeks for a portfolio of options.
        
        Args:
            positions: List of (OptionParameters, quantity) tuples
            calculate_second_order: Whether to calculate second-order Greeks
            
        Returns:
            Aggregate Greeks for the portfolio
        """
        # Initialize aggregate Greeks
        total = Greeks(
            price=0, delta=0, gamma=0, theta=0, vega=0, rho=0,
            vanna=0, charm=0, vomma=0, veta=0, speed=0, zomma=0,
            color=0, ultima=0, lambda_=0, dual_delta=0, dual_gamma=0
        )
        
        total_value = 0
        
        for params, quantity in positions:
            greeks = self.calculate_greeks(params, calculate_second_order)
            
            # Aggregate first-order Greeks
            total.price += greeks.price * quantity
            total.delta += greeks.delta * quantity
            total.gamma += greeks.gamma * quantity
            total.theta += greeks.theta * quantity
            total.vega += greeks.vega * quantity
            total.rho += greeks.rho * quantity
            
            # Track total value for lambda calculation
            total_value += abs(greeks.price * quantity)
            
            # Aggregate second-order Greeks if calculated
            if calculate_second_order:
                for attr in ['vanna', 'charm', 'vomma', 'veta', 'speed', 'zomma', 'color', 'ultima', 'dual_delta', 'dual_gamma']:
                    current = getattr(total, attr, 0) or 0
                    additional = getattr(greeks, attr, 0) or 0
                    setattr(total, attr, current + additional * quantity)
        
        # Calculate portfolio lambda
        if total_value > 0:
            total.lambda_ = total.delta * params.spot_price / total_value
        
        # Round all values
        for attr in ['price', 'delta', 'gamma', 'theta', 'vega', 'rho', 'lambda_',
                    'vanna', 'charm', 'vomma', 'veta', 'speed', 'zomma', 'color', 
                    'ultima', 'dual_delta', 'dual_gamma']:
            value = getattr(total, attr)
            if value is not None:
                setattr(total, attr, round(value, self.precision))
        
        return total


# Utility functions

def greeks_to_dict(greeks: Greeks) -> Dict[str, float]:
    """Convert Greeks object to dictionary"""
    return {
        'price': greeks.price,
        'delta': greeks.delta,
        'gamma': greeks.gamma,
        'theta': greeks.theta,
        'vega': greeks.vega,
        'rho': greeks.rho,
        'lambda': greeks.lambda_,
        'vanna': greeks.vanna,
        'charm': greeks.charm,
        'vomma': greeks.vomma,
        'veta': greeks.veta,
        'speed': greeks.speed,
        'zomma': greeks.zomma,
        'color': greeks.color,
        'ultima': greeks.ultima,
        'dual_delta': greeks.dual_delta,
        'dual_gamma': greeks.dual_gamma
    }


def create_greeks_surface(
    spot_price: float,
    strikes: List[float],
    expirations: List[float],
    volatility: float,
    risk_free_rate: float,
    dividend_yield: float,
    option_type: str = 'call',
    greek: str = 'delta'
) -> np.ndarray:
    """
    Create a surface of Greek values across strikes and expirations.
    
    Args:
        spot_price: Current spot price
        strikes: List of strike prices
        expirations: List of expiration times (in years)
        volatility: Implied volatility
        risk_free_rate: Risk-free rate
        dividend_yield: Dividend yield
        option_type: 'call' or 'put'
        greek: Which Greek to calculate ('delta', 'gamma', etc.)
        
    Returns:
        2D array of Greek values [strikes x expirations]
    """
    calculator = GreeksCalculator()
    surface = np.zeros((len(strikes), len(expirations)))
    
    for i, strike in enumerate(strikes):
        for j, expiry in enumerate(expirations):
            params = OptionParameters(
                spot_price=spot_price,
                strike_price=strike,
                time_to_expiry=expiry,
                volatility=volatility,
                risk_free_rate=risk_free_rate,
                dividend_yield=dividend_yield,
                option_type=option_type
            )
            
            greeks = calculator.calculate_greeks(params)
            surface[i, j] = getattr(greeks, greek)
    
    return surface