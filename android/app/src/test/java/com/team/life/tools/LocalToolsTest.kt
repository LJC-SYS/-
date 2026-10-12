package com.team.life.tools

import org.junit.Assert.assertEquals
import org.junit.Test

class LocalToolsTest {
    @Test fun lengthAndSpeedConversionsAreCorrect() {
        assertEquals(1000.0, UnitConverter.convert("长度", 1.0, 1, 0), 0.0001)
        assertEquals(10.0, UnitConverter.convert("速度", 36.0, 1, 0), 0.0001)
    }

    @Test fun temperatureConversionsAreCorrect() {
        assertEquals(32.0, UnitConverter.convert("温度", 0.0, 0, 1), 0.0001)
        assertEquals(0.0, UnitConverter.convert("温度", 273.15, 2, 0), 0.0001)
    }

    @Test fun calculatorSupportsOperationsPercentSignAndBackspace() {
        val calculator = CalculatorEngine()
        listOf("1", "2", "+", "3", "=").forEach(calculator::press)
        assertEquals("15", calculator.display)
        calculator.press("+/-")
        assertEquals("-15", calculator.display)
        calculator.press("%")
        assertEquals("-0.15", calculator.display)
        calculator.press("AC")
        calculator.press("9")
        calculator.press("⌫")
        assertEquals("0", calculator.display)
    }

    @Test fun divisionByZeroReturnsFriendlyError() {
        val calculator = CalculatorEngine()
        listOf("8", "÷", "0", "=").forEach(calculator::press)
        assertEquals("错误", calculator.display)
    }
}
