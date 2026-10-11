package com.team.life.tools

import java.math.BigDecimal
import java.math.RoundingMode

data class UnitOption(val name: String, val symbol: String, val toBase: (Double) -> Double, val fromBase: (Double) -> Double)

object UnitConverter {
    val categories: Map<String, List<UnitOption>> = linkedMapOf(
        "长度" to linear("米" to 1.0, "千米" to 1000.0, "厘米" to 0.01, "英寸" to 0.0254, "英尺" to 0.3048),
        "重量" to linear("千克" to 1.0, "克" to 0.001, "吨" to 1000.0, "磅" to 0.45359237),
        "面积" to linear("平方米" to 1.0, "平方千米" to 1_000_000.0, "公顷" to 10_000.0, "亩" to 666.6666667),
        "体积" to linear("升" to 1.0, "毫升" to 0.001, "立方米" to 1000.0, "加仑" to 3.785411784),
        "速度" to linear("米/秒" to 1.0, "千米/时" to (1.0 / 3.6), "英里/时" to 0.44704, "节" to 0.514444),
        "温度" to listOf(
            UnitOption("摄氏度", "°C", { it }, { it }),
            UnitOption("华氏度", "°F", { (it - 32) * 5 / 9 }, { it * 9 / 5 + 32 }),
            UnitOption("开尔文", "K", { it - 273.15 }, { it + 273.15 }),
        ),
    )

    fun convert(category: String, value: Double, from: Int, to: Int): Double {
        val options = categories.getValue(category)
        return options[to].fromBase(options[from].toBase(value))
    }

    private fun linear(vararg entries: Pair<String, Double>) = entries.map { (name, factor) ->
        UnitOption(name, name, { it * factor }, { it / factor })
    }
}

class CalculatorEngine {
    var display: String = "0"; private set
    private var accumulator: BigDecimal? = null
    private var operation: Char? = null
    private var replace = true

    fun press(key: String): String {
        when (key) {
            "AC" -> clear()
            "⌫" -> if (!replace) display = display.dropLast(1).ifBlank { "0" }
            "+/-" -> if (display != "0") display = if (display.startsWith("-")) display.drop(1) else "-$display"
            "%" -> { display = number().divide(BigDecimal(100)).plain(); replace = true }
            "+", "-", "×", "÷" -> setOperation(key.single())
            "=" -> calculate()
            "." -> if (replace) { display = "0."; replace = false } else if (!display.contains('.')) display += "."
            else -> if (key.all(Char::isDigit)) { display = if (replace || display == "0") key else display + key; replace = false }
        }
        return display
    }

    private fun setOperation(next: Char) {
        if (operation != null && !replace) calculate()
        accumulator = number(); operation = next; replace = true
    }

    private fun calculate() {
        val left = accumulator ?: return
        val right = number()
        display = when (operation) {
            '+' -> left + right
            '-' -> left - right
            '×' -> left * right
            '÷' -> if (right.compareTo(BigDecimal.ZERO) == 0) return clear("错误") else left.divide(right, 10, RoundingMode.HALF_UP)
            else -> right
        }.plain()
        accumulator = null; operation = null; replace = true
    }

    private fun number() = display.toBigDecimalOrNull() ?: BigDecimal.ZERO
    private fun clear(value: String = "0") { display = value; accumulator = null; operation = null; replace = true }
    private fun BigDecimal.plain() = stripTrailingZeros().toPlainString()
}
