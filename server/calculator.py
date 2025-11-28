from sympy import sympify, N
from sympy.core.sympify import SympifyError
import numpy as np
import statistics
import math
import mpmath
import re

def register(mcp):
    PRECISION = 200

    def manual_mean(values):
        evaluated = []
        for v in values:
            try:
                evaluated.append(float(N(sympify(v), PRECISION)))
            except Exception:
                evaluated.append(float(v))
        total = 0.0
        count = 0
        for x in evaluated:
            total += x
            count += 1
        return total / count if count > 0 else 0

    SAFE_ENV = {
        "np": np,
        "math": math,
        "mpmath": mpmath,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "asin": math.asin, "acos": math.acos, "atan": math.atan,
        "log": math.log, "log10": math.log10, "ln": math.log,
        "exp": math.exp, "sqrt": math.sqrt, "abs": abs,
        "mean": manual_mean,
        "median": statistics.median,
        "variance": statistics.variance,
        "stdev": statistics.stdev,
        "sum": sum, "max": max, "min": min,
    }

    def convert_stats(expr: str) -> str:
        functions = ["mean", "stdev", "variance", "median"]
        pattern = r'\b(' + "|".join(functions) + r')\s*\('
        i = 0
        while True:
            match = re.search(pattern, expr[i:])
            if not match:
                break
            fn = match.group(1)
            start = match.start() + i + len(fn) + 1
            depth = 0
            for j in range(start, len(expr)):
                if expr[j] == "(":
                    depth += 1
                elif expr[j] == ")":
                    if depth == 0:
                        end = j
                        break
                    depth -= 1
            args = expr[start:end].strip()
            if not (args.startswith("[") and args.endswith("]")):
                expr = expr[:start] + "[" + args + "]" + expr[end:]
            i = end + 1
        return expr

    def format_result(value):
        try:
            f = float(value)

            # If integer → format with commas
            if f.is_integer():
                return format(int(f), ",")

            # Very small or very large floats → scientific
            if abs(f) < 1e-5 or abs(f) > 1e8:
                return f"{f:.4e}"

            # Normal float → fixed 5 decimals + commas on integer section
            formatted = f"{f:.4f}"
            left, right = formatted.split(".")
            left = format(int(left), ",")
            return f"{left}.{right}"

        except Exception:
            return "input not in valid mathematical format"

    def calculate(expr: str) -> str:
        if not isinstance(expr, str) or expr.strip() == "":
            return "input not in valid mathematical format"

        expr = expr.replace("^", "**")
        expr = convert_stats(expr)

        try:
            value = N(sympify(expr, locals=SAFE_ENV), PRECISION)
        except ZeroDivisionError:
            return "division by zero"
        except SympifyError:
            return "input not in valid mathematical format"
        except Exception:
            return "input not in valid mathematical format"

        return format_result(value)

    
    @mcp.tool()
    async def calculate_math(expression: str) -> str:
        result = calculate(expression)
        return (f"🔢 Calculation\n"
                f"────────────────────\n"
                f"📥 Input: {expression}\n"
                f"📤 Output: {result}"
                )
    return calculate_math

# if __name__ == "__main__":
#     import asyncio
#     from mcp.server import FastMCP # type: ignore

#     test = FastMCP("test_calculator")
#     register(test)
#     tool = test._tool_manager.list_tools()[0]

#     # Custom test run (same format as weather tool)
#     print(asyncio.run(tool.fn("mean(10, max(5,20), 2+3)")))
