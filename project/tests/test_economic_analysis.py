"""Comprehensive tests for economic_analysis module."""
import pytest
from economic_analysis import (
    calculate_grafting_costs,
    calculate_grafting_revenue,
    calculate_profitability,
    calculate_break_even_analysis,
    optimize_grafting_operation,
    calculate_productivity_metrics
)


class TestCostCalculation:
    """Test cost calculations."""
    
    def test_calculate_costs(self):
        """Test cost calculation."""
        costs = calculate_grafting_costs(
            n_grafts=100,
            labor_cost_per_graft=2.0,
            material_cost_per_graft=1.0,
            overhead_cost=50.0
        )
        assert costs["total_cost"] == 350.0
        assert costs["cost_per_graft"] == 3.5


class TestRevenueCalculation:
    """Test revenue calculations."""
    
    def test_calculate_revenue(self):
        """Test revenue calculation."""
        revenue = calculate_grafting_revenue(
            n_successful=80,
            value_per_successful_graft=20.0
        )
        assert revenue["total_revenue"] == 1600.0
    
    def test_calculate_revenue_time_to_market_zero(self):
        """Test revenue calculation with time_to_market=0."""
        revenue = calculate_grafting_revenue(
            n_successful=80,
            value_per_successful_graft=20.0,
            time_to_market=0.0
        )
        assert revenue["total_revenue"] == 1600.0
        assert revenue["annualized_revenue"] == 1600.0
    
    def test_calculate_revenue_short_time_to_market(self):
        """Test revenue calculation with short time to market."""
        revenue = calculate_grafting_revenue(
            n_successful=80,
            value_per_successful_graft=20.0,
            time_to_market=180.0  # 6 months
        )
        assert revenue["total_revenue"] == 1600.0
        # Annualized should be higher (365/180 * 1600)
        assert revenue["annualized_revenue"] > 1600.0


class TestProfitability:
    """Test profitability calculations."""
    
    def test_profitability(self):
        """Test profitability calculation."""
        profit = calculate_profitability(
            total_cost=300.0,
            total_revenue=1600.0,
            n_grafts=100
        )
        assert profit["net_profit"] == 1300.0
        assert profit["is_profitable"] is True
    
    def test_profitability_zero_cost(self):
        """Test profitability with zero cost."""
        profit = calculate_profitability(
            total_cost=0.0,
            total_revenue=1600.0,
            n_grafts=100
        )
        assert profit["net_profit"] == 1600.0
        assert profit["roi_percent"] == 0.0  # Division by zero handled
        assert profit["is_profitable"] is True
    
    def test_profitability_zero_revenue(self):
        """Test profitability with zero revenue."""
        profit = calculate_profitability(
            total_cost=300.0,
            total_revenue=0.0,
            n_grafts=100
        )
        assert profit["net_profit"] == -300.0
        assert profit["profit_margin_percent"] == 0.0  # Division by zero handled
        assert profit["is_profitable"] is False
    
    def test_profitability_zero_grafts(self):
        """Test profitability with zero grafts."""
        profit = calculate_profitability(
            total_cost=300.0,
            total_revenue=1600.0,
            n_grafts=0
        )
        assert profit["net_profit"] == 1300.0
        assert profit["profit_per_graft"] == 0.0  # Division by zero handled


class TestBreakEven:
    """Test break-even analysis."""
    
    def test_break_even(self):
        """Test break-even calculation."""
        analysis = calculate_break_even_analysis(
            cost_per_graft=5.0,
            value_per_successful_graft=20.0
        )
        assert analysis["break_even_success_rate"] == 0.25
    
    def test_break_even_zero_value(self):
        """Test break-even with zero value per successful graft."""
        analysis = calculate_break_even_analysis(
            cost_per_graft=5.0,
            value_per_successful_graft=0.0
        )
        assert analysis["break_even_success_rate"] == 1.0  # Impossible
        assert analysis["is_feasible"] is False
    
    def test_break_even_negative_value(self):
        """Test break-even with negative value per successful graft."""
        analysis = calculate_break_even_analysis(
            cost_per_graft=5.0,
            value_per_successful_graft=-10.0
        )
        assert analysis["break_even_success_rate"] == 1.0  # Impossible
        assert analysis["is_feasible"] is False


class TestOptimization:
    """Test grafting operation optimization."""
    
    def test_optimize_with_budget(self):
        """Test optimization with budget constraint."""
        result = optimize_grafting_operation(
            success_rate=0.8,
            cost_per_graft=5.0,
            value_per_successful_graft=20.0,
            max_grafts=1000,
            budget=500.0
        )
        assert "optimal_n_grafts" in result
        assert result["optimal_n_grafts"] <= 100  # Budget allows 100 grafts
        assert "expected_successful" in result
        assert "expected_costs" in result
        assert "expected_revenue" in result
        assert "expected_profitability" in result
        assert "recommendation" in result
    
    def test_optimize_without_budget(self):
        """Test optimization without budget constraint."""
        result = optimize_grafting_operation(
            success_rate=0.8,
            cost_per_graft=5.0,
            value_per_successful_graft=20.0,
            max_grafts=1000,
            budget=None
        )
        # Expected profit per graft = 0.8 * 20 - 5 = 11 > 0, so should use max_grafts
        assert result["optimal_n_grafts"] == 1000
        assert result["recommendation"] == "proceed"
    
    def test_optimize_unprofitable(self):
        """Test optimization when operation is unprofitable."""
        result = optimize_grafting_operation(
            success_rate=0.1,
            cost_per_graft=5.0,
            value_per_successful_graft=20.0,
            max_grafts=1000,
            budget=None
        )
        # Expected profit per graft = 0.1 * 20 - 5 = -3 < 0, so should be 0
        assert result["optimal_n_grafts"] == 0
        assert result["recommendation"] == "reconsider"
    
    def test_optimize_budget_exceeds_max(self):
        """Test optimization when budget allows more than max_grafts."""
        result = optimize_grafting_operation(
            success_rate=0.8,
            cost_per_graft=5.0,
            value_per_successful_graft=20.0,
            max_grafts=100,
            budget=10000.0  # Allows 2000 grafts, but max is 100
        )
        assert result["optimal_n_grafts"] == 100  # Limited by max_grafts


class TestProductivity:
    """Test productivity metrics."""
    
    def test_productivity_metrics(self):
        """Test productivity metrics calculation."""
        metrics = calculate_productivity_metrics(
            n_grafts_per_day=50.0,
            success_rate=0.8,
            days_per_year=250.0
        )
        assert "grafts_per_day" in metrics
        assert "grafts_per_year" in metrics
        assert "successful_per_year" in metrics
        assert "working_days" in metrics
        assert "efficiency" in metrics
        assert metrics["grafts_per_year"] == 12500.0  # 50 * 250
        assert metrics["successful_per_year"] == 10000.0  # 12500 * 0.8
    
    def test_productivity_custom_days(self):
        """Test productivity with custom working days."""
        metrics = calculate_productivity_metrics(
            n_grafts_per_day=30.0,
            success_rate=0.75,
            days_per_year=200.0
        )
        assert metrics["grafts_per_year"] == 6000.0  # 30 * 200
        assert metrics["successful_per_year"] == 4500.0  # 6000 * 0.75
        assert metrics["working_days"] == 200.0


if __name__ == "__main__":
    pytest.main([__file__])

