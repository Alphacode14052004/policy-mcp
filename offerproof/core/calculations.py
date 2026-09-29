from calendar import monthrange
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP


def dollars(cents):
    return f"${Decimal(cents) / 100:.2f}"


def add_months(date, months):
    year, month = divmod(date.year * 12 + date.month - 1 + months, 12)
    return date.replace(year=year, month=month + 1, day=min(date.day, monthrange(year, month + 1)[1]))


def equal_payments(cents, months):
    regular = int((Decimal(cents) / (months * 100)).to_integral_value(rounding=ROUND_CEILING)) * 100
    remaining, payments = cents, []
    for _ in range(months):
        payment = min(regular, remaining)
        payments.append(payment)
        remaining -= payment
    return payments


def schedule(cents, offer):
    months, family = offer["term_months"], offer["plan_type"]
    if not months:
        return {"payments_cents": [], "total_payments_cents": None, "finance_cost_cents": None,
                "kind": "REVOLVING_NO_PAYOFF_ESTIMATE"}
    finance_cost = 0
    if family == "CUSTOM_AMORTIZATION":
        payments = [int(Decimal(cents) * Decimal(bps) / 10000) for bps in offer["custom_schedule_bps"]]
        payments[-1] += cents - sum(payments)
    elif family == "REDUCED_APR_FIXED_TERM":
        rate = Decimal(offer["promo_apr_bps"]) / Decimal(120000)
        if rate == 0:
            payments = equal_payments(cents, months)
        else:
            payment = int((Decimal(cents) * rate / (1 - (1 + rate) ** (-months))).to_integral_value(rounding=ROUND_CEILING))
            balance, payments = cents, []
            for index in range(months):
                interest = int((Decimal(balance) * rate).to_integral_value(rounding=ROUND_HALF_UP))
                finance_cost += interest
                paid = balance + interest if index == months - 1 else min(payment, balance + interest)
                payments.append(paid)
                balance += interest - paid
    else:
        payments = equal_payments(cents, months)
    return {"payments_cents": payments, "total_payments_cents": sum(payments), "finance_cost_cents": finance_cost,
            "kind": "ILLUSTRATIVE_PAYOFF_NOT_MINIMUM" if family == "DEFERRED_INTEREST" else "CONFIGURED_SCHEDULE_ESTIMATE"}
