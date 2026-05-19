from config import RISK_FREE_RATE
from config import MARKET_RETURN
from config import TAX_RATE


def cost_of_equity(beta):
    return RISK_FREE_RATE + beta * (MARKET_RETURN - RISK_FREE_RATE)


def after_tax_cost_of_debt(cost_of_debt):
    return cost_of_debt * (1 - TAX_RATE)


def calculate_wacc(
    equity_value,
    debt_value,
    cost_equity,
    cost_debt

  
):

    total = equity_value + debt_value

    equity_weight = equity_value / total
    debt_weight = debt_value / total

    after_tax_debt = after_tax_cost_of_debt(cost_debt)

    wacc = (
        equity_weight * cost_equity
        + debt_weight * after_tax_debt
    )

    return wacc